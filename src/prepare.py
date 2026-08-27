"""Turn the downloaded raw files into the small tables the notebooks read.

``00_download_data.ipynb`` fetches the raw sources; this module converts them
once into ``data/derived/``. Everything here is deterministic, so two students
who ran the download get byte-identical derived files.

Each ``prepare_X`` function returns a short human-readable summary line.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import simulate
from data_registry import MODULES, SOURCES
from xlsx import read_records


def repo_root():
    return next(parent for parent in [Path.cwd(), *Path.cwd().parents] if (parent / "src").exists())


def _raw(key):
    return repo_root() / SOURCES[key]["path"]


def _derived(name):
    path = repo_root() / "data" / "derived" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


# --------------------------------------------------------------------------
# A - OASIS-2 longitudinal MRI measures, plus simulated slice images
# --------------------------------------------------------------------------

def prepare_A():
    _, records = read_records(_raw("oasis2_longitudinal"))
    rows = []
    for record in records:
        rows.append({
            "subject_id": record["Subject ID"],
            "session_id": record["MRI ID"],
            "visit": int(_number(record["Visit"])),
            "days_since_first_visit": int(_number(record["MR Delay"])),
            "group": record["Group"],
            "sex": record["M/F"],
            "age": _number(record["Age"]),
            "education_years": _number(record["EDUC"]),
            "ses": _number(record["SES"]),
            "mmse": _number(record["MMSE"]),
            "cdr": _number(record["CDR"]),
            "etiv_mm3": _number(record["eTIV"]),
            "nwbv": _number(record["nWBV"]),
            "asf": _number(record["ASF"]),
        })
    frame = pd.DataFrame(rows)
    # Teaching target: any clinical dementia rating above zero at this visit.
    frame["impaired"] = (frame["cdr"] > 0).astype("Int64")
    frame.loc[frame["cdr"].isna(), "impaired"] = pd.NA
    frame = frame.sort_values(["subject_id", "visit"]).reset_index(drop=True)
    frame.to_csv(_derived("a_oasis_visits.csv"), index=False)

    # Simulated 64x64 axial slices, one per visit, conditioned on the *real* nWBV/eTIV.
    images = np.zeros((len(frame), 64, 64), dtype=np.uint8)
    for position, record in frame.iterrows():
        nwbv = record["nwbv"] if np.isfinite(record["nwbv"]) else 0.73
        etiv = record["etiv_mm3"] if np.isfinite(record["etiv_mm3"]) else 1500.0
        slice_ = simulate.brain_slice(float(nwbv), float(etiv), size=64, seed=position)
        images[position] = np.clip(np.array(slice_) * 255, 0, 255).astype(np.uint8)
    np.savez_compressed(
        _derived("a_slices.npz"),
        images=images,
        subject_id=frame["subject_id"].to_numpy(),
        session_id=frame["session_id"].to_numpy(),
        group=frame["group"].to_numpy(),
        impaired=frame["impaired"].fillna(0).astype(int).to_numpy(),
        age=frame["age"].to_numpy(dtype=float),
        sex=frame["sex"].to_numpy(),
        cdr=frame["cdr"].to_numpy(dtype=float),
        nwbv=frame["nwbv"].to_numpy(dtype=float),
    )
    return f"A: {len(frame)} visits from {frame['subject_id'].nunique()} subjects, plus {len(frame)} 64x64 slices"


# --------------------------------------------------------------------------
# C - simulated fluid biomarkers
# --------------------------------------------------------------------------

def prepare_C():
    fields, rows = simulate.fluid_biomarkers()
    frame = pd.DataFrame(rows, columns=fields)
    frame.to_csv(_derived("c_biomarkers.csv"), index=False)
    return f"C: {len(frame)} simulated participants, {len(fields)} columns"


# --------------------------------------------------------------------------
# D - OASIS-1 cross-sectional, for the confounding module
# --------------------------------------------------------------------------

def prepare_D():
    _, records = read_records(_raw("oasis1_cross_sectional"))
    rows = []
    for record in records:
        identifier = record["ID"]
        if not identifier or not str(identifier).startswith("OAS1"):
            continue
        rows.append({
            "subject_id": str(identifier).split("_MR")[0],
            "session_id": identifier,
            "sex": record["M/F"],
            "handedness": record["Hand"],
            "age": _number(record["Age"]),
            "education_code": _number(record["Educ"]),
            "ses": _number(record["SES"]),
            "mmse": _number(record["MMSE"]),
            "cdr": _number(record["CDR"]),
            "etiv_mm3": _number(record["eTIV"]),
            "nwbv": _number(record["nWBV"]),
            "asf": _number(record["ASF"]),
        })
    frame = pd.DataFrame(rows).drop_duplicates(subset="subject_id").reset_index(drop=True)
    frame["impaired"] = (frame["cdr"] > 0).astype("Int64")
    frame.loc[frame["cdr"].isna(), "impaired"] = pd.NA
    frame.to_csv(_derived("d_oasis_subjects.csv"), index=False)
    labelled = int(frame["impaired"].notna().sum())
    return f"D: {len(frame)} subjects ({labelled} with a CDR rating, the rest are the young reference group)"


# --------------------------------------------------------------------------
# E - simulated clinical records
# --------------------------------------------------------------------------

def prepare_E():
    fields, rows = simulate.clinical_records()
    frame = pd.DataFrame(rows, columns=fields)
    frame.to_csv(_derived("e_records.csv"), index=False)
    events = int(frame["diagnosis_event"].sum())
    return f"E: {len(frame)} simulated participants, {events} diagnosed during follow-up"


# --------------------------------------------------------------------------
# F - real GWAS Catalog effects, simulated genotypes
# --------------------------------------------------------------------------

MAX_VARIANTS = 24


def prepare_F():
    catalog = pd.read_csv(_raw("gwas_catalog_ad"), sep="\t", low_memory=False)
    catalog = catalog[catalog["DISEASE/TRAIT"].str.contains("Alzheimer", case=False, na=False)]

    def parse_risk_allele(text):
        if not isinstance(text, str) or "-" not in text:
            return np.nan
        allele = text.rsplit("-", 1)[1].strip()
        return allele if allele in {"A", "C", "G", "T"} else np.nan

    catalog = catalog.assign(
        rsid=catalog["SNPS"].astype(str).str.strip(),
        risk_allele=catalog["STRONGEST SNP-RISK ALLELE"].map(parse_risk_allele),
        odds_ratio=pd.to_numeric(catalog["OR or BETA"], errors="coerce"),
        risk_allele_freq=pd.to_numeric(catalog["RISK ALLELE FREQUENCY"], errors="coerce"),
        p_value=pd.to_numeric(catalog["P-VALUE"], errors="coerce"),
        gene=catalog["MAPPED_GENE"].astype(str).str.split(" - ").str[0].str.split(",").str[0],
    )
    # Keep rows that are unambiguously an odds ratio for a single rs-identifier.
    keep = (
        catalog["rsid"].str.match(r"^rs\d+$", na=False)
        & catalog["risk_allele"].notna()
        & catalog["odds_ratio"].between(1.02, 6.0)
        & catalog["risk_allele_freq"].between(0.02, 0.98)
        & (catalog["p_value"] < 5e-8)
        & ~catalog["95% CI (TEXT)"].astype(str).str.contains("unit", case=False, na=False)
    )
    catalog = catalog[keep].sort_values("p_value")
    catalog = catalog.drop_duplicates(subset="rsid").drop_duplicates(subset="gene")
    variants = catalog.head(MAX_VARIANTS)[
        ["rsid", "gene", "risk_allele", "risk_allele_freq", "odds_ratio", "p_value", "PUBMEDID", "DISEASE/TRAIT"]
    ].rename(columns={"PUBMEDID": "pubmed_id", "DISEASE/TRAIT": "reported_trait"}).reset_index(drop=True)
    variants["log_odds"] = np.log(variants["odds_ratio"])
    variants.to_csv(_derived("f_variants.csv"), index=False)

    fields, rows = simulate.genotype_cohort(variants.to_dict("records"))
    cohort = pd.DataFrame(rows, columns=fields)
    cohort.to_csv(_derived("f_cohort.csv"), index=False)
    cases = int((cohort["diagnosis"] == "AD").sum())
    return f"F: {len(variants)} real risk variants, {len(cohort)} simulated participants ({cases} cases)"


# --------------------------------------------------------------------------
# G - GEO GSE1297 post-mortem hippocampal expression
# --------------------------------------------------------------------------

N_GENES = 2000


def _read_series_matrix(path):
    import gzip

    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as handle:
        lines = handle.read().splitlines()
    meta = {}
    for line in lines:
        if line.startswith("!Sample_geo_accession"):
            meta["accession"] = [v.strip('"') for v in line.split("\t")[1:]]
        elif line.startswith("!Sample_characteristics_ch1"):
            values = [v.strip('"') for v in line.split("\t")[1:]]
            if not values or ":" not in values[0]:
                continue
            key = values[0].split(":")[0].strip().lower()
            meta[key] = [v.split(":", 1)[1].strip() if ":" in v else "" for v in values]
    start = lines.index("!series_matrix_table_begin")
    header = [v.strip('"') for v in lines[start + 1].split("\t")]
    probes, values = [], []
    for line in lines[start + 2:]:
        if line.startswith("!series_matrix_table_end"):
            break
        parts = line.split("\t")
        probes.append(parts[0].strip('"'))
        values.append([float(v) if v not in ("", "null") else np.nan for v in parts[1:]])
    matrix = pd.DataFrame(values, index=probes, columns=header[1:])
    return matrix, meta


def _read_gpl_annotation(path):
    import gzip

    mapping = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as handle:
        in_table = False
        columns = None
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("!platform_table_begin"):
                in_table = True
                continue
            if line.startswith("!platform_table_end"):
                break
            if not in_table:
                continue
            parts = line.split("\t")
            if columns is None:
                columns = parts
                continue
            record = dict(zip(columns, parts))
            symbol = record.get("Gene symbol", "").split("///")[0].strip()
            if symbol:
                mapping[record["ID"]] = symbol
    return mapping


def prepare_G():
    matrix, meta = _read_series_matrix(_raw("gse1297_matrix"))
    symbols = _read_gpl_annotation(_raw("gpl96_annotation"))

    samples = pd.DataFrame({
        "sample_id": meta["accession"],
        "group": meta.get("group", [""] * matrix.shape[1]),
        "braak_stage": pd.to_numeric(pd.Series(meta.get("braak", [])), errors="coerce"),
        "nft_count": pd.to_numeric(pd.Series(meta.get("nft", [])), errors="coerce"),
        "mmse": pd.to_numeric(pd.Series(meta.get("mmse", [])), errors="coerce"),
        "age": pd.to_numeric(pd.Series(meta.get("age", [])), errors="coerce"),
        "sex": meta.get("sex", [""] * matrix.shape[1]),
        "post_mortem_interval_h": pd.to_numeric(pd.Series(meta.get("pmi", [])), errors="coerce"),
    })
    samples["is_ad"] = (samples["group"] != "Control").astype(int)

    # log2 transform, drop probes with no signal, keep the most variable ones.
    expression = np.log2(matrix.clip(lower=1.0))
    expression = expression.dropna()
    expression = expression[expression.mean(axis=1) > expression.mean(axis=1).quantile(0.30)]
    expression = expression.assign(gene=[symbols.get(probe, "") for probe in expression.index])
    expression = expression[expression["gene"] != ""]
    # One row per gene: keep the probe with the strongest average signal.
    numeric = expression.drop(columns="gene")
    order = numeric.mean(axis=1).groupby(expression["gene"].to_numpy()).rank(ascending=False)
    expression = expression[order.to_numpy() == 1].set_index("gene")
    expression = expression.loc[expression.var(axis=1).sort_values(ascending=False).index[:N_GENES]]

    # Samples as rows, genes as columns: 31 rows and 2000 columns, so p >> n is visible.
    table = expression.transpose().round(4)
    table.index.name = "sample_id"
    table = table.reset_index()
    table.to_csv(_derived("g_expression.csv"), index=False)
    samples.to_csv(_derived("g_samples.csv"), index=False)
    return f"G: {table.shape[0]} brain samples x {table.shape[1] - 1} genes (p >> n by design)"


# --------------------------------------------------------------------------
# H - MoleculeNet BACE1
# --------------------------------------------------------------------------

DESCRIPTORS = [
    "MW", "AlogP", "HBA", "HBD", "RB", "HeavyAtomCount",
    "ChiralCenterCount", "RingCount", "PSA", "MR", "Polar",
]
N_SERIES = 80


def prepare_H():
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    raw = pd.read_csv(_raw("bace_moleculenet"))
    numeric = raw.select_dtypes("number").drop(columns=["Class", "pIC50"], errors="ignore")
    numeric = numeric.loc[:, numeric.std() > 0].fillna(0.0)

    # Compounds in a medicinal-chemistry series are near-identical analogues. Without
    # RDKit we approximate the Murcko scaffold by clustering the full descriptor
    # profile; close analogues land in the same cluster, which is what grouped
    # splitting needs. The 🔵 extension in the notebook computes true scaffolds.
    scaled = StandardScaler().fit_transform(numeric.to_numpy())
    series = KMeans(n_clusters=N_SERIES, random_state=42, n_init=10).fit_predict(scaled)

    frame = pd.DataFrame({
        "compound_id": raw["CID"],
        "smiles": raw["mol"],
        "analogue_series": series,
        "pic50": raw["pIC50"].round(3),
        "active": raw["Class"].astype(int),
    })
    for name in DESCRIPTORS:
        if name in raw.columns:
            frame[name.lower()] = raw[name].round(4)
    frame.to_csv(_derived("h_bace.csv"), index=False)
    return f"H: {len(frame)} real BACE1 compounds in {frame['analogue_series'].nunique()} analogue series"


PREPARERS = {"A": prepare_A, "C": prepare_C, "D": prepare_D, "E": prepare_E, "F": prepare_F, "G": prepare_G, "H": prepare_H}


def derived_present(module):
    return all((repo_root() / name).exists() for name in MODULES[module.upper()]["derived"])


def prepare(module, force=False):
    module = module.upper()
    if not force and derived_present(module):
        return f"{module}: already prepared"
    return PREPARERS[module]()


def prepare_all(modules=None, force=False):
    lines = []
    for module in (modules or MODULES):
        lines.append(prepare(module, force=force))
    return lines

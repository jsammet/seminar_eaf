"""Single source of truth for every file this course downloads or generates.

Two dictionaries matter:

``SOURCES``
    One entry per *raw file we fetch over the network*. Each entry records the
    URL, where it lands under ``data/raw/``, the licence, the citation, the date
    we last verified the link, and — where the file is stable — its exact size
    and SHA-256. ``00_download_data.ipynb`` reads nothing else.

``MODULES``
    One entry per teaching module: which sources it needs, which derived files
    ``src/prepare.py`` builds from them, and an honest statement of what is real
    measured data and what is simulated.

Some sources are *volatile*: the GWAS Catalog gains associations every week, so
pinning a checksum would guarantee a false alarm. Those entries carry
``sha256=None`` and are verified by parsing instead.
"""

# Verified reachable and downloaded on this date.
ACCESS_DATE = "2026-08-26"

SOURCES = {
    "oasis1_cross_sectional": {
        "url": "https://sites.wustl.edu/oasisbrains/files/2024/04/oasis_cross-sectional-5708aa0a98d82080.xlsx",
        "path": "data/raw/oasis_cross-sectional.xlsx",
        "bytes": 35716,
        "sha256": "e603a8fd45e10acd83371291784bcc2d7d4f183e58fc5fae724b3f62753c54d9",
        "volatile": False,
        "title": "OASIS-1 cross-sectional demographic and MRI-derived data",
        "what": "436 subjects, one session each: age, sex, education, socioeconomic status, MMSE, CDR and the FreeSurfer-style volumetrics eTIV, nWBV and ASF.",
        "licence": "Open access under the OASIS data-use terms. Free for research and teaching; cite the paper and acknowledge the grants listed by OASIS.",
        "citation": "Marcus DS et al. (2007) Open Access Series of Imaging Studies (OASIS): cross-sectional MRI data in young, middle aged, nondemented and demented older adults. J Cogn Neurosci 19:1498-1507.",
        "homepage": "https://sites.wustl.edu/oasisbrains/home/oasis-1/",
    },
    "oasis2_longitudinal": {
        "url": "https://sites.wustl.edu/oasisbrains/files/2024/03/oasis_longitudinal_demographics-8d83e569fa2e2d30.xlsx",
        "path": "data/raw/oasis_longitudinal.xlsx",
        "bytes": 50743,
        "sha256": "2298ed89718ffeb4131ee41ab22bada949542e028bda0c9356c6688c944f930e",
        "volatile": False,
        "title": "OASIS-2 longitudinal demographic and MRI-derived data",
        "what": "373 imaging sessions from 150 older adults, 1-5 visits each: the repeated visits are what make subject-level leakage demonstrable on real data.",
        "licence": "Open access under the OASIS data-use terms. Free for research and teaching; cite the paper and acknowledge the grants listed by OASIS.",
        "citation": "Marcus DS et al. (2010) Open Access Series of Imaging Studies (OASIS): longitudinal MRI data in nondemented and demented older adults. J Cogn Neurosci 22:2677-2684.",
        "homepage": "https://sites.wustl.edu/oasisbrains/home/oasis-2/",
    },
    "bace_moleculenet": {
        "url": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/bace.csv",
        "path": "data/raw/bace.csv",
        "bytes": 3897767,
        "sha256": "f3fb9ce90bada3e2bd6148b0df13f8f8145a357bf87df0dd5b391ede974fc737",
        "volatile": False,
        "title": "MoleculeNet BACE-1 inhibition benchmark",
        "what": "1513 real compounds with measured BACE1 binding affinity (pIC50), a SMILES structure, a binary active/inactive class and ~590 precomputed 2D descriptors.",
        "licence": "MIT License, distributed with DeepChem/MoleculeNet. Redistribution and teaching use permitted.",
        "citation": "Wu Z et al. (2018) MoleculeNet: a benchmark for molecular machine learning. Chem Sci 9:513-530. Underlying assays curated from ChEMBL.",
        "homepage": "https://moleculenet.org/datasets-1",
    },
    "gse1297_matrix": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE1nnn/GSE1297/matrix/GSE1297_series_matrix.txt.gz",
        "path": "data/raw/GSE1297_series_matrix.txt.gz",
        "bytes": 1622090,
        "sha256": "7fe93d1e78ea1567625a066a267e28a62de2d421d517f3dd7a12576628d89009",
        "volatile": False,
        "title": "GEO GSE1297 - post-mortem hippocampal CA1 expression in AD",
        "what": "22283 Affymetrix HG-U133A probes across 31 post-mortem hippocampal CA1 samples spanning Control, Incipient, Moderate and Severe AD, with MMSE, Braak stage, neurofibrillary tangle count, age, sex and post-mortem interval per sample.",
        "licence": "Public GEO record; NCBI places no restriction on reuse. Cite the originating study.",
        "citation": "Blalock EM et al. (2004) Incipient Alzheimer's disease: microarray correlation analyses reveal major transcriptional and tumor suppressor responses. PNAS 101:2173-2178. GEO accession GSE1297.",
        "homepage": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE1297",
    },
    "gpl96_annotation": {
        "url": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL96/annot/GPL96.annot.gz",
        "path": "data/raw/GPL96.annot.gz",
        "bytes": 4522748,
        "sha256": "88e0b22362bac779eb220b3b185c80faa6510a92b9358eaad159a561ab4351c4",
        "volatile": False,
        "title": "GEO GPL96 platform annotation (HG-U133A)",
        "what": "Probe-set to gene-symbol mapping, so the volcano plot can name genes instead of probe identifiers.",
        "licence": "Public GEO annotation; no reuse restriction.",
        "citation": "NCBI Gene Expression Omnibus platform GPL96 annotation, dated Aug 2016.",
        "homepage": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL96",
    },
    "gwas_catalog_ad": {
        "url": (
            "https://www.ebi.ac.uk/gwas/api/search/downloads?q=alzheimer&pvalfilter=&orfilter="
            "&betafilter=&datefilter=&genomicfilter=&genotypingfilter[]=&traitfilter[]="
            "&dateaddedfilter=&facet=association&efo=true"
        ),
        "path": "data/raw/gwas_catalog_alzheimer.tsv",
        "bytes": 7361500,          # measured on ACCESS_DATE; grows over time
        "sha256": None,            # volatile: the Catalog is updated continuously
        "volatile": True,
        "title": "GWAS Catalog associations for Alzheimer's disease",
        "what": "Every published genome-wide-significant association the Catalog holds for an Alzheimer-related trait: SNP, risk allele, odds ratio, p-value and mapped gene. Real effect sizes, used as the weights of the teaching polygenic score.",
        "licence": "EMBL-EBI terms of use; the GWAS Catalog is freely available with attribution.",
        "citation": "Sollis E et al. (2023) The NHGRI-EBI GWAS Catalog: knowledgebase and deposition resource. Nucleic Acids Res 51:D977-D985.",
        "homepage": "https://www.ebi.ac.uk/gwas/",
    },
}


MODULES = {
    "A": {
        "title": "Structural MRI",
        "goal": "predict dementia status from MRI-derived brain measures, then from brain images",
        "feasibility": "Amber",
        "sources": ["oasis2_longitudinal"],
        "derived": ["data/derived/a_oasis_visits.csv", "data/derived/a_slices.npz"],
        "real": "OASIS-2: real MRI-derived volumetrics (eTIV, nWBV, ASF) and real clinical ratings, with real repeated visits per subject.",
        "simulated": "The 2D slice images are simulated phantoms, drawn to match each real visit's measured brain volume. Raw OASIS images need a data-use agreement, so the pixels are ours; the anatomy they encode is the real measurement.",
    },
    "C": {
        "title": "Blood and CSF biomarkers",
        "goal": "classify diagnosis from fluid biomarkers",
        "feasibility": "Red",
        "sources": [],
        "derived": ["data/derived/c_biomarkers.csv"],
        "real": "None. No open individual-level AD fluid-biomarker table exists that we may redistribute.",
        "simulated": "Everything. Distributions are calibrated by hand to published cohort summaries (lower Abeta42/40 and higher p-tau181/NfL in AD, assay batch offsets, a lower limit of detection).",
    },
    "D": {
        "title": "Biomarkers plus demographics (confounding)",
        "goal": "work out what the model actually learned, not maximise accuracy",
        "feasibility": "Green",
        "sources": ["oasis1_cross_sectional"],
        "derived": ["data/derived/d_oasis_subjects.csv"],
        "real": "All of it. OASIS-1's age range (18-96), its real missing socioeconomic-status field and its real education gradient make the confounding lesson land without any simulation.",
        "simulated": "Nothing.",
    },
    "E": {
        "title": "Clinical records and epidemiology",
        "goal": "risk factors and time to diagnosis",
        "feasibility": "Red",
        "sources": [],
        "derived": ["data/derived/e_records.csv"],
        "real": "None. Individual-level electronic health records are never openly redistributable.",
        "simulated": "Everything, from a survival model whose hazard ratios are set to published values for age, APOE e4 dose, education and vascular burden.",
    },
    "F": {
        "title": "Genetics",
        "goal": "polygenic risk prediction and risk-variant discovery",
        "feasibility": "Amber",
        "sources": ["gwas_catalog_ad"],
        "derived": ["data/derived/f_variants.csv", "data/derived/f_cohort.csv"],
        "real": "The variants, risk alleles, allele frequencies, odds ratios and p-values are the real published GWAS Catalog record for Alzheimer's disease.",
        "simulated": "The genotypes. Individual-level AD genotypes are access-controlled, so each teaching participant's alleles are drawn from the real allele frequencies and their disease status from the real odds ratios.",
    },
    "G": {
        "title": "Brain transcriptomics",
        "goal": "which genes differ in the AD brain - unsupervised discovery",
        "feasibility": "Green",
        "sources": ["gse1297_matrix", "gpl96_annotation"],
        "derived": ["data/derived/g_expression.csv", "data/derived/g_samples.csv"],
        "real": "All of it. Real post-mortem human hippocampal tissue, real microarray intensities, real Braak stages and real post-mortem intervals.",
        "simulated": "Nothing.",
    },
    "H": {
        "title": "Small-molecule chemistry",
        "goal": "predict BACE1 inhibition from molecular structure",
        "feasibility": "Green",
        "sources": ["bace_moleculenet"],
        "derived": ["data/derived/h_bace.csv"],
        "real": "All of it. Real compounds, real measured pIC50 values against BACE1, real descriptors.",
        "simulated": "Nothing. The analogue-series identifier used for grouped splitting is computed by us from the descriptors, and is a stand-in for a true Murcko scaffold.",
    },
}


def module_ids():
    return list(MODULES)


def sources_for(modules):
    """Return the de-duplicated source keys needed by these modules, in order."""
    keys = []
    for module in modules:
        for key in MODULES[module.upper()]["sources"]:
            if key not in keys:
                keys.append(key)
    return keys


def download_bytes(modules):
    """Measured download size for a selection, in bytes."""
    return sum(SOURCES[key]["bytes"] for key in sources_for(modules))

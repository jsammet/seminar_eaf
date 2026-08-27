# Dataset register

Every file this course downloads, where it comes from, what it may be used for, and what we do to it.
**Sources last verified and downloaded: 2026-08-26.**

`notebooks/00_download_data.ipynb` fetches exactly the files in the first table below — nothing else, and
nothing at any other time. `src/data_registry.py` is the machine-readable version of this document; the
notebook, the size table and the loaders all read from it, so the two cannot drift apart.

Two of the seven modules have **no real data at all** and say so in their first cell, in the download
notebook, and in the orientation notebook. That is a licensing fact, not an oversight: there is no open
individual-level Alzheimer's fluid-biomarker table and no open individual-level electronic health record
that we may redistribute.

---

## 1 · Files downloaded from the network

| # | File | Source | Bytes | SHA-256 | Licence / terms |
|---|---|---|---|---|---|
| 1 | `data/raw/oasis_cross-sectional.xlsx` | [OASIS-1](https://sites.wustl.edu/oasisbrains/home/oasis-1/), Washington University in St. Louis | 35,716 | `e603a8fd45e10acd83371291784bcc2d7d4f183e58fc5fae724b3f62753c54d9` | Open access under the OASIS terms; free for research and teaching with citation and grant acknowledgement |
| 2 | `data/raw/oasis_longitudinal.xlsx` | [OASIS-2](https://sites.wustl.edu/oasisbrains/home/oasis-2/), Washington University in St. Louis | 50,743 | `2298ed89718ffeb4131ee41ab22bada949542e028bda0c9356c6688c944f930e` | as above |
| 3 | `data/raw/bace.csv` | [MoleculeNet BACE-1](https://moleculenet.org/datasets-1), via DeepChem S3 | 3,897,767 | `f3fb9ce90bada3e2bd6148b0df13f8f8145a357bf87df0dd5b391ede974fc737` | MIT License; redistribution and teaching use permitted |
| 4 | `data/raw/GSE1297_series_matrix.txt.gz` | [NCBI GEO GSE1297](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE1297) | 1,622,090 | `7fe93d1e78ea1567625a066a267e28a62de2d421d517f3dd7a12576628d89009` | Public GEO record; no reuse restriction; cite the originating study |
| 5 | `data/raw/GPL96.annot.gz` | [NCBI GEO platform GPL96](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL96) | 4,522,748 | `88e0b22362bac779eb220b3b185c80faa6510a92b9358eaad159a561ab4351c4` | Public GEO annotation; no reuse restriction |
| 6 | `data/raw/gwas_catalog_alzheimer.tsv` | [NHGRI-EBI GWAS Catalog](https://www.ebi.ac.uk/gwas/) association download, query `alzheimer` | 7,361,500 *(on the access date)* | **not pinned — see note** | EMBL-EBI terms of use; freely available with attribution |

**Total download: 17.5 MB.** After preparation the derived tables add roughly 2 MB.

> **Note on file 6.** The GWAS Catalog is updated continuously, so its download grows week by week and a
> pinned checksum would raise a false alarm every time. `src/data_registry.py` marks it `volatile: True`;
> the downloader verifies it by size range and by successfully parsing it, not by hash. Every other file
> is byte-for-byte checksummed on every run.

### Citations — please use these

1. **OASIS-1** — Marcus DS, Wang TH, Parker J, Csernansky JG, Morris JC, Buckner RL (2007). *Open Access
   Series of Imaging Studies (OASIS): cross-sectional MRI data in young, middle aged, nondemented and
   demented older adults.* Journal of Cognitive Neuroscience 19:1498–1507.
2. **OASIS-2** — Marcus DS, Fotenos AF, Csernansky JG, Morris JC, Buckner RL (2010). *Open Access Series of
   Imaging Studies (OASIS): longitudinal MRI data in nondemented and demented older adults.* Journal of
   Cognitive Neuroscience 22:2677–2684.
3. **BACE-1** — Wu Z, Ramsundar B, Feinberg EN, Gomes J, Geniesse C, Pappu AS, Leswing K, Pande V (2018).
   *MoleculeNet: a benchmark for molecular machine learning.* Chemical Science 9:513–530. Underlying
   bioactivity curated from ChEMBL.
4. **GSE1297** — Blalock EM, Geddes JW, Chen KC, Porter NM, Markesbery WR, Landfield PW (2004). *Incipient
   Alzheimer's disease: microarray correlation analyses reveal major transcriptional and tumor suppressor
   responses.* PNAS 101:2173–2178.
5. **GWAS Catalog** — Sollis E, Mosaku A, Abid A, et al. (2023). *The NHGRI-EBI GWAS Catalog:
   knowledgebase and deposition resource.* Nucleic Acids Research 51:D977–D985.

---

## 2 · Per module: what is real, what is not

| Module | Feasibility | Real measured data | Simulated | Derived files (size) |
|---|---|---|---|---|
| **A** Structural MRI | 🟠 Amber | OASIS-2: 373 real MRI sessions from 150 people — eTIV, nWBV, ASF, CDR, MMSE, age, sex, education, SES, with real repeated visits | the 64×64 slice images | `a_oasis_visits.csv`, `a_slices.npz` (1.13 MB) |
| **C** Fluid biomarkers | 🔴 Red | none | the entire cohort (420 people) | `c_biomarkers.csv` (28 KB) |
| **D** Confounding | 🟢 Green | OASIS-1: 416 real people, ages 18–96, one session each | nothing | `d_oasis_subjects.csv` (26 KB) |
| **E** Clinical records | 🔴 Red | none | the entire cohort (900 people) | `e_records.csv` (39 KB) |
| **F** Genetics | 🟠 Amber | 24 real GWAS Catalog variants: rsID, risk allele, allele frequency, odds ratio, p-value, mapped gene | the genotypes and disease status of 1200 participants | `f_variants.csv`, `f_cohort.csv` (93 KB) |
| **G** Transcriptomics | 🟢 Green | GSE1297: 31 real post-mortem hippocampal CA1 samples × 2000 genes, with real Braak stage, MMSE, NFT count, age, sex, post-mortem interval | nothing | `g_expression.csv`, `g_samples.csv` (437 KB) |
| **H** Chemistry | 🟢 Green | 1513 real compounds with measured BACE1 pIC50, SMILES structures and 2D descriptors | nothing (the `analogue_series` grouping is computed by us — see below) | `h_bace.csv` (203 KB) |

### Exactly what preparation does (`src/prepare.py`, deterministic)

- **A** — parse the OASIS-2 workbook with a standard-library XLSX reader (`src/xlsx.py`, so `openpyxl` is
  not a dependency); rename columns; derive `impaired = cdr > 0`. Then draw one 64×64 phantom axial slice
  per visit whose ventricle size and cortical ribbon are set by *that visit's real measured* `nwbv` and
  `etiv_mm3`, stored as compressed `uint8`. **The pixels are ours; the anatomy they encode is a real
  measurement.** Raw OASIS images require a signed data-use agreement and are not shipped.
- **C** — `simulate.fluid_biomarkers()`: 420 participants drawn from published group means and spreads for
  Aβ42/40, p-tau181, NfL and GFAP, with a per-site assay batch offset, a lower limit of detection at
  8 pg/ml, and missingness that increases with severity.
- **D** — parse the OASIS-1 workbook, deduplicate by subject, derive `impaired = cdr > 0`. Nothing else.
  Missing `ses` and `mmse` are left exactly as the source has them — the missingness is part of the lesson.
- **E** — `simulate.clinical_records()`: 900 participants from a Weibull survival model whose log hazard
  ratios are set to published population estimates (APOE ε4 ≈ 2.6 per allele, diabetes ≈ 1.45, depression
  history ≈ 1.6, education protective ≈ 0.93/year), with a competing risk of death and administrative
  censoring at 12 years.
- **F** — filter the GWAS Catalog download to Alzheimer traits, single rsIDs, p < 5×10⁻⁸, a parseable risk
  allele, an odds ratio in [1.02, 6.0] (excluding rows whose CI text marks them as betas), and a stated
  risk-allele frequency; keep the strongest hit per rsID and per gene; take the top 24 by p-value. Then
  draw genotypes from those real frequencies and disease status from those real odds ratios, with two
  ancestry groups whose frequencies are slightly shifted.
- **G** — parse the GEO series matrix and its sample characteristics; log2-transform; drop the lowest-signal
  30% of probes; map probes to gene symbols via GPL96, keeping the strongest probe per gene; retain the
  2000 most variable genes; transpose to samples-as-rows. **No filtering by outcome at any point** — that
  would be selection bias baked into the file.
- **H** — take `CID`, `mol` (SMILES), `pIC50` and `Class` plus eleven interpretable descriptors. The
  `analogue_series` column is **computed by us**: k-means (k=80, seed 42) on the standardised full
  descriptor profile, as a stand-in for a true Murcko scaffold, which would require RDKit. Near-identical
  analogues land in the same cluster, which is what grouped splitting needs. The notebook says this
  plainly and offers the RDKit version as an extension.

---

## 3 · Data we deliberately do not use

| Considered | Why not |
|---|---|
| ADNI (imaging, PET, biomarkers) | Requires an application with review; redistribution forbidden. Cannot be part of a self-serve student download. |
| NACC (clinical records) | Data request required; turnaround measured in weeks. |
| ROSMAP (transcriptomics) | Access-controlled through the AD Knowledge Portal. GSE1297 is open and adequate for the lesson. |
| Kaggle "Alzheimer MRI" slice collections | Provenance unclear, and several are augmented duplicates of one another — a subject-leakage disaster shipped as a dataset. Rejected. |
| Raw OASIS MRI volumes | The DUA permits use but we cannot redistribute, and full volumes would blow the size budget several times over. Hence the simulated slices. |

## 4 · Ethics and obligations

These are donated human data. OASIS-1 and OASIS-2 are volunteers who lay in a scanner, some repeatedly,
some while developing dementia. GSE1297 is 31 donated human brains. The GWAS Catalog aggregates studies in
which hundreds of thousands of people consented to genetic research.

Obligations we accept in return: cite the sources above in any public use of this material; do not attempt
re-identification; do not redistribute the raw files as though they were ours; and state plainly, in every
notebook, which numbers are measurements and which are simulations. Every module's first cell prints its own
provenance via `data.provenance(module)`, and every module's final section states that nothing built here is
a diagnostic tool.

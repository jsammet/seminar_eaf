# CLAUDE.md — Alzheimer's Disease AI Practical (Seminar Day 4)

Instructions for any agent generating material in this repository. Read fully before writing code.

---

## 1. What this project is

We build **Jupyter notebooks for a single 3.5-hour hands-on session**, day 4 of a 5-day seminar for **bachelor students from mixed backgrounds** (biology, medicine, psychology, computer science, ...). Some have never written a line of code; some are CS students who will be bored by anything less than building a model themselves.

By day 4 the students have already had lectures on AI concepts and on how AI models are used across the stages of biomedical research, with a focus on **Alzheimer's disease (AD)**. They have heard the words. They have not touched the data.

The session is a **menu, not a lecture**: several self-contained modules covering different data modalities (§4). Students pick one to work through properly and at least one more to sample, then the room reconvenes to compare what different data types can and cannot tell us about the same disease.

**Everything must be framed in the context of Alzheimer's disease.** No iris, no titanic, no MNIST, no generic `make_classification`. Synthetic data is permitted only where real data is inaccessible (§4, modules E and F), must use AD-realistic variables, and must be labelled as synthetic in the first markdown cell.

**Hardware reality:** student laptops, **CPU only, no GPU**, possibly 8 GB RAM, possibly Windows. Seminar Wi-Fi is assumed to be unreliable.

---

## 2. How a request to you will look, and what you do first

You will receive a **data type** and a **rough prediction goal** — usually corresponding to one of the modules in §4. Work through these steps in order. Do not skip to writing notebooks.

### Step 1 — Search for an existing course first
Search the web for existing teaching material covering this modality + goal in an AD context (university course repos, Kaggle Learn / competition notebooks, Neuromatch, Carpentries, workshop GitHub repos, tutorial papers).

**If a good, freely usable, still-maintained course already exists: say so and point the user to it instead of rebuilding it.** State what it covers, what it lacks for our format, and what adapting it would cost versus building fresh. Recommend one option. Wait for the user's decision.

### Step 2 — Find and vet the dataset
Search for a **concrete, downloadable dataset**. Do not invent one, and do not write notebooks against a schema you have not inspected.

Requirements, in priority order:
1. **Openly downloadable** without a multi-week application. If a strong dataset needs registration, only propose it if the instructor can plausibly obtain access before the seminar and the licence permits teaching use.
2. **Redistributable or at least cacheable** — check the licence/DUA before planning to ship a copy.
3. **Small**: ideally < 100 MB, hard ceiling ~500 MB per module. Subsample and document the subsampling.
4. **Real, with real flaws.** Missing values, imbalance, batch effects and confounds are the point. Do not clean it before shipping it.

Record everything in `DATASETS.md`, per module: source URL, licence, citation, access date, exact download/subsampling steps, file hashes, variable dictionary.

### Step 3 — Propose a plan, then stop
Present to the user: chosen dataset + licence + why; the prediction target and why it matters in AD; the four-notebook outline with **minute budgets** for both the Full and Express paths (§3); the model ladder with expected CPU runtimes; a **feasibility verdict** (§4.1); and what students on each track actually do.

**Wait for approval.** Then build.

---

## 3. Session structure and time budget

210 minutes total. Students do **one module in full and one in express mode**, or one module plus its deep-dive extensions.

| Block | Minutes | Content |
|---|---|---|
| Orientation | 15 | Which stage of AD research is each modality used in; how to pick a module; setup check |
| **Module 1 — Full path** | 85 | Explore → QC → Model → Results, chosen by the student |
| Break | 15 | |
| **Module 2 — Express path** | 55 | A second modality, QC pre-run and presented as findings |
| Cross-modal wrap-up | 25 | Compare what each modality can and cannot tell us; what would you trust in a clinic? **No leaderboard, no comparison of students' numbers** (§6). |
| Slack | 15 | Absorbed by whatever goes wrong |

Therefore **every module ships in two paths**:

- **Full (~85 min)**: all four notebooks, student runs QC themselves.
- **Express (~50 min)**: notebook 1 condensed, notebook 2 replaced by a short read-only "QC findings" summary with pre-computed figures, notebooks 3–4 intact. The modelling and interpretation are never cut — those are the point.

Budget **~40% slack for humans**: a block budgeted at 85 minutes may contain at most ~50 minutes of actual reading, running and typing.

---

## 4. Module catalogue

Seven modules — five clinical/translational (A, C–F) and two basic-research (G–H). **Module B (PET) was removed**: no open individual-level PET data exists that we may redistribute, and the tabular-SUVR fallback would have duplicated module C's lesson without adding a modality the students could actually touch. Do not re-add it without a concrete open dataset. Each is self-contained, each follows the identical four-step trajectory (§5), each uses the identical helper API (§6) so that a student switching modules recognises the structure immediately.

| ID | Modality | Prediction goal | Research stage framing |
|---|---|---|---|
| **A** | Structural MRI (2D slices) | CN / MCI / AD classification; *or* differential diagnosis across neurodegenerative diseases; *or* longitudinal (visit 1 vs visit 2) progression risk | Diagnosis & staging |
| **C** | Blood & CSF biomarkers | Disease classification from fluid markers | Minimally invasive screening |
| **D** | Biomarkers + demographics | Understanding confounding — not just accuracy | Study design & interpretation |
| **E** | Clinical records | Epidemiological risk factors, time-to-event | Population risk, prevention |
| **F** | Genetics | Polygenic risk prediction and risk-gene identification | Aetiology, risk stratification |
| **G** | Brain transcriptomics | Which genes and cell types differ in the AD brain — **unsupervised discovery**, not patient prediction | Basic research: mechanism |
| **H** | Small-molecule chemistry | Predict whether a compound inhibits an AD drug target (BACE1) from its structure | Basic research: drug discovery |

Modules **G and H are the basic-research pair**: no patient is being classified in either. They exist so students see that "AI in Alzheimer's research" is not synonymous with "diagnose this patient" — one is hypothesis generation from molecular data, the other is chemistry. Both are worth offering as the Express second module to a student whose Full module was clinical, because the contrast is the lesson.

### 4.1 Feasibility verdict (required per module)
Data availability varies enormously across these modalities. Before building, classify the module and tell the user:

- **Green** — open real data found, licence permits use, notebooks build as specified.
- **Amber** — real data exists but is restricted or awkward (registration, size, format). State the workaround: request access, subsample, or use a smaller proxy dataset.
- **Red** — no usable open individual-level data. Fall back to **realistic simulation calibrated on published summary statistics**, clearly labelled, with the real-world data source named so students know what the real thing looks like. A well-built simulation that teaches the method honestly beats a scraped dataset of unknown provenance.

**As built:** A is Amber (real OASIS-2 measures, simulated slice images), C is Red (fully simulated — no shareable biomarker table exists), D is Green (real OASIS-1), E is Red (fully simulated — EHR data is never open), F is Amber (real GWAS Catalog effects, simulated genotypes), G is Green (real GEO GSE1297) and H is Green (real MoleculeNet BACE-1). Do not fake Green, and do not quietly upgrade a verdict.

### 4.2 Module briefs

Dataset entries are **leads to verify, not facts.** Availability, licences and URLs change — search and confirm before use.

---

**A — Structural MRI**
- *Goal options (pick one per request):* three-class CN/MCI/AD; binary disease status; differential across neurodegenerative diseases; or longitudinal two-timepoint change → progression risk.
- *Leads:* OASIS-1/2/3 (data-use agreement; longitudinal in OASIS-2/3), ADNI (application; **never redistribute**), Kaggle MRI slice datasets (**provenance often unclear and several are augmented duplicates — verify or reject**), IXI (healthy reference).
- *Ladder:* volumetric/tabular features (hippocampal volume) → logistic regression → random forest → PCA/eigenbrains → small CNN on downsampled 2D slices → frozen pretrained backbone as feature extractor.
- *Signature hazard:* **subject-level leakage.** Multiple slices or multiple visits from one patient split across train and test inflates accuracy to near-perfect. Demonstrate this deliberately, then fix it with grouped splitting (§6).
- *Longitudinal variant hazard:* registration/intensity differences between visits can dominate real atrophy; discuss normalisation.

**C — Blood & CSF biomarkers**
- *Goal:* classify diagnosis from Aβ42, Aβ42/40 ratio, p-tau181/p-tau217, t-tau, NfL, GFAP.
- *Leads:* ADNI biomarker tables, OASIS-3 clinical/biomarker tables, published cohort supplements, curated Kaggle tabular sets (verify provenance).
- *Ladder:* single-marker threshold + ROC → logistic regression → random forest / gradient boosting → small MLP.
- *Signature hazard:* assay batch effects and left/right-censored values at the assay detection limit; ratios outperform single markers and students should discover this themselves.
- *This is the recommended default module* for students with no coding background: fastest to run, most legible.

**D — Biomarkers + demographics (confounding)**
- *Goal:* explicitly **not** maximum accuracy. The goal is to understand what the model has actually learned.
- *Data:* module C's dataset plus age, sex, education (cognitive reserve), APOE ε4, site/cohort.
- *Ladder:* naive model with everything → stratified analysis → covariate adjustment → matched subsample → permutation/ablation of individual features → "predict age instead of diagnosis" to reveal how much signal is age.
- *Signature hazards to build the notebook around:* age is entangled with AD status in nearly every cohort; Simpson's paradox; site as a proxy for diagnosis when cohorts were recruited differently; education shifting cognitive test cutoffs.
- *Pairs naturally with C as the Express second module.*

**E — Clinical records / epidemiology**
- *Goal:* which factors predict AD risk in a population; time-to-diagnosis modelling.
- *Leads:* real individual-level EHR is essentially never open — expect **Amber/Red**. Check NACC (data request), CDC population indicator data (open but aggregate, weak for ML), and **synthetic EHR generators as a legitimate Red fallback**.
- *Ladder:* contingency tables and odds ratios → Kaplan–Meier curves → Cox proportional hazards → tree-based risk model → compare epidemiological and ML framings of the same question.
- *Signature hazards:* immortal time bias, competing risk of death (critical in an elderly cohort), reverse causation (prodromal symptoms recorded as risk factors), and the association-versus-causation line, which must be drawn explicitly.
- *Needs `lifelines` or `statsmodels` — declare in the module environment.*

**F — Genetics**
- *Goal:* polygenic risk prediction, and identification of risk-associated variants.
- *Leads:* individual-level genotypes with AD labels are restricted. Use **open GWAS summary statistics** (GWAS Catalog and major published AD GWAS) for the risk-gene half, and open reference genotype panels with a **simulated AD phenotype** for the prediction half — labelled as simulated. Simplify aggressively if needed: an APOE ε4 dose plus a handful of published top loci is a legitimate teaching PRS.
- *Ladder:* allele counting → APOE-only risk model → weighted PRS from published effect sizes → PRS + age/sex → logistic regression on selected SNPs. Manhattan and QQ plots for the discovery half.
- *Signature hazards:* multiple testing (why p < 5×10⁻⁸), population stratification, effect sizes that are real but tiny (AUC ~0.6 is a *good* result here — students must be told this before they see it), and PRS transferability across ancestries as an equity issue.
- *Keep the compute trivial: precompute anything genome-scale into `data/derived/`.*

**G — Brain transcriptomics (mechanism discovery)**
- *Goal:* not "predict the patient" but "**what is different in the AD brain, and in which cells?**" This is the module where the AI method is largely **unsupervised** — the answer is a set of genes and a picture, not an accuracy score.
- *Leads:* GEO post-mortem brain expression series (open, microarray and RNA-seq, several classic AD datasets with region and Braak stage annotation); public single-nucleus AD brain atlases (open browsing, but check download terms and size); ROSMAP-derived resources (typically access-controlled — treat as Amber). **Prefer bulk or precomputed pseudobulk over raw single-cell** so the module runs without a heavy single-cell stack.
- *Ladder:* filtering and normalisation → PCA → clustering (k-means / hierarchical) → UMAP/t-SNE of samples or cells → differential expression with multiple-testing correction → enrichment of the resulting gene set → 🔵 optional supervised classifier on expression, explicitly to show how badly it overfits at p ≫ n.
- *Signature hazards, and the reason this module is worth teaching:* **p ≫ n** (20,000 genes, 40 brains) and what that does to any classifier; multiple testing and FDR; batch and post-mortem interval confounds; **cell-type composition change versus within-cell-type change** — a "downregulated neuronal gene" in AD tissue may simply reflect fewer neurons; and the honest fact that differential expression is correlational and post-mortem tissue is end-stage disease, so causality claims are unwarranted.
- *Visual payoff:* clustering that separates AD from control on PC1 — or conspicuously fails to, which is a better teaching moment. Volcano plots, heatmaps of top genes, UMAP coloured by diagnosis and then by batch.
- *Deps:* `scipy` + `statsmodels` suffice for bulk. `scanpy` only as a declared optional extra; if used, ship a pre-filtered object.

**H — Small-molecule chemistry (drug discovery)**
- *Goal:* given a molecule's structure, predict whether it inhibits **BACE1 (β-secretase)**, a much-studied target in the amyloid pathway. Frame it properly: this is the *in silico* triage step that decides which of a million candidate compounds ever gets synthesised — and BACE1 inhibitors are also a cautionary tale, since several reached late-stage AD trials without delivering clinical benefit. Both halves of that story belong in the notebook.
- *Leads:* curated public bioactivity benchmark sets for BACE1 (small, ~10³ compounds, ideal size for a laptop) and the underlying open bioactivity databases if a custom set is preferred. Verify licence and the activity threshold used.
- *Ladder:* simple physicochemical descriptors (molecular weight, logP, H-bond donors/acceptors — and the drug-likeness rules students may have heard of) → logistic regression → molecular fingerprints + random forest / gradient boosting → 🔵 optional small MLP on fingerprints → ⚫ graph-based models as take-home only.
- *Signature hazards:* **scaffold leakage** — near-identical analogues split across train and test make the model look far better than it is, exactly parallel to subject-level leakage in the imaging modules (§6); activity cliffs, where one atom flips a compound from potent to inert; heterogeneous assays and the arbitrariness of the active/inactive cutoff; and the gap between binding a target in a dish and helping a patient.
- *Visual payoff:* chemical space in 2D coloured by activity, molecules rendered next to their predictions, and the correctly-versus-incorrectly-classified compounds shown as actual structures.
- *Deps:* `rdkit` (pip-installable) as a declared extra — but **ship precomputed descriptors and fingerprints as CSV in `data/derived/` so the 🟢 Core path runs with no chemistry stack at all.** Structure rendering degrades gracefully to a static image if RDKit is missing.

### 4.3 Imaging modules: 2D and the escape hatch
Non-negotiable rules for module A (and any future imaging module):

- **Always work in 2D.** Extract representative slices or projections offline; ship the 2D arrays, never full volumes. Document the slice-selection rule and note in the notebook that it discards information.
- **Small CNNs are the final step, not the first.** Students must first beat a baseline with tabular features and classical models so the CNN's contribution is measurable rather than magical.
- **CPU budget applies:** a CNN training run must complete in ≤ 3 minutes on CPU. Achieve this with small images (e.g. 64×64), few filters, few epochs, and a subsampled balanced set. *As built, module A's CNN trains in about 6 seconds on 254 64×64 images, and the whole notebook runs in ~35 s.*
- **Dependency escape hatch:** the CNN must degrade gracefully. `src/images.py` uses PyTorch when it is installed and otherwise trains an equivalent dense network on the same pixels, printing an explanation. No student is ever blocked by a missing optional dependency.
- **Hosted-runtime escape hatch:** required only if a module's compute exceeds the CPU budget above. Module A currently does not come close, so it ships without a Colab badge. If a future imaging module needs real GPU time, add the badge, a `RUNTIME` detection cell, and a loader that falls back to a public URL — and say plainly: *if your laptop is too slow here, open the same notebook there and keep going.* The hosted GPU is an accelerator, never a requirement.

### 4.4 Cross-modal wrap-up
A final shared notebook (`99_crossmodal_wrap.ipynb`) that:
- is a **discussion, not a scoreboard**. There is deliberately no shared results file and no comparison between students' numbers: different cohorts, sample sizes, label definitions and difficulty make them incomparable, and putting them on one axis would teach exactly the wrong lesson. Say so explicitly;
- has each module report back on what its data was, what flaw would have fooled them, and the one figure worth showing;
- draws out the **pairs**: A and H are the same leakage problem in two disciplines; C and D are the same kind of data asked two different questions;
- maps each modality onto the AD research pipeline the students heard about earlier in the week: who gets scanned, who gets a lumbar puncture, who gets genotyped, and what each is actually used for;
- **handles the discovery modules separately.** G and H do not classify patients: G contributes a gene set and a clustering figure, H a compound-activity model. The framing to make explicit is that these sit *upstream* — G proposes what to study, H proposes what to synthesise, and the clinical modules only exist because work like that came first;
- closes with two questions: given cost, invasiveness and accuracy, which modality would you screen a population with and which would you use to confirm a diagnosis — and, separately, which of today's modules was actually trying to *predict* something versus trying to *understand* something?

### 4.5 The data download notebook — `00_download_data.ipynb`

With seven modules, data acquisition cannot happen during the session. A room of thirty students pulling several GB over seminar Wi-Fi in the first fifteen minutes is a guaranteed failure. **The download is homework, distributed with the seminar materials several days in advance**, and it gets its own top-level notebook.

**This notebook is the single entry point for all data in the repository.** No other notebook downloads anything, except as the last-resort fallbacks already specified (§4.3 Colab, §6 offline-first).

**Requirements:**

- **Selective by design.** Students choose which modules to fetch — their intended Full module, their likely Express module, or everything. Provide **both** selection mechanisms, because `ipywidgets` does not render reliably on every install:
  1. checkbox widgets per module plus a **"select all"** control, and
  2. a plain, clearly commented fallback cell: `MODULES = ["C", "D"]  # or "ALL"`.
  Both paths must lead to the same download call. Never make the widget path the only path.

- **Two tiers per module**, since most students need only the smaller one:
  - **Minimal** — precomputed/derived artefacts only (2D slices, extracted features, fingerprints, pretrained weights). Sufficient for the entire 🟢 Core path. Target **≤ 100 MB per module**.
  - **Full** — minimal plus raw data, needed for 🔵 Extension and ⚫ Deep-dive cells that do their own preprocessing.

  Default to Minimal, and state plainly which cells require Full.

- **Sizes stated in the notebook text, in a table the student reads before choosing.** One row per module: download size (minimal), download size (full), size on disk after extraction, and rough download time on a typical home connection. **These numbers must be measured, not estimated** (§9), and must be rendered from the registry rather than typed by hand, so they cannot drift out of date. Before any download starts, print the selection's total: *"You selected A, C, D (full) — 340 MB to download, 810 MB on disk, roughly 4 minutes."*

- **A single source of truth**: `src/data_registry.py` (or `datasets.yaml`) holding, per module and tier, the URLs, sizes, checksums, licence, target paths, and whether access is gated. The notebook, the size table and every module loader read from it. Adding a module means editing the registry, not the notebook.

- **Idempotent and resumable.** Re-running is always safe: files already present with a matching checksum are skipped with a message. Interrupted downloads resume or restart cleanly. Show per-file progress and retry transient failures.

- **Gated datasets are never automated.** For anything behind a DUA or application (ADNI, OASIS, NACC — §4.2), do not attempt a download. Print numbered manual instructions, the exact filename and target path expected, and a re-check cell that verifies the file once the student has placed it. State the expected turnaround for access requests, since that determines whether the module is viable at all.

- **Offline fallback.** A cell that points the loader at an instructor USB stick or shared folder and copies from there, for students with no usable connection.

- **Ends with a verification status table**: one row per module, ✅ / ⚠️ / ❌ for verified, partial, or missing, plus total disk used. Tell students to screenshot this and send it to the instructor if anything is wrong — before the session, not during it.

- **Runs on a bare Python install.** It must work *before* the full environment exists, so it may use only the standard library plus at most one HTTP dependency, with `ipywidgets` optional. Do not import `pandas`, `torch` or anything module-specific here.

- **Keep the total honest.** "Everything, Full tier" should stay under roughly 2 GB. If a candidate dataset would blow that, subsample it (§2) rather than shipping it whole.

The opening text must tell students: run this **at home, at least two days before the session**; two modules is normal and sufficient; downloading everything is optional and only worth it on a fast connection.

---

## 5. The four-step trajectory (identical in every module)

**N1 — Understand the data.** Load, inspect shape and dtypes, explain **every variable in clinical terms** (MMSE, CDR, APOE ε4, SUVR, Aβ42/40, hippocampal volume — assume nothing). Cohort composition by diagnosis, age, sex. Univariate and bivariate views. One planted "wait, that's odd" moment.

**N2 — Quality control.** The notebook biomedical students will remember. At minimum: missingness and whether it is random (sicker patients skip visits); distributions and outliers, including the judgement call of drop-versus-keep; class imbalance and what it does to accuracy; batch/site/scanner effects; coverage gaps and who the resulting model would fail; and **leakage** — split before imputing or scaling, show the wrong way once with its inflated score, then fix it. End with an explicit written verdict on usability and caveats.

**N3 — Apply AI methods.** The module's ladder (§4.2), always starting from a trivial baseline. **Visual feedback is mandatory**: decision boundaries, tree structure, learning curves, confusion matrices responding to a moving threshold, PCA/UMAP of learned representations, misclassified cases shown as actual subjects. Every model produces a picture, not only a number. Provide `ipywidgets` or clearly marked parameter cells so a non-coder can change one hyperparameter and immediately see the effect.

**N4 — Display results.** Model comparison table; ROC and PR curves and why PR matters under imbalance; calibration; the confusion matrix read clinically (a false negative here is a missed early diagnosis — what does that cost?); feature importance sanity-checked against known AD biology; **interpretability — exact Shapley values via `src/interpret.py` where the feature set is small enough (≤ 10)**; subgroup error analysis; honest limitations. **Every step produces a figure; no step ends on a bare number.** Close with: what would have to be true before this is used on a patient?

---

## 6. Cross-cutting technical rules

**Consistency across modules** — a student switching modules must not have to relearn anything.
- Identical notebook skeleton and filenames inside each module folder (§7).
- Identical helper API in `src/`: `load_data(module)`, `load_extra(module)`, `provenance(module)`, `split_data(X, y, groups=None)`, `train_model(name, X, y, **params)`, `evaluate(model, X, y)`, `compare_models(...)`, `sweep_parameter(...)`, `plots.plot_*` helpers, and `interpret.shapley_values(...)`.
- Identical lane markers 🟢 / 🔵 / ⚫ (§8) and identical `# TODO` conventions.
- Identical metric set so a student switching modules recognises it: balanced accuracy, AUROC, AUPRC, sensitivity, specificity. Modules with a supervised endpoint (A, C, D, E, F, H) report all of them; **G reports none of these** and instead produces a gene set, a volcano plot and a clustering figure (§4.4).
- **No leaderboard, no shared results file, no comparison between students.** Each module's results section ends with a summary *figure* for the student's own notes and nothing that is written to shared state.

**Splitting.** `split_data` takes a `groups` argument and any module where rows are not independent **must** pass it: subject IDs for repeated visits (A), and **chemical analogue-series / scaffold IDs for H**. Same function, same argument, same lesson in two very different disciplines — make that parallel explicit in the text of both modules. Grouped splitting is a cross-cutting requirement, not a per-module detail.

**Compute.** No cell may exceed ~30 s on a CPU laptop (imaging CNN cells: ~3 min, flagged with an expected-time note). Whole-notebook compute budget ~5 min, imaging ~8 min. Anything slower ships precomputed in `data/derived/` with the slow path offered as ⚫ take-home.

**Environments.** One base environment covers all modules (`pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `ipywidgets`). Module-specific extras (`torch` CPU for A/B, `lifelines`/`statsmodels` for E, `rdkit` for H, optional `scanpy` for G) are declared per module and **checked by `01_setup_check.ipynb`, which reports which modules are runnable on this machine** and cross-checks against which data the student actually downloaded.

**Offline-first.** Data must be present locally before the session; loaders check local paths first, download only as fallback, and fail with a human-readable message naming the file to copy from the USB stick or shared folder. Imaging modules additionally support the Colab download path (§4.3).

**Code style.** Readable over clever; explicit loops beat dense comprehensions. Boilerplate lives in `src/`; anything conceptually load-bearing stays visible in the notebook. Never hide the thing being taught. Set and mention random seeds — then, once per session, show what changes when the seed changes. One guarded `pip install` cell at the top of setup only.

**Writing style.** Every notebook opens with learning objectives, estimated time for Full and Express paths, and the AD research question it serves. Explain before the cell, interpret after it. Ask students to predict a plot before running it. Define jargon at first use in both directions — a biologist needs "cross-validation" explained; a CS student needs "MCI conversion" explained. Each section ends with a 🧠 interpretation question, answered in a `<details>` block or the facilitator guide. Anticipate the errors students will hit.

**Ethics and framing** — short and non-negotiable. Data provenance, consent and DUA obligations get a paragraph in every N1. Every N4 states plainly that these are teaching artefacts, not diagnostic tools, and discusses bias against underrepresented groups using that dataset's own composition. Module F must address ancestry bias in PRS; module D is largely about this already. Where AD biology is contested, say so in one sentence and move on.

---

## 7. Repository layout

```
├── CLAUDE.md
├── README.md                     # student-facing: setup, schedule, how to choose a module
├── DATASETS.md                   # per-module provenance, licences, download steps, hashes
├── FACILITATOR.md                # timings, pitfalls, discussion answers, module triage advice
├── MODULES.md                    # one-page menu students read during orientation
├── environment.yml               # base + per-module extras
├── notebooks/
│   ├── 00_download_data.ipynb    # run at home, days before; selective, sized, verified
│   ├── 01_setup_check.ipynb      # 30 s; verifies imports, data files, reports runnable modules
│   ├── 02_orientation.ipynb      # the AD research pipeline; how to pick a module
│   ├── modules/                  # one consecutive notebook per module (N1–N4 as sections)
│   │   ├── A_mri_structural.ipynb
│   │   ├── C_fluid_biomarkers.ipynb
│   │   ├── D_confounders.ipynb
│   │   ├── E_clinical_epi.ipynb
│   │   ├── F_genetics.ipynb
│   │   ├── G_transcriptomics.ipynb
│   │   └── H_drug_discovery.ipynb
│   └── 99_crossmodal_wrap.ipynb
├── generate_notebooks.py         # single source: regenerates all notebooks + solutions
├── solutions/                    # mirrors modules/, one _solutions notebook per module with a TODO
├── src/                          # data_registry, download, prepare, simulate, xlsx,
│                                 # data, models, plots, interpret, images
└── data/
    ├── raw/                      # downloaded sources; gitignored
    └── derived/                  # prepared teaching tables, 2D slices; gitignored
```

Each module is a single consecutive notebook whose four sections follow the N1–N4 trajectory (§5); the Express path simply reads or skips the quality-control section rather than opening a separate file. Notebooks are not hand-edited — regenerate them with `python generate_notebooks.py`.

`00_download_data.ipynb` and `01_setup_check.ipynb` are both **pre-session homework** — they exist so the first fifteen minutes are not lost to downloads and broken installs. Both must be runnable days in advance on a bare machine, and the README must say so in its first paragraph.

---

## 8. Two tracks, one room

Every notebook serves both audiences in the same file, with clearly marked lanes:

- 🟢 **Core** — everyone. Read, run, change one parameter, interpret the plot. Zero prior coding required.
- 🔵 **Extension** — real `# TODO` code: custom preprocessing, feature engineering, cross-validation scheme, model architecture, custom metric.
- ⚫ **Deep dive** — optional, may exceed the session; take-home.

Rules:
- **Core cells must never depend on Extension cells having been completed.** A student who ignores every 🔵 still reaches the end of N4 with working results.
- Split into separate files only if inline lanes make a notebook unreadable. Inline is preferred — the room is shared.
- **Advanced students get design guidance, not a blank cell.** Where students design a model, include a "how practitioners actually approach this" box: beat the baseline before adding complexity; parameters versus sample size (biomedical *n* is small — this is *the* constraint); width/depth heuristics; when to standardise; regularisation and dropout as defaults; early stopping; why cross-validation beats a single split at n=300; class weighting versus resampling; telling overfitting apart from a bad architecture. For imaging add: augmentation choices that are anatomically sensible versus nonsense (a horizontally flipped brain is arguable; a vertically flipped brain is not).

**Solutions.** Every notebook containing `# TODO` gets a matching file in `solutions/` with **worked code plus commentary on why**, not an answer key. Never leave solution code commented out inside a student notebook.

---

## 9. Definition of done

Per module, before presenting it as finished:

- [ ] Kernel → **Restart & Run All** completes cleanly in a fresh environment, the whole module notebook (all four sections)
- [ ] Runtime measured and recorded per notebook **on CPU**, for both Full and Express paths
- [ ] Express path verified to work without the student having run N2
- [ ] 🟢 Core path works end-to-end with every 🔵 cell untouched
- [ ] Every `# TODO` has a solution in `solutions/`
- [ ] Grouped splitting used wherever subjects contribute more than one row
- [ ] N4 ends with a summary figure for the student's own notes — **nothing written to shared state**, and `99_crossmodal_wrap.ipynb` still runs
- [ ] Imaging modules: CNN degrades gracefully without PyTorch, and a hosted-runtime badge is present *if and only if* the module exceeds the CPU budget (§4.3)
- [ ] Feasibility verdict (Green/Amber/Red) stated, and any simulated data labelled as such in the first markdown cell
- [ ] The module is registered in `src/data_registry.py` with **measured** download sizes and SHA-256 checksums (or an explicit `volatile: True` with the reason), and appears correctly in `00_download_data.ipynb`'s size table
- [ ] `00_download_data.ipynb` verified end-to-end for this module from a **cold start** (no `data/raw`, no `data/derived`): both the widget and the `MODULES_TO_FETCH = [...]` fallback path, re-run safely, and the status table reporting ✅
- [ ] Every dataset claim in `DATASETS.md` verified against the source this week
- [ ] No absolute paths, no author-machine paths, no network calls in the critical local path
- [ ] Every plot has axis labels, units and a caption a non-coder can read
- [ ] AD framing present in every notebook, not just the first
- [ ] Minute estimates in each notebook header; module totals fit §3

---

## 10. When in doubt

Ask the user. Specifically: ask before choosing a dataset, before declaring a module Red, before dropping a planned notebook, and before adding a dependency heavier than scikit-learn.

**Build modules one at a time, C first** (most reliably Green, best default for non-coders), then D (reuses C's data), then **H** (small, Green, self-contained, and the cheapest way to get a basic-research module into the session), then A, then G, then E, F. Get one module fully working end-to-end and reviewed before starting the next — seven half-finished modules are worth less than three that run.

**Aim for at least one clinical and one basic-research module before adding breadth.** A student who does C in full and H in express has seen the whole arc — patient data and molecular discovery — which is worth more than four diagnostic modules that differ only in file format.
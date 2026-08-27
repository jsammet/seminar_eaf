# Alzheimer's Disease AI Practical

A 3.5-hour hands-on session. Seven self-contained modules, each pointing machine learning at a different
kind of Alzheimer's data. You do **one properly and sample a second** — there is no competition and no
shared scoreboard, because the modules are not comparable and pretending otherwise would teach the wrong
lesson.

## Before the session — two notebooks, at home, please

1. **`notebooks/00_download_data.ipynb`** — downloads about 18 MB of real data from OASIS, GEO, the GWAS
   Catalog and MoleculeNet. Takes a couple of minutes. Runs on a bare Python install.
2. **`notebooks/01_setup_check.ipynb`** — thirty seconds; tells you which modules will run on your machine.

Do these **at least two days before**. Thirty laptops downloading data over seminar Wi-Fi is a guaranteed
way to lose the first half hour. If anything is not ✅, send the instructor a screenshot beforehand.

## Setup

```bash
conda env create -f environment.yml
conda activate ad-ai-practical
jupyter lab
```

Or with pip: `pip install numpy pandas matplotlib scikit-learn scipy jupyter ipywidgets`.

Everything runs on a **CPU laptop**. No GPU, no cloud account, no internet during the session.

## The modules

| | Module | Data | The question |
|---|---|---|---|
| **A** | Structural MRI | real OASIS-2 measures + simulated slices | Can a brain scan tell us who has dementia? |
| **C** | Blood & CSF biomarkers | simulated from published cohorts | Can a blood test identify Alzheimer's? |
| **D** | Confounding | real OASIS-1 | Is the model learning disease, or who was recruited? |
| **E** | Clinical records | simulated cohort | Which life factors predict a later diagnosis? |
| **F** | Genetics | real GWAS effects + simulated genotypes | How much risk is written in the genome? |
| **G** | Brain transcriptomics | real post-mortem brains (GEO) | Which genes differ in the Alzheimer's brain? |
| **H** | Small-molecule chemistry | real BACE1 compounds | Which molecules are worth making? |

**Never written code before? Start with C**, then sample D. **Want to build something?** A, which trains a
support vector machine and a convolutional neural network on brain images. **Biologist?** G. Read
`notebooks/02_orientation.ipynb` for the full guide, and `MODULES.md` for the one-page menu.

Five of the seven modules use real downloaded data. **C and E are entirely simulated** — no shareable
individual-level fluid-biomarker table or health record exists — and they say so in their first cell, every
time. `DATASETS.md` records every source, licence, checksum and preprocessing step.

## How a module works

Four sections, identical in every module: **understand the data → quality control → build models → read the
results.** Along the way:

- ✏️ **YOUR TURN** cells — change one clearly marked value, re-run, watch the figure change. Everyone does
  these; no coding required.
- 🟢 run and read · 🔵 write a little code (`# TODO`, worked answers in `solutions/`) · ⚫ take home
- 🧠 questions with the answer hidden underneath, so you can try first
- Every modelling and results step draws a **figure**. No step ends on a bare number.

## Layout

```
notebooks/00_download_data.ipynb   run at home: downloads and prepares everything
notebooks/01_setup_check.ipynb    run at home: 30-second check
notebooks/02_orientation.ipynb    how to choose your module
notebooks/modules/                the seven modules
notebooks/99_crossmodal_wrap.ipynb  closing discussion
solutions/modules/                worked answers, with commentary on why
src/                              the shared API every module uses
generate_notebooks.py             regenerates every notebook — do not hand-edit them
data/raw/, data/derived/          created by the download notebook
```

Notebooks are generated, never hand-edited. To change one, edit `generate_notebooks.py` and run
`python generate_notebooks.py`.

## A standing caveat

Everything here is teaching material. Nothing built in these notebooks is a diagnostic tool, and every
module ends by asking what would have to be true before it could be.

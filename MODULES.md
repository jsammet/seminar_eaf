# Module menu

Pick **one to work through fully** and **one to sample**. There is no scoreboard: your results are yours.

| | Module | The question | Data | Pick it if you… |
|---|---|---|---|---|
| **A** | Structural MRI | Can a brain scan tell us who has dementia? | real OASIS-2 volumetrics + simulated 2D slices | want to train an SVM and a CNN on images |
| **C** | Blood & CSF biomarkers | Can a blood test identify Alzheimer's? | simulated from published cohorts | **have never written code — start here** |
| **D** | Confounding | Is the model learning disease, or who was recruited? | real OASIS-1 (ages 18–96) | enjoy arguing about what a result means |
| **E** | Clinical records | Which life factors predict a later diagnosis? | simulated prospective cohort | want survival analysis and interpretability |
| **F** | Genetics | How much risk is written in the genome? | real GWAS Catalog effects + simulated genotypes | want to build a polygenic score by hand |
| **G** | Brain transcriptomics | Which genes differ in the Alzheimer's brain? | 31 real post-mortem brains (GEO GSE1297) | prefer discovery to prediction |
| **H** | Small-molecule chemistry | Which molecules are worth making? | 1513 real BACE1 compounds | want drug discovery, not patients |

## The flaw each module is built around

| | The trap |
|---|---|
| **A** | **Subject-level leakage** — one patient, several scans, split across train and test |
| **C** | **Label leakage** through the MMSE, plus missingness that tracks severity |
| **D** | **Confounding** — age is entangled with diagnosis; education's effect reverses when you stratify |
| **E** | **Competing risk** of death, **reverse causation**, **immortal time bias** |
| **F** | **Multiple testing**, **population stratification**, and scores that do not transfer between ancestries |
| **G** | **p ≫ n**, and **cell-composition change** masquerading as gene regulation |
| **H** | **Scaffold leakage** — the exact twin of module A's problem, in a different discipline |

**A and H are the same mathematical problem** in two fields that rarely cite each other, with the same
one-argument fix. **C and D are the same kind of dataset** asked two different questions. Those pairings are
the most transferable thing in the day.

## Suggested pairings

- **No coding background** → C in full, D to sample.
- **Comfortable coder** → A in full, H to sample.
- **Biologist** → G in full, C to sample.
- **Interested in prevention** → E in full, F to sample.
- **Widest view of the field** → any clinical module (A, C, D, E, F) plus a discovery module (G or H).
  G and H involve no patient at all: G asks what to study next, H asks what to synthesise next. Both sit
  *upstream* of everything the clinical modules do, and that contrast is what the closing discussion is
  built around.

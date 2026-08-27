# Facilitator notes

## Before the day

Send `README.md` and tell students to run `00_download_data.ipynb` and `01_setup_check.ipynb` **at least two
days ahead**, and to send you a screenshot of the verification table if anything is not ✅. Ask for those
screenshots — the ones who do not reply are the ones who will have no data on the day.

**Bring the `data/raw` folder on a USB stick.** It is 18 MB. The download notebook has an offline fallback
cell (`INSTRUCTOR_FOLDER`) that copies from it; students then re-run section 4 and are ready in a minute.

Two live-source caveats worth knowing:

- The **GWAS Catalog** download (module F) grows every week. Its checksum is deliberately not pinned; the
  downloader checks size and parseability instead. If EMBL-EBI changes the download endpoint, module F's
  entry in `src/data_registry.py` is the only place to fix.
- The **OASIS** site rejects unusual user agents. `src/download.py` sends a browser string for this reason.
  If OASIS moves the files, the links live on the OASIS-1 and OASIS-2 pages.

## Timing

| Block | Minutes |
|---|---|
| Orientation (`02_orientation.ipynb`) | 15 |
| **Module 1 — full path** | 85 |
| Break | 15 |
| **Module 2 — express path** | 55 |
| Cross-modal wrap-up (`99_crossmodal_wrap.ipynb`) | 25 |
| Slack | 15 |

**Express path:** every module has a `## 2.x QC verdict` cell that ends with *"Express path: start here."*
Tell students on their second module to read section 2's figures without doing the ✏️ turns, then work
sections 3 and 4 properly. The modelling and interpretation are never cut — those are the point.

**Measured run times (whole notebook, CPU, no user thinking time):**

| Module | Compute | Notes |
|---|---|---|
| A | ~33 s | 3.6 and 3.7 train a CNN (~6 s each); 3.9 repeats everything over 5 splits (~15 s) |
| C | ~13 s | 3.3 sweeps a hyperparameter (~7 s); 4.3 computes exact Shapley values |
| D | ~4 s | 4.3 computes exact Shapley values |
| E | ~6 s | 4.2 computes exact Shapley values (~2 s) |
| F | ~4 s | 4.2 computes exact Shapley values |
| G | ~3 s | |
| H | ~17 s | 3.1 fits eight models; 4.3 computes exact Shapley values |

Everything else is reading, which is where the 85 minutes actually goes.

## Module triage

- **Genuine beginners → C.** Fastest, most legible, cleanest arc. Then D as express — same style of data,
  much harder question.
- **CS students → A.** It is the only module with images, an SVM on raw pixels, and a real CNN, and its 3.9
  cell is the best antidote to "I'll just use deep learning" in the whole course. Send them to H as express.
- **Biologists → G.** No accuracy score anywhere. Then C as express.
- **Someone bored halfway through** → point at the ⚫ take-home suggestions in the 🎚 Go further boxes.

## What to make sure gets said

- **A ↔ H are the same problem.** Subject leakage and scaffold leakage are identical mathematics with
  identical fixes, in two disciplines that never talk. If you get one thing across today, get this.
- **A's section 3.9** produces roughly: extracted volumes 0.83 ± 0.03, CNN 0.72 ± 0.06, SVM on raw pixels
  0.68 ± 0.05, eigenbrains 0.67 ± 0.04. The simple number wins, and the spread is larger than every gap between methods. Let the
  room sit with that before you explain it.
- **C's section 1.5** plants the MMSE. Most students will notice it is "too good" without prompting; give
  them the chance before you say anything.
- **D is not about accuracy** and students trained on the other modules will keep trying to maximise the
  bar. Redirect: the deliverable is a defensible judgement, not a tall bar.
- **F's AUROC around 0.70 is a good result.** Say this *before* they see it, or they will read it as failure.
- **G's answer is a gene list and a picture.** Do not let anyone turn the clustering into a diagnostic claim.
- **H ends on the BACE1 trial failures.** A perfect model would have ranked verubecestat at the top. That is
  the closing note for the whole day: a model can only be as right as the question it was asked.

## The interpretability thread (modules C, D, E, F, H)

`src/interpret.py` computes **exact** Shapley values by enumerating all 2^n coalitions — no `shap`
dependency, and students see the actual definition rather than a library call. It is capped at 10 features
and takes 1–3 seconds. Two things worth pointing out in the room:

- The contributions **add up exactly** to the prediction; each notebook prints the arithmetic so students
  can check it. That additivity is the guarantee no other importance measure offers.
- **Module D section 4.3 is the one to dwell on.** Ablation says deleting `age` costs nothing; Shapley says
  age drives about a quarter of every prediction. Both are correct, about different questions, and the
  reason they disagree — correlated features standing in for each other — is the whole module in miniature.

## Discussion answers

Every 🧠 box already carries a worked answer in a collapsed `<details>` block, so students who work alone
are not stuck. The final question in each module's section 4.6 is deliberately open — those are the ones for
the room, not for the notebook.

## Things that will go wrong

| Symptom | Fix |
|---|---|
| `FileNotFoundError` naming a raw file | They skipped the download notebook. The error message names the exact file and path; the USB fallback takes a minute. |
| Module A's CNN cell prints "PyTorch is not installed" | Nothing is broken. It trains an equivalent dense network and says so. Do not stop to install torch mid-session. |
| Module E prints "lifelines is not installed" | Same — it shows logistic odds ratios instead. The forest plot still appears. |
| `ipywidgets` renders nothing in the download notebook | Expected on some installs. The `MODULES_TO_FETCH` list above it does the same job and always works. |
| A ✏️ cell produces an error after editing | Almost always a typo in a quoted string. The banner comments list the exact valid values. |
| Someone finishes a module in 40 minutes | They skipped the ✏️ turns. Send them back to section 2. |

## Deliberately absent

There is **no leaderboard and no shared results file.** Students do not compare numbers with each other, and
the wrap-up notebook says why: different cohorts, sample sizes, label definitions and difficulty make the
numbers incomparable, and putting them on one axis would teach exactly the wrong thing. If a student asks
who "won", that is the discussion, not a failure of the design.

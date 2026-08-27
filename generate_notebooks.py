"""Generate every notebook for the Alzheimer's disease AI practical.

Notebooks are never hand-edited. Change this file and run:

    python generate_notebooks.py

Design rules that apply to all seven modules:

* One notebook per module, four sections in a fixed order: understand the data,
  quality control, model, results. A student who switches modules recognises
  the structure immediately.
* Every section is broken into small steps with a short explanation before the
  cell and an interpretation after it.
* Every section contains at least one "YOUR TURN" cell: a single clearly marked
  value the student changes, which produces a *visibly different figure*.
* Every modelling and results step draws a figure. No step ends on a bare number.
* Three lanes, marked inline: 🟢 everyone, 🔵 write some code, ⚫ take-home.
* No leaderboard, no shared scoreboard, no comparison between students.
"""
import json
import shutil
from pathlib import Path

# folder stem -> (module id, title, one-line question)
MODULES = {
    "A_mri_structural": ("A", "Structural MRI", "Can a brain scan tell us who has dementia?"),
    "C_fluid_biomarkers": ("C", "Blood and CSF biomarkers", "Can a blood test tell us who has Alzheimer's disease?"),
    "D_confounders": ("D", "Confounding", "Is the model learning the disease, or learning who was recruited?"),
    "E_clinical_epi": ("E", "Clinical records", "Which life-course factors predict a later dementia diagnosis?"),
    "F_genetics": ("F", "Genetics", "How much of Alzheimer's risk can we read off the genome?"),
    "G_transcriptomics": ("G", "Brain transcriptomics", "Which genes differ in the Alzheimer's brain?"),
    "H_drug_discovery": ("H", "Small-molecule chemistry", "Which molecules are worth making in the lab?"),
}


# --- notebook plumbing --------------------------------------------------------

def md(source, ident):
    return {"cell_type": "markdown", "metadata": {"id": ident},
            "source": [line + "\n" for line in source.rstrip("\n").split("\n")]}


def code(source, ident):
    return {"cell_type": "code", "metadata": {"id": ident}, "execution_count": None, "outputs": [],
            "source": [line + "\n" for line in source.rstrip("\n").split("\n")]}


def notebook_json(cells):
    return json.dumps({
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }, indent=1, ensure_ascii=False)


# --- reusable building blocks -------------------------------------------------

TURN = "# " + "=" * 74 + "\n# ✏️  YOUR TURN\n"
TURN_END = "# " + "=" * 74


def turn(instruction, assignment):
    """The standard 'change one value' banner used in every section."""
    lines = [line for line in instruction.strip().split("\n")]
    body = "\n".join("#   " + line for line in lines)
    return f"{TURN}{body}\n{TURN_END}\n{assignment}"


def go_further(ident, core, extension, deep):
    text = (
        "### 🎚 Go further — pick whichever suits you\n\n"
        f"- 🟢 **Everyone:** {core}\n"
        f"- 🔵 **If you want to write code:** {extension}\n"
        f"- ⚫ **Take home:** {deep}\n"
    )
    return md(text, ident)



def express_catchup(module, body):
    """The cell that makes sections 3 and 4 stand alone.

    Every module's Express path tells students to read section 2 rather than work
    through it. This cell rebuilds everything the later sections need, starting
    from nothing but the setup cell, and is harmless to run twice.
    """
    text = (
        "### 🚏 Taking the Express path? Run this one cell first\n\n"
        "It rebuilds everything sections 3 and 4 need, so you can start here without having run "
        "sections 1 and 2 yourself. **If you did run them, run this anyway** — it just redefines the "
        "same things and costs a second."
    )
    return [md(text, f"{module}-express-md"),
            code("# Express catch-up: safe to run whether or not you did sections 1 and 2.\n" + body,
                 f"{module}-express")]

def setup_cell(module, extra_imports=()):
    imports = "\n".join(extra_imports)
    return code(
        "# Run me first. This finds the project folder, loads the shared helpers,\n"
        "# and prints exactly where this module's data came from.\n"
        "from pathlib import Path\n"
        "import sys\n"
        "repo_root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src').exists())\n"
        "sys.path.insert(0, str(repo_root / 'src'))\n\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import plots\n"
        "from data import load_data, load_extra, provenance\n"
        "from models import split_data, train_model, evaluate, compare_models, sweep_parameter, MODEL_CHOICES\n"
        + (imports + "\n" if imports else "") +
        "\npd.set_option('display.width', 160)\n"
        f"print(provenance('{module}'))",
        f"{module}-setup",
    )


def intro_cell(module, title, question, objectives, data_line, express_line, warning=None):
    bullets = "\n".join(f"{index}. {objective}" for index, objective in enumerate(objectives, start=1))
    banner = f"\n> ⚠️ **{warning}**\n" if warning else ""
    text = (
        f"# Module {module} — {title}\n\n"
        f"## {question}\n"
        f"{banner}\n"
        "### What you will be able to do by the end\n\n"
        f"{bullets}\n\n"
        f"### The data\n\n{data_line}\n\n"
        "### How to work through this notebook\n\n"
        "Run the cells in order, top to bottom. The notebook is split into four sections:\n\n"
        "| | Section | What happens |\n|---|---|---|\n"
        "| 1 | **Understand the data** | Meet every column and every person in the table |\n"
        "| 2 | **Quality control** | Find the flaws before they fool you |\n"
        "| 3 | **Build models** | Start from something trivial, then climb |\n"
        "| 4 | **Read the results** | Turn numbers into a clinical judgement |\n\n"
        "Look out for these markers:\n\n"
        "- ✏️ **YOUR TURN** — change the value shown, re-run the cell, watch the figure change. Everyone does these.\n"
        "- 🟢 run and read · 🔵 write a little code · ⚫ take home\n"
        "- 🧠 a question to think about; the answer is hidden underneath, so try first\n\n"
        f"**In a hurry?** {express_line}\n\n"
        "---\n\n"
        "*Teaching material. Nothing here is a diagnostic tool, and no result in this notebook "
        "is clinical evidence.*"
    )
    return md(text, f"{module}-intro")


def thinking(question, answer, ident):
    return md(
        f"🧠 **Think first:** {question}\n\n"
        f"<details>\n<summary>Click for one good answer</summary>\n\n{answer}\n\n</details>",
        ident,
    )


# =============================================================================
# Module C — blood and CSF biomarkers
# =============================================================================

def build_C():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "C", "Blood and CSF biomarkers",
        "Can a blood test tell us who has Alzheimer's disease?",
        [
            "read a clinical biomarker table and say what every column measures in the body",
            "spot missing data that is *not* missing at random, and say why that matters",
            "explain what an assay detection limit and a batch effect do to a model",
            "train and compare five different models, and change their settings yourself",
            "read a confusion matrix as a clinician would, and say what a missed diagnosis costs",
        ],
        "**This module's table is simulated.** No open dataset of individual Aβ42, p-tau181 and NfL "
        "measurements exists that we are allowed to redistribute, so 420 participants were drawn from "
        "published cohort summaries: the group means, the spread, the assay batch offsets and the "
        "detection limit are all set to realistic published values. The biology is real; the people are not. "
        "Every other module you might pick today uses real measured data.",
        "Skim section 2 (run the cells, read the figures, skip the ✏️ turns) and spend your time on sections 3 and 4.",
        warning="Simulated data — realistic numbers, invented people. Section 1 explains exactly why.",
    ))
    cells.append(setup_cell("C"))

    # --- Section 1 -----------------------------------------------------------
    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "Before any modelling, you need to be able to say out loud what a single row is. "
        "Here, one row is **one person, at one memory-clinic visit**.",
        "C-s1"))

    cells.append(md(
        "### 1.1 Load the table and look at it\n\n"
        "`load_data('C')` returns a pandas *DataFrame* — a table, like a spreadsheet, where every column "
        "has a name and a type. `.shape` gives (rows, columns) and `.head()` shows the first few rows.",
        "C-1-1-md"))
    cells.append(code(
        "df = load_data('C')\n"
        "print('This table has', df.shape[0], 'people and', df.shape[1], 'columns.\\n')\n"
        "df.head()",
        "C-1-1"))

    cells.append(md(
        "### 1.2 What does each column actually measure?\n\n"
        "This is the part biologists find obvious and computer scientists do not, and vice versa. "
        "Read it — you cannot judge a model without it.\n\n"
        "| Column | What it is | Why it matters in Alzheimer's disease |\n|---|---|---|\n"
        "| `age` | years | The single strongest risk factor for AD. It will haunt every model you build today. |\n"
        "| `sex` | F / M | Around two-thirds of people with AD are women; some of that is longer life expectancy, some is not. |\n"
        "| `education_years` | years of schooling | A proxy for **cognitive reserve**: more education tends to delay the *appearance* of symptoms, not the underlying pathology. |\n"
        "| `apoe4_carrier` | 0 / 1 | Carrying at least one *APOE* ε4 allele, the biggest common genetic risk factor. |\n"
        "| `site` | site_1/2/3 | Which clinic collected the sample. Different clinics used different assay lots — remember this. |\n"
        "| `diagnosis` | CN / MCI / AD | **The label.** CN = cognitively normal. MCI = mild cognitive impairment, a fuzzy in-between state. AD = diagnosed Alzheimer's dementia. |\n"
        "| `ab42_pg_ml` | amyloid-β 42, pg/ml | Aβ42 is the sticky peptide that forms plaques. Counter-intuitively it goes **down** in blood/CSF in AD — it is being deposited in the brain instead of floating around. |\n"
        "| `ab40_pg_ml` | amyloid-β 40, pg/ml | A related peptide that is *not* strongly deposited. Mostly reflects how much amyloid you make overall. |\n"
        "| `ab42_40_ratio` | Aβ42 ÷ Aβ40 | The ratio cancels out person-to-person differences in total production. Keep an eye on whether it beats Aβ42 alone. |\n"
        "| `ptau181_pg_ml` | phosphorylated tau 181, pg/ml | Tangle pathology. Goes **up** in AD, and is fairly specific to it. |\n"
        "| `nfl_pg_ml` | neurofilament light, pg/ml | Leaks out of damaged axons. Goes up in AD — and in stroke, MS, ALS, ageing. Sensitive, not specific. |\n"
        "| `gfap_pg_ml` | glial fibrillary acidic protein, pg/ml | Astrocyte activation; rises early in the amyloid cascade. |\n"
        "| `mmse` | 0–30 | Mini-Mental State Examination, a bedside cognitive test. 30 is perfect, under ~24 suggests impairment. **Note where this number comes from — we come back to it.** |",
        "C-1-2-md"))

    cells.append(md(
        "### 1.3 Who is in this cohort?\n\n"
        "**Predict before you run:** the three diagnostic groups — will they be equally sized? "
        "Should the AD group be older or younger than the CN group?",
        "C-1-3-md"))
    cells.append(code(
        "plots.plot_class_balance(df['diagnosis'], title='Diagnostic groups in the cohort')\n"
        "plt.show()\n\n"
        "plots.plot_by_group(df, 'age', 'diagnosis', unit='(years)',\n"
        "                    title='Age distribution by diagnosis — notice the overlap, and the shift')\n"
        "plt.show()\n\n"
        "print(df.groupby('diagnosis')[['age', 'education_years', 'apoe4_carrier']].mean().round(2))",
        "C-1-3"))

    cells.append(md(
        "### 1.4 ✏️ Your turn — look at one biomarker at a time\n\n"
        "Change `BIOMARKER` below to any of these and re-run the cell:\n\n"
        "`'ab42_pg_ml'` · `'ab40_pg_ml'` · `'ab42_40_ratio'` · `'ptau181_pg_ml'` · `'nfl_pg_ml'` · `'gfap_pg_ml'` · `'mmse'`\n\n"
        "For each one, ask yourself: **do the three coloured histograms sit on top of each other, or apart?** "
        "A marker whose groups overlap completely cannot separate patients no matter how clever the model is.",
        "C-1-4-md"))
    cells.append(code(
        turn(
            "Pick a biomarker. Try at least three of them.\n"
            "Watch the 'separation score' printed underneath: it is how many\n"
            "standard deviations apart the CN and AD group means are.",
            "BIOMARKER = 'ab42_40_ratio'",
        ) + "\n\n"
        "plots.plot_by_group(df, BIOMARKER, 'diagnosis',\n"
        "                    title=f'{BIOMARKER} by diagnosis')\n"
        "plt.show()\n\n"
        "summary = df.groupby('diagnosis')[BIOMARKER].agg(['mean', 'std', 'count']).round(3)\n"
        "print(summary)\n\n"
        "cn, ad = df[df.diagnosis == 'CN'][BIOMARKER].dropna(), df[df.diagnosis == 'AD'][BIOMARKER].dropna()\n"
        "pooled_sd = np.sqrt((cn.var() + ad.var()) / 2)\n"
        "separation = abs(cn.mean() - ad.mean()) / pooled_sd\n"
        "print(f'\\nSeparation score (CN vs AD): {separation:.2f} standard deviations')\n"
        "print('Under 0.5 = the groups are basically the same. Over 1.5 = a strong single marker.')",
        "C-1-4"))

    cells.append(md(
        "### 1.5 Wait, that's odd\n\n"
        "Let's rank every numeric column by how strongly it tracks an AD diagnosis. "
        "One of them is going to look suspiciously good.",
        "C-1-5-md"))
    cells.append(code(
        "is_ad = (df['diagnosis'] == 'AD').astype(int)\n"
        "strength = df.select_dtypes('number').apply(lambda column: column.corr(is_ad)).drop(labels=[], errors='ignore')\n"
        "strength = strength.dropna().sort_values(key=abs, ascending=False)\n\n"
        "plots.plot_importance(strength.index, strength.values,\n"
        "                      title='Correlation of each measurement with an AD diagnosis',\n"
        "                      xlabel='correlation (negative = lower in AD)')\n"
        "plt.show()\n"
        "print(strength.round(3))",
        "C-1-5"))
    cells.append(thinking(
        "`mmse` is the strongest signal in the table by a wide margin. Should we be pleased?",
        "No. The MMSE is a **cognitive test**, and a clinician used the patient's cognitive performance to "
        "assign the diagnosis in the first place. Predicting the diagnosis from the MMSE is close to "
        "predicting the label from the label. It is not *impossible* to use — an MMSE is cheap and a blood "
        "draw is not — but a model that leans on it is not telling you anything about **blood biomarkers**, "
        "which is the actual question this module asks. We come back to this in section 2.5.",
        "C-1-5-think"))

    cells.append(go_further(
        "C-1-further",
        "re-run cell 1.4 with `'nfl_pg_ml'` and with `'ptau181_pg_ml'` and decide which you would rather have as a screening test.",
        "make a scatter plot of `ab42_40_ratio` against `ptau181_pg_ml`, coloured by diagnosis, using "
        "`plots.plot_scatter(df['ab42_40_ratio'], df['ptau181_pg_ml'], colour_by=df['diagnosis'], ...)`. "
        "Do the two markers carry the same information, or different information?",
        "the real Aβ42/40 ratio is measured on several different analytical platforms that disagree with each "
        "other. Look up 'Aβ42/40 harmonisation' and consider what that means for a threshold published by one lab.",
    ))

    # --- Section 2 -----------------------------------------------------------
    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "This is the section that matters most and gets skipped most. Four flaws live in this table, and each "
        "one can make a model look better than it is.",
        "C-s2"))

    cells.append(md(
        "### 2.1 Flaw one — missing values that are not missing at random\n\n"
        "Some p-tau181 and GFAP results are missing. The dangerous question is not *how many*, it is "
        "**who**. If sicker patients are more likely to miss a blood draw, then 'has a p-tau result' is "
        "itself a clue about diagnosis, and any analysis that quietly drops those rows is now studying a "
        "different, healthier population.",
        "C-2-1-md"))
    cells.append(code(
        "plots.plot_missingness(df, title='Missing values, as a percentage of all 420 people')\n"
        "plt.show()\n\n"
        "# The real question: is a missing p-tau equally likely in every group?\n"
        "missing_rate = df.assign(missing=df['ptau181_pg_ml'].isna()).groupby('diagnosis')['missing'].mean()\n"
        "plots.plot_score_comparison(missing_rate.index.tolist(), (100 * missing_rate).tolist(),\n"
        "                            title='Percentage of people with NO p-tau181 result, by diagnosis',\n"
        "                            ylabel='percent missing')\n"
        "plt.show()\n"
        "print('If these bars are not level, the missingness carries information about the diagnosis.')",
        "C-2-1"))

    cells.append(md(
        "### 2.2 ✏️ Your turn — how you fill the gaps changes the answer\n\n"
        "You have three sensible options, and they genuinely disagree:\n\n"
        "- `'median'` — fill each gap with the middle value of that column. Safe, ignores the person.\n"
        "- `'mean'` — fill with the average. Pulled around by extreme values.\n"
        "- `'drop'` — throw away every row with any gap. Honest-looking, but see 2.1.\n\n"
        "Change `HOW_TO_HANDLE_MISSING` and re-run. The figure shows how the held-out score moves, "
        "and how many people you have left.",
        "C-2-2-md"))
    cells.append(code(
        turn(
            "Try all three: 'median', 'mean', 'drop'\n"
            "Then answer: does the best score belong to the best method?",
            "HOW_TO_HANDLE_MISSING = 'median'",
        ) + "\n\n"
        "feature_columns = ['age', 'sex', 'education_years', 'apoe4_carrier',\n"
        "                   'ab42_40_ratio', 'ptau181_pg_ml', 'nfl_pg_ml', 'gfap_pg_ml']\n\n"
        "scores, labels, sizes = [], [], []\n"
        "for strategy in ['median', 'mean', 'drop']:\n"
        "    table = df.dropna(subset=feature_columns) if strategy == 'drop' else df\n"
        "    X = table[feature_columns]\n"
        "    y = (table['diagnosis'] == 'AD').astype(int)\n"
        "    X_train, X_test, y_train, y_test = split_data(X, y)\n"
        "    fill = 'median' if strategy == 'drop' else strategy\n"
        "    model = train_model('logistic', X_train, y_train, impute=fill)\n"
        "    scores.append(evaluate(model, X_test, y_test)['balanced_accuracy'])\n"
        "    labels.append(f'{strategy}\\n(n={len(table)})')\n"
        "    sizes.append(len(table))\n\n"
        "highlight = ['#e08214' if s.startswith(HOW_TO_HANDLE_MISSING) else '#2c6fbb' for s in ['median', 'mean', 'drop']]\n"
        "plots.plot_score_comparison(labels, scores, colours=highlight, reference=0.5,\n"
        "                            title=f'Your choice ({HOW_TO_HANDLE_MISSING}) is in orange')\n"
        "plt.show()\n"
        "print('Dropping rows costs you', len(df) - min(sizes), 'people — and not a random', len(df) - min(sizes), 'people.')",
        "C-2-2"))

    cells.append(md(
        "### 2.3 Flaw two — the assay cannot see below its detection limit\n\n"
        "Every immunoassay has a floor. Below it the machine reports the floor, not the true value. "
        "In this dataset the p-tau181 assay bottoms out at **8.0 pg/ml**. Those people do not have a "
        "p-tau of exactly 8.0 — we simply do not know what they have. This is called **left censoring**.",
        "C-2-3-md"))
    cells.append(code(
        "limit = 8.0\n"
        "at_limit = (df['ptau181_pg_ml'] <= limit).sum()\n\n"
        "fig, ax = plt.subplots(figsize=(7, 3.6))\n"
        "ax.hist(df['ptau181_pg_ml'].dropna(), bins=40, color='#2c6fbb')\n"
        "ax.axvline(limit, color='#c0392b', linewidth=2)\n"
        "ax.annotate(f'detection limit\\n{at_limit} people pile up here', (limit, ax.get_ylim()[1] * 0.7),\n"
        "            xytext=(20, 0), textcoords='offset points', color='#c0392b', fontsize=9)\n"
        "ax.set_xlabel('p-tau181 (pg/ml)'); ax.set_ylabel('number of people')\n"
        "ax.set_title('The spike on the left is not biology, it is the machine')\n"
        "plt.tight_layout(); plt.show()",
        "C-2-3"))

    cells.append(md(
        "### 2.4 Flaw three — the three clinics did not use the same assay lot\n\n"
        "`site` records which clinic drew the blood. If one clinic's assay reads systematically high, then "
        "'which clinic' becomes a fake biomarker. It only becomes a *disaster* if the clinics also recruited "
        "different kinds of patient — check both.",
        "C-2-4-md"))
    cells.append(code(
        "plots.plot_group_means(df, 'ptau181_pg_ml', 'site', unit='(pg/ml)',\n"
        "                       title='p-tau181 by collection site — same biology, different machines')\n"
        "plt.show()\n\n"
        "composition = pd.crosstab(df['site'], df['diagnosis'], normalize='index').round(3) * 100\n"
        "print('Percentage of each site\\'s patients in each diagnostic group:')\n"
        "print(composition)\n"
        "print('\\nIf these rows look alike, site is only noise. If they differ, site is a confounder.')",
        "C-2-4"))

    cells.append(md(
        "### 2.5 Flaw four — leakage, in two flavours\n\n"
        "**Leakage** is when information that would not be available at prediction time sneaks into training. "
        "It is the single most common reason a published medical AI result fails to replicate.\n\n"
        "*Flavour one — preprocessing leakage.* If you scale or impute using the whole dataset and *then* "
        "split, the training set has secretly seen the test set's average.\n\n"
        "*Flavour two — label leakage.* If a feature is part of how the label was decided (`mmse`, here), the "
        "model gets to peek at the answer.\n\n"
        "We do the wrong thing on purpose, once, so you can see the size of the lie.",
        "C-2-5-md"))
    cells.append(code(
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.linear_model import LogisticRegression\n"
        "from sklearn.impute import SimpleImputer\n\n"
        "columns_no_mmse = ['age', 'sex', 'education_years', 'apoe4_carrier',\n"
        "                   'ab42_40_ratio', 'ptau181_pg_ml', 'nfl_pg_ml', 'gfap_pg_ml']\n"
        "columns_with_mmse = columns_no_mmse + ['mmse']\n"
        "y_all = (df['diagnosis'] == 'AD').astype(int)\n\n"
        "# --- the WRONG way: impute and scale the whole table first, then split ---\n"
        "numeric = df[columns_no_mmse].select_dtypes('number')\n"
        "filled = pd.DataFrame(SimpleImputer(strategy='median').fit_transform(numeric), columns=numeric.columns)\n"
        "scaled = pd.DataFrame(StandardScaler().fit_transform(filled), columns=numeric.columns)\n"
        "X_train, X_test, y_train, y_test = split_data(scaled, y_all)\n"
        "leaky = LogisticRegression(max_iter=2000, class_weight='balanced').fit(X_train, y_train)\n"
        "leaky_score = evaluate(leaky, X_test, y_test)['auroc']\n\n"
        "# --- the RIGHT way: split first, fit the preprocessing inside the pipeline ---\n"
        "X_train, X_test, y_train, y_test = split_data(df[columns_no_mmse], y_all)\n"
        "clean_score = evaluate(train_model('logistic', X_train, y_train), X_test, y_test)['auroc']\n\n"
        "# --- and the label-leakage version: let the model see the cognitive test ---\n"
        "X_train_m, X_test_m, y_train_m, y_test_m = split_data(df[columns_with_mmse], y_all)\n"
        "mmse_score = evaluate(train_model('logistic', X_train_m, y_train_m), X_test_m, y_test_m)['auroc']\n\n"
        "plots.plot_score_comparison(\n"
        "    ['scaled before splitting\\n(leaky)', 'split first\\n(honest)', 'honest, but shown\\nthe MMSE'],\n"
        "    [leaky_score, clean_score, mmse_score],\n"
        "    colours=['#c0392b', '#2c6fbb', '#e08214'], reference=0.5,\n"
        "    title='Three AUROCs. Only the blue one answers the question we asked.', ylabel='AUROC')\n"
        "plt.show()",
        "C-2-5"))
    cells.append(thinking(
        "The MMSE model scores highest of all three. Why is it still the wrong model for this module's question?",
        "Because the question was *\"can a **blood test** identify Alzheimer's disease?\"* — and that model's "
        "answer is mostly \"a cognitive test can\". We already knew that; it is how the diagnosis was made. "
        "A model is only as useful as the decision it would change, and this one changes nothing: any clinic "
        "that can run an MMSE already has the MMSE. The blood-only model, at a lower AUROC, is the one that "
        "would actually add information — for instance in a GP surgery, before a memory-clinic referral.",
        "C-2-5-think"))

    cells.append(md(
        "### 2.6 ✏️ Your turn — decide what goes into the model\n\n"
        "You are now the analyst. Switch each of these on and off, re-run, and watch the score move. "
        "There is no single right answer — but you should be able to *justify* the one you pick.",
        "C-2-6-md"))
    cells.append(code(
        turn(
            "Set each of these to True or False and re-run.\n"
            "Suggested experiments:\n"
            "  (a) everything False except biomarkers -> the honest blood-only model\n"
            "  (b) USE_MMSE = True                    -> watch it jump, then ask why\n"
            "  (c) USE_SITE = True                    -> does knowing the clinic help? should it?",
            "USE_MMSE   = False   # the cognitive test the diagnosis was based on\n"
            "USE_SITE   = False   # which clinic collected the sample\n"
            "USE_AGE    = True    # age and sex\n"
            "USE_RATIO  = True    # Abeta42/40 ratio instead of Abeta42 alone",
        ) + "\n\n"
        "chosen = ['ptau181_pg_ml', 'nfl_pg_ml', 'gfap_pg_ml', 'apoe4_carrier', 'education_years']\n"
        "chosen += ['ab42_40_ratio'] if USE_RATIO else ['ab42_pg_ml']\n"
        "if USE_AGE:\n"
        "    chosen += ['age', 'sex']\n"
        "if USE_SITE:\n"
        "    chosen += ['site']\n"
        "if USE_MMSE:\n"
        "    chosen += ['mmse']\n\n"
        "X_train, X_test, y_train, y_test = split_data(df[chosen], y_all)\n"
        "chosen_model = train_model('logistic', X_train, y_train)\n"
        "chosen_metrics = evaluate(chosen_model, X_test, y_test)\n\n"
        "plots.plot_score_comparison(list(chosen_metrics), list(chosen_metrics.values()),\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title=f'Your feature set: {len(chosen)} columns', ylabel='score')\n"
        "plt.show()\n"
        "print('Columns you gave the model:', ', '.join(chosen))",
        "C-2-6"))

    cells.append(md(
        "### 2.7 QC verdict — write it down before you model\n\n"
        "**Usable? Yes, with three caveats.**\n\n"
        "1. p-tau181 is missing more often in the sicker groups, so any row-dropping analysis studies a "
        "healthier cohort than the one you meant to study. Impute inside the pipeline instead.\n"
        "2. p-tau181 is left-censored at 8 pg/ml. Values at the floor are upper bounds, not measurements. "
        "A model will happily treat that spike as a real cluster.\n"
        "3. Site shifts the p-tau readings. Unless the sites recruited identical patients, some of any "
        "'biomarker' signal is really 'which building'.\n\n"
        "**And a decision:** we exclude `mmse` from the main model, because this module asks what a *blood "
        "test* can do. We will report the blood-only number as the headline.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "C-2-verdict"))

    cells.append(go_further(
        "C-2-further",
        "go back to 2.6 and find the smallest set of columns that still reaches an AUROC above 0.85.",
        "write a cell that replaces the censored p-tau values (≤ 8.0) with `np.nan` and lets the imputer handle "
        "them as genuinely unknown. Does the model get better, worse, or just more honest?",
        "read about **inverse probability weighting**, the standard statistical fix for data that is missing "
        "*because of* the thing you are studying.",
    ))
    solutions["C-2-further-sol"] = None

    # --- Section 3 -----------------------------------------------------------
    cells.append(md(
        "---\n# 3 · Build models\n\n"
        "The rule is always the same: **start with something so simple it is almost insulting, then only add "
        "complexity that pays for itself.** If a random forest cannot beat a single blood test with a "
        "threshold on it, the random forest has earned nothing.",
        "C-s3"))
    cells += express_catchup("C", "df = load_data('C')\ny_all = (df['diagnosis'] == 'AD').astype(int)\nprint(f'{len(df)} participants; {y_all.sum()} with an AD diagnosis. Ready for section 3.')")

    cells.append(md(
        "### 3.1 Two baselines to beat\n\n"
        "*Baseline zero:* always say \"not AD\". It gets most people right, because most people are not AD. "
        "That is why plain accuracy is a bad metric here.\n\n"
        "*Baseline one:* pick a single biomarker and a cutoff. This is genuinely how biomarkers are used in "
        "clinics today. The ROC curve shows every possible cutoff at once.",
        "C-3-1-md"))
    cells.append(code(
        "features = ['age', 'sex', 'education_years', 'apoe4_carrier',\n"
        "            'ab42_40_ratio', 'ptau181_pg_ml', 'nfl_pg_ml', 'gfap_pg_ml']\n"
        "X = df[features]\n"
        "y = (df['diagnosis'] == 'AD').astype(int)\n"
        "X_train, X_test, y_train, y_test = split_data(X, y)\n"
        "print(f'{len(X_train)} people to learn from, {len(X_test)} held back to test on.')\n"
        "print(f'{y_test.sum()} of the {len(y_test)} held-out people actually have AD.\\n')\n\n"
        "# Baseline zero\n"
        "dumb = train_model('baseline', X_train, y_train)\n"
        "print('Always saying \"not AD\":')\n"
        "print(f\"  plain accuracy      {(dumb.predict(X_test) == y_test).mean():.3f}   <- looks fine!\")\n"
        "print(f\"  balanced accuracy   {evaluate(dumb, X_test, y_test)['balanced_accuracy']:.3f}   <- the honest version\\n\")\n\n"
        "# Baseline one: a single marker, every possible cutoff\n"
        "single = -X_test['ptau181_pg_ml'].fillna(X_train['ptau181_pg_ml'].median())\n"
        "plots.plot_roc_pr(y_test, -single, title='One marker (p-tau181), every possible cutoff')\n"
        "plt.show()",
        "C-3-1"))

    cells.append(md(
        "### 3.2 The model ladder\n\n"
        "Now five models on the identical split. Each one is a different *shape* of decision rule:\n\n"
        "| Model | The idea, in one sentence |\n|---|---|\n"
        "| `baseline` | Always guess the commonest answer. |\n"
        "| `logistic` | Add up the markers with weights, squash into a probability. Straight-line boundaries, readable coefficients. |\n"
        "| `knn` | Find the most similar patients we have seen and copy their diagnosis. |\n"
        "| `random_forest` | Ask hundreds of slightly different flowcharts and take a vote. Handles interactions and curvature. |\n"
        "| `svm` | Draw the boundary with the widest possible empty margin around it. |\n"
        "| `mlp` | A small neural network. With 300 patients, do not expect miracles. |\n\n"
        "**Predict before you run:** which will win? Write your guess down.",
        "C-3-2-md"))
    cells.append(code(
        "ladder = ['baseline', 'logistic', 'knn', 'random_forest', 'svm', 'mlp']\n"
        "comparison = compare_models(ladder, X_train, y_train, X_test, y_test)\n"
        "display(comparison)\n\n"
        "plots.plot_model_comparison(comparison, metric='auroc',\n"
        "                            title='Blood-biomarker models on the same held-out patients (AUROC)')\n"
        "plt.show()\n"
        "print('The dashed line at 0.5 is a coin flip. Anything near it has learned nothing.')",
        "C-3-2"))

    cells.append(md(
        "### 3.3 ✏️ Your turn — turn the dial and watch it overfit\n\n"
        "Every model has settings (*hyperparameters*). One of them usually controls **how much the model is "
        "allowed to contort itself around the training data**. Turn it too far and the model memorises the "
        "training patients instead of learning about the disease — that is **overfitting**, and the figure "
        "below shows it as the orange line rising while the blue line falls.\n\n"
        "Change `MODEL` (and optionally `VALUES`) and re-run.",
        "C-3-3-md"))
    cells.append(code(
        turn(
            "Pick a model, then re-run. Try them all:\n"
            "  'logistic'          -> C: smaller = simpler, more regularised\n"
            "  'knn'               -> n_neighbors: 1 memorises, 51 over-smooths\n"
            "  'tree'              -> max_depth: how many questions deep\n"
            "  'random_forest'     -> max_depth\n"
            "  'svm'               -> C: how hard it tries to get every point right\n"
            "  'gradient_boosting' -> learning_rate",
            "MODEL = 'random_forest'",
        ) + "\n\n"
        "description, parameter, values = MODEL_CHOICES[MODEL]\n"
        "print(f'{MODEL}: {description}')\n"
        "print(f'Sweeping {parameter} over {values}\\n')\n\n"
        "swept, train_scores, test_scores = sweep_parameter(\n"
        "    MODEL, parameter, values, X_train, y_train, X_test, y_test)\n\n"
        "plots.plot_parameter_sweep(swept, train_scores, test_scores, parameter,\n"
        "                           title=f'{MODEL}: the gap between the lines IS the overfitting')\n"
        "plt.show()\n"
        "best = values[int(np.argmax(test_scores))]\n"
        "print(f'Best held-out {parameter} for {MODEL}: {best}')",
        "C-3-3"))
    cells.append(thinking(
        "Why is it cheating to pick the setting with the best *held-out* score and then report that score as your result?",
        "Because you just used the test set to make a decision, so it is no longer held out — you have leaked, "
        "gently, through your own choices. The honest procedure is three-way: train on one part, tune on a "
        "*validation* part, and only ever touch the test part once, at the very end. With 420 people that is "
        "wasteful, which is why cross-validation (🔵 below) is the usual answer in biomedicine.",
        "C-3-3-think"))

    cells.append(md(
        "### 3.4 🔵 Your turn to write code — cross-validation\n\n"
        "A single train/test split of 420 people is noisy: shuffle differently and the AUROC moves by several "
        "points. **Cross-validation** splits the data five ways, trains five times, and reports the spread — "
        "far more trustworthy at biomedical sample sizes.\n\n"
        "The helper is already imported for you. Fill in the `# TODO` line.\n\n"
        "> **How practitioners think about this:** at n = 300–500, the error bar on your score is often bigger "
        "than the difference between two models. Before you claim model A beats model B, check whether their "
        "cross-validation ranges overlap. If they do, you have not shown anything.",
        "C-3-4-md"))
    cells.append(code(
        "from models import cross_validated_score\n\n"
        "# TODO (🔵): call cross_validated_score for 'logistic' and for 'random_forest'.\n"
        "#   Signature: cross_validated_score(name, X, y, folds=5, metric='auroc')\n"
        "#   Store each result in the dictionary below, then run the plotting code underneath.\n"
        "fold_scores = {}\n"
        "# fold_scores['logistic'] = ...\n"
        "# fold_scores['random_forest'] = ...\n\n"
        "if fold_scores:\n"
        "    fig, ax = plt.subplots(figsize=(6, 3.8))\n"
        "    for position, (name, scores) in enumerate(fold_scores.items()):\n"
        "        ax.scatter([position] * len(scores), scores, s=60, color='#2c6fbb', zorder=3)\n"
        "        ax.plot([position - 0.18, position + 0.18], [np.mean(scores)] * 2, color='#e08214', linewidth=3)\n"
        "        ax.annotate(f'{np.mean(scores):.3f}\\n± {np.std(scores):.3f}', (position, np.mean(scores)),\n"
        "                    textcoords='offset points', xytext=(24, -6), fontsize=9)\n"
        "    ax.set_xticks(range(len(fold_scores)), list(fold_scores), fontsize=10)\n"
        "    ax.set_ylabel('AUROC'); ax.set_ylim(0.5, 1.02)\n"
        "    ax.set_title('Five folds each. Do the clouds overlap?')\n"
        "    plt.tight_layout(); plt.show()\n"
        "else:\n"
        "    print('Fill in the TODO above to see the figure. Solutions notebook has the answer.')",
        "C-3-4"))
    solutions["C-3-4"] = (
        "from models import cross_validated_score\n\n"
        "# ✅ Worked solution.\n"
        "fold_scores = {}\n"
        "fold_scores['logistic'] = cross_validated_score('logistic', X, y, folds=5, metric='auroc')\n"
        "fold_scores['random_forest'] = cross_validated_score('random_forest', X, y, folds=5, metric='auroc')\n\n"
        "# Why this matters: notice we pass the FULL X and y, not X_train. Cross-validation makes\n"
        "# its own five splits internally, and the preprocessing is refitted inside every fold, so\n"
        "# nothing leaks. If we had passed pre-scaled data, we would have reintroduced the exact\n"
        "# leak we removed in section 2.5.\n"
        "#\n"
        "# Read the output as a range, not a number. If logistic gives 0.91 ± 0.03 and the forest\n"
        "# gives 0.89 ± 0.04, those are the same result. Reporting 'logistic won' would be noise.\n\n"
        "fig, ax = plt.subplots(figsize=(6, 3.8))\n"
        "for position, (name, scores) in enumerate(fold_scores.items()):\n"
        "    ax.scatter([position] * len(scores), scores, s=60, color='#2c6fbb', zorder=3)\n"
        "    ax.plot([position - 0.18, position + 0.18], [np.mean(scores)] * 2, color='#e08214', linewidth=3)\n"
        "    ax.annotate(f'{np.mean(scores):.3f}\\n± {np.std(scores):.3f}', (position, np.mean(scores)),\n"
        "                textcoords='offset points', xytext=(24, -6), fontsize=9)\n"
        "ax.set_xticks(range(len(fold_scores)), list(fold_scores), fontsize=10)\n"
        "ax.set_ylabel('AUROC'); ax.set_ylim(0.5, 1.02)\n"
        "ax.set_title('Five folds each. Do the clouds overlap?')\n"
        "plt.tight_layout(); plt.show()"
    )

    cells.append(go_further(
        "C-3-further",
        "run 3.3 for `'knn'` with `n_neighbors = 1` and explain, in one sentence, why the orange training line hits 1.0.",
        "add `'gradient_boosting'` to the ladder in 3.2 and see whether boosting beats the forest here. "
        "Then try giving the forest `n_estimators=1` — how much of a forest's power is the averaging?",
        "implement a nested cross-validation: an inner loop that picks the hyperparameter and an outer loop "
        "that scores it. This is the only fully honest way to report a tuned model's performance.",
    ))

    # --- Section 4 -----------------------------------------------------------
    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "A number is not a result. In this section every cell produces a **figure**, because the questions "
        "that matter — *who does this model fail? what does a mistake cost? can I trust the probability?* — "
        "are not answerable from a single score.",
        "C-s4"))

    cells.append(md(
        "### 4.1 The four standard views\n\n"
        "We fit one model — logistic regression on the blood markers, no MMSE — and look at it four ways.",
        "C-4-1-md"))
    cells.append(code(
        "final_model = train_model('logistic', X_train, y_train)\n"
        "probability = final_model.predict_proba(X_test)[:, 1]\n"
        "predicted = (probability >= 0.5).astype(int)\n"
        "final_metrics = evaluate(final_model, X_test, y_test)\n\n"
        "plots.plot_confusion(y_test, predicted, labels=('not AD', 'AD'),\n"
        "                     title='Held-out patients: what the model got right and wrong')\n"
        "plt.show()\n\n"
        "plots.plot_roc_pr(y_test, probability, title='Blood-biomarker model, held-out patients')\n"
        "plt.show()\n\n"
        "plots.plot_calibration(y_test, probability)\n"
        "plt.show()\n\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "C-4-1"))
    cells.append(md(
        "**How to read these.**\n\n"
        "- **Confusion matrix** — the bottom-left box is a *missed diagnosis*. In early AD that may mean a "
        "person is not offered an anti-amyloid therapy while it could still help, and is not told what is "
        "happening to them. The top-right box is a *false alarm*: an unnecessary lumbar puncture or PET scan, "
        "cost, and months of fear. These are not interchangeable, and no single accuracy number can tell them apart.\n"
        "- **ROC** — performance across every possible cutoff. AUROC of 0.5 is a coin flip, 1.0 is perfect.\n"
        "- **Precision-recall** — the same model, but it *notices* when cases are rare. The dashed line is what "
        "you would get by guessing at random. Under imbalance this is the more honest curve.\n"
        "- **Calibration** — when the model says \"70% chance\", do 70% of those people actually have AD? "
        "A model can rank patients perfectly (great AUROC) and still be badly calibrated, which makes its "
        "probabilities useless for a conversation with a patient.",
        "C-4-1-read"))

    cells.append(md(
        "### 4.2 ✏️ Your turn — move the threshold, change the medicine\n\n"
        "The model outputs a probability. Turning that into a yes/no needs a **threshold**, and that choice "
        "is a *clinical* decision, not a statistical one.\n\n"
        "- A **screening** test wants a low threshold: catch everyone, tolerate false alarms.\n"
        "- A **confirmatory** test wants a high threshold: be sure before you act.\n\n"
        "Change `DECISION_THRESHOLD` and watch both the curve and the confusion matrix move.",
        "C-4-2-md"))
    cells.append(code(
        turn(
            "Try 0.20, then 0.50, then 0.80.\n"
            "For each: how many AD patients did you miss, and how many\n"
            "healthy people did you send for an unnecessary lumbar puncture?",
            "DECISION_THRESHOLD = 0.5",
        ) + "\n\n"
        "plots.plot_threshold_sweep(y_test, probability, chosen=DECISION_THRESHOLD)\n"
        "plt.show()\n\n"
        "at_threshold = (probability >= DECISION_THRESHOLD).astype(int)\n"
        "plots.plot_confusion(y_test, at_threshold, labels=('not AD', 'AD'),\n"
        "                     title=f'Decisions at threshold {DECISION_THRESHOLD}')\n"
        "plt.show()\n\n"
        "shifted = evaluate(final_model, X_test, y_test, threshold=DECISION_THRESHOLD)\n"
        "print(f\"At {DECISION_THRESHOLD}: sensitivity {shifted['sensitivity']:.2f} \"\n"
        "      f\"(share of AD patients caught), specificity {shifted['specificity']:.2f} \"\n"
        "      f\"(share of healthy people spared).\")\n"
        "print(f'You would send {at_threshold.mean():.0%} of this clinic for further testing.')",
        "C-4-2"))

    cells.append(md(
        "### 4.3 What is the model actually using? Shapley values\n\n"
        "Coefficients tell you about the model. **Shapley values** tell you about *each individual patient*: "
        "how much did this person's high p-tau, specifically, push their predicted risk up?\n\n"
        "The idea comes from game theory. Treat the features as players in a team, and the prediction as the "
        "prize. A feature's Shapley value is its fair share of the prize, averaged over every possible order "
        "in which the team could have been assembled. We compute the **exact** value here by enumerating all "
        "2⁸ = 256 combinations — the well-known `shap` package approximates this because real models have "
        "hundreds of features, but with eight we do not need to.",
        "C-4-3-md"))
    cells.append(code(
        "from interpret import shapley_values, shapley_importance, baseline_prediction\n\n"
        "explain_columns = ['age', 'ab42_40_ratio', 'ptau181_pg_ml', 'nfl_pg_ml',\n"
        "                   'gfap_pg_ml', 'apoe4_carrier', 'education_years']\n"
        "shap_frame = shapley_values(final_model, X_test.head(60), X_train, features=explain_columns)\n\n"
        "# (a) Globally: which features move predictions the most, across 60 held-out patients?\n"
        "importance = shapley_importance(shap_frame)\n"
        "plots.plot_importance(importance.index, importance.values,\n"
        "                      title='Average influence on predicted AD risk (exact Shapley values)',\n"
        "                      xlabel='mean |contribution| to predicted probability')\n"
        "plt.show()\n\n"
        "# (b) For ONE patient: why did the model say what it said?\n"
        "PATIENT = 0\n"
        "one = shap_frame.iloc[PATIENT].sort_values()\n"
        "plots.plot_importance(one.index, one.values,\n"
        "                      title=f'Patient {X_test.index[PATIENT]}: what pushed this prediction up (blue) and down (red)',\n"
        "                      xlabel='contribution to predicted probability')\n"
        "plt.show()\n\n"
        "base = baseline_prediction(final_model, X_train)\n"
        "print(f'Average predicted risk across the cohort: {base:.3f}')\n"
        "print(f'Sum of this patient\\'s contributions:      {one.sum():+.3f}')\n"
        "print(f'Model\\'s prediction for this patient:      {base + one.sum():.3f}')\n"
        "print(f'(Check — the model really predicts:        {probability[PATIENT]:.3f})')\n"
        "print('\\nThose two numbers agreeing is not a coincidence: Shapley values are defined to add up.')",
        "C-4-3"))
    cells.append(thinking(
        "The Shapley plot says `age` is influential. Is the model detecting Alzheimer's disease, or detecting old age?",
        "Both, unavoidably entangled — and you cannot tell which from this figure alone. Age is the strongest "
        "risk factor for AD, so an age-heavy model will score well while adding nothing a calendar could not. "
        "The test is to remove age and see what survives: if the biomarkers still work, they carry independent "
        "information. **Module D is entirely about this problem** — it is a good choice for your second module.",
        "C-4-3-think"))

    cells.append(md(
        "### 4.4 Who does this model fail?\n\n"
        "An overall score hides the people it was worst for. Split the errors by subgroup and look.",
        "C-4-4-md"))
    cells.append(code(
        "errors = df.loc[X_test.index].copy()\n"
        "errors['correct'] = (predicted == y_test).astype(int)\n"
        "errors['age_band'] = pd.cut(errors['age'], [50, 65, 75, 85, 100],\n"
        "                            labels=['50-65', '65-75', '75-85', '85+'])\n\n"
        "for subgroup in ['sex', 'site', 'age_band', 'diagnosis']:\n"
        "    plots.plot_subgroup_errors(errors, subgroup, 'correct',\n"
        "                               title=f'Proportion correct by {subgroup}')\n"
        "    plt.show()",
        "C-4-4"))
    cells.append(md(
        "**The MCI bar is the one to look at.** People with mild cognitive impairment are counted as 'not AD' "
        "here, but many of them will convert to AD within a few years. The model is being marked wrong for "
        "flagging people who are arguably early cases — and marked right for reassuring people who are about "
        "to get worse. A label is a snapshot; the disease is a process.\n\n"
        "**And the bias question.** This simulated cohort is deliberately narrow: three clinics, one broad "
        "ancestry group, everyone already referred to a memory service. A model trained here has never seen "
        "the people least likely to be referred in the first place — which in most health systems means "
        "poorer, less educated, and minority-ethnic patients. Deploying it would work worst for exactly the "
        "groups already worst served.",
        "C-4-4-read"))

    cells.append(md(
        "### 4.5 Your headline result\n\n"
        "One figure summarising what you built, for your own notes. **There is no shared scoreboard and no "
        "comparison between students** — the interesting differences between modules are qualitative, and we "
        "discuss them together at the end.",
        "C-4-5-md"))
    cells.append(code(
        "summary = pd.Series(final_metrics)\n"
        "plots.plot_score_comparison(list(summary.index), list(summary.values), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * len(summary),\n"
        "                            title='Module C — blood biomarkers, logistic regression, held-out patients',\n"
        "                            ylabel='score')\n"
        "plt.show()\n\n"
        "print('Model:      logistic regression on 8 blood/CSF and demographic features')\n"
        "print(f'Trained on: {len(X_train)} people   Tested on: {len(X_test)} unseen people')\n"
        "print('Excluded:   MMSE (label leakage), site (batch confounder)')\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "C-4-5"))

    cells.append(md(
        "### 4.6 What would have to be true before this touched a patient?\n\n"
        "Honest limitations, in the order a regulator would ask about them:\n\n"
        "1. **The data are simulated.** Nothing here is evidence about real biomarkers. Real p-tau217 assays "
        "do perform roughly this well against clinical diagnosis — but *roughly this well in published "
        "cohorts* is not the same as *this well in your clinic*.\n"
        "2. **One cohort, one time.** The model has never seen a different hospital, a different assay lot, "
        "or a different population. External validation is not a nice-to-have; it is the whole test.\n"
        "3. **The label is imperfect.** Clinical AD diagnosis without autopsy or PET confirmation is wrong "
        "perhaps 10–30% of the time. The model can never be more accurate than its labels.\n"
        "4. **Nobody has shown it changes anything.** A model that predicts well but does not alter treatment, "
        "timing or outcome has no clinical value. That requires a prospective study, not a held-out split.\n"
        "5. **Coverage.** See 4.4. If the training cohort excluded a group, the model's confident answers "
        "about that group are confident guesses.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "Blood tests are cheap, quick and nearly harmless. Lumbar punctures and PET scans are expensive, "
        "unpleasant and rationed. Given the confusion matrix you produced in 4.2 — **would you use this model "
        "to decide who gets referred for a PET scan?** What threshold would you set, and who would you be "
        "willing to miss?",
        "C-4-6"))

    cells.append(go_further(
        "C-4-further",
        "set `DECISION_THRESHOLD` in 4.2 to whatever you would defend in a clinic, and be ready to say why.",
        "in 4.3, change `PATIENT` to find a patient the model got *wrong*, and use their Shapley plot to "
        "explain what misled it. (Hint: `wrong = np.where(predicted != y_test)[0]`.)",
        "the `shap` package draws beeswarm and waterfall plots from these same values. Install it and "
        "compare its `KernelExplainer` output to our exact values — how close does the approximation get?",
    ))

    return cells, solutions


# =============================================================================
# Module A — structural MRI
# =============================================================================

def build_A():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "A", "Structural MRI",
        "Can a brain scan tell us who has dementia?",
        [
            "read the numbers a radiologist's pipeline extracts from a brain scan, and say what each one means",
            "explain why the same person appearing twice in a dataset destroys a test score, and fix it",
            "train a **support vector machine** directly on brain images",
            "train a small **convolutional neural network** on the same images, on your own laptop's CPU",
            "explain why the CNN does not win, and why that is the expected answer at this sample size",
        ],
        "**Real data, simulated pictures.** The table is **OASIS-2**: 373 real MRI sessions from 150 real "
        "older adults, with the volumetric measures a processing pipeline extracted from each scan (`eTIV`, "
        "`nWBV`, `ASF`) and real clinical ratings. Many participants were scanned several times, which is "
        "exactly what makes this module's central lesson possible.\n\n"
        "The **2D slice images** are simulated. Raw OASIS images need a signed data-use agreement, so we "
        "cannot ship them. Instead each visit gets a 64×64 phantom slice whose ventricle size and cortical "
        "ribbon are drawn from *that visit's real measured brain volume*. The pixels are ours; the anatomy "
        "they encode is a real measurement of a real person.",
        "Read section 2's figures without doing the ✏️ turns, then go to 3.3 (the SVM on images) and work forward.",
        warning="Real OASIS measurements; simulated slice images. Section 1.5 explains exactly what that means.",
    ))
    cells.append(setup_cell("A", extra_imports=["import images as image_tools"]))

    # --- Section 1 ---------------------------------------------------------
    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "One row is **one MRI session**, not one person. Hold on to that distinction — it is the whole of "
        "section 2.",
        "A-s1"))

    cells.append(md(
        "### 1.1 Load the table",
        "A-1-1-md"))
    cells.append(code(
        "df = load_data('A')\n"
        "print(f'{df.shape[0]} scanning sessions from {df.subject_id.nunique()} different people.')\n"
        "df.head(6)",
        "A-1-1"))

    cells.append(md(
        "### 1.2 What the columns mean\n\n"
        "A structural MRI is a 3D picture of brain tissue. Nobody feeds the raw picture to a doctor; a "
        "processing pipeline first reduces it to a handful of numbers.\n\n"
        "| Column | What it is |\n|---|---|\n"
        "| `subject_id` | The person. **Appears more than once.** |\n"
        "| `session_id` | One scanning appointment. |\n"
        "| `visit`, `days_since_first_visit` | Which appointment this was, and how long after the first. |\n"
        "| `group` | `Nondemented`, `Demented`, or `Converted` — someone who was fine at first and was not later. |\n"
        "| `age`, `sex` | At the time of this scan. |\n"
        "| `education_years` | Years of schooling — a proxy for **cognitive reserve**. |\n"
        "| `ses` | Socioeconomic status, 1 (highest) to 5 (lowest). Note how often it is missing. |\n"
        "| `mmse` | Mini-Mental State Examination, 0–30. A bedside cognitive test. |\n"
        "| `cdr` | **Clinical Dementia Rating**: 0 = none, 0.5 = very mild, 1 = mild, 2 = moderate. This is the clinical label. |\n"
        "| `etiv_mm3` | *Estimated total intracranial volume* — the size of the skull cavity. A proxy for **head size**, which does not change with disease. It is here so that brain volumes can be compared between a large man and a small woman. |\n"
        "| `nwbv` | ***Normalised whole-brain volume*** — the fraction of the skull cavity still filled with brain tissue. Typically 0.84 in a young adult, falling to below 0.70 with atrophy. **This is the atrophy measure. It is the most important column in the table.** |\n"
        "| `asf` | Atlas scaling factor, the number used to normalise this brain to a template. Essentially 1/eTIV. |",
        "A-1-2-md"))

    cells.append(md(
        "### 1.3 The atrophy signal\n\n"
        "**Predict before you run:** the brain shrinks with normal ageing *and* with dementia. Will the two "
        "groups' `nwbv` distributions separate cleanly, or overlap heavily?",
        "A-1-3-md"))
    cells.append(code(
        "plots.plot_class_balance(df['group'], title='Diagnostic groups across all 373 sessions')\n"
        "plt.show()\n\n"
        "plots.plot_by_group(df, 'nwbv', 'group',\n"
        "                    title='Normalised whole-brain volume — the fraction of skull still filled with brain')\n"
        "plt.show()\n\n"
        "plots.plot_scatter(df['age'], df['nwbv'], colour_by=df['group'],\n"
        "                   xlabel='age (years)', ylabel='normalised whole-brain volume',\n"
        "                   title='Brain volume falls with age in everyone. Dementia shifts the whole line down.',\n"
        "                   legend_title='group')\n"
        "plt.show()",
        "A-1-3"))
    cells.append(thinking(
        "The two clouds in the scatter plot overlap a lot. Does that mean brain volume is useless?",
        "No — it means it is a *risk marker*, not a *test*. A 78-year-old with an nWBV of 0.68 is much more "
        "likely to be demented than one at 0.78, but plenty of individuals sit in the overlap. This is the "
        "normal situation for almost every biomarker in medicine, and it is why we measure AUROC (how well "
        "the model *ranks* people) rather than demanding a clean separation.",
        "A-1-3-think"))

    cells.append(md(
        "### 1.4 ✏️ Your turn — the repeated-visit structure\n\n"
        "Change `SUBJECT` to look at one person's whole scanning history. Try a few. Some people are stable "
        "for years; some visibly decline; the `Converted` group changes diagnosis mid-study.",
        "A-1-4-md"))
    cells.append(code(
        turn(
            "Pick any subject id from the list printed underneath.\n"
            "Try one 'Converted' subject and one 'Nondemented' subject.\n"
            "Ask: could a model tell these two visits apart, or are they the same person twice?",
            "SUBJECT = 'OAS2_0002'",
        ) + "\n\n"
        "person = df[df.subject_id == SUBJECT]\n"
        "display(person[['session_id', 'visit', 'days_since_first_visit', 'age', 'group', 'mmse', 'cdr', 'nwbv']])\n\n"
        "visits_each = df.groupby('subject_id').size()\n"
        "fig, ax = plt.subplots(figsize=(6, 3.4))\n"
        "ax.hist(visits_each, bins=range(1, visits_each.max() + 2), color='#2c6fbb', align='left', rwidth=0.8)\n"
        "ax.set_xlabel('number of scans this person contributed'); ax.set_ylabel('number of people')\n"
        "ax.set_title(f'{len(df)} rows, but only {df.subject_id.nunique()} people')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "converted = df[df.group == 'Converted'].subject_id.unique()\n"
        "print('Some subjects who converted during the study:', ', '.join(converted[:6]))",
        "A-1-4"))

    cells.append(md(
        "### 1.5 The pictures\n\n"
        "Now the images. Each row of the table has a matching 64×64 slice, and we will feed those raw pixels "
        "to a model in section 3.\n\n"
        "**Read this before you look at them.** These slices are *simulated*. We could not ship real OASIS "
        "images — they require a signed agreement — so each one is drawn to match that visit's real measured "
        "`nwbv` and `etiv_mm3`: less brain tissue means bigger dark ventricles in the middle and wider dark "
        "grooves at the surface, which is what atrophy looks like on a real scan. Any model that works on "
        "these is really working on the real measurement, laundered through a picture. That is a fair "
        "demonstration of the *method* and not evidence about real radiology.",
        "A-1-5-md"))
    cells.append(code(
        "extra = load_extra('A')\n"
        "slices, groups_per_slice, nwbv_per_slice = extra['images'], extra['group'], extra['nwbv']\n"
        "print('Image array shape:', slices.shape, '-> 373 scans, each 64 by 64 pixels')\n"
        "print('Pixel values run from', slices.min(), 'to', slices.max(), '(0 = black, 1 = white)\\n')\n\n"
        "# Show the six least atrophied and six most atrophied brains in the study.\n"
        "order = np.argsort(nwbv_per_slice)\n"
        "chosen = np.concatenate([order[-6:], order[:6]])\n"
        "titles = [f'{groups_per_slice[i]}\\nnWBV {nwbv_per_slice[i]:.3f}' for i in chosen]\n"
        "plots.plot_image_grid(slices[chosen], titles=titles, columns=6,\n"
        "                      title='Top row: most brain tissue.  Bottom row: least (the dark centres are enlarged ventricles).')\n"
        "plt.show()",
        "A-1-5"))

    cells.append(go_further(
        "A-1-further",
        "in 1.4, find a subject whose `cdr` increases between visits and read their `nwbv` over the same period.",
        "compute each subject's *change* in nWBV per year (`nwbv` difference divided by `days_since_first_visit`/365) "
        "and plot it by group. Is the rate of shrinkage more informative than the single measurement?",
        "real longitudinal imaging has a nasty trap: the scanner is recalibrated, or the software is upgraded, "
        "between a person's visits, and the apparent 'atrophy' is a software version change. Look up 'longitudinal "
        "registration bias' in FreeSurfer.",
    ))

    # --- Section 2 ---------------------------------------------------------
    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "This module has one flaw so important it deserves the whole section, plus two smaller ones.",
        "A-s2"))

    cells.append(md(
        "### 2.1 Missing values\n\n"
        "`ses` and `mmse` have gaps. Before deciding what to do about them, ask *who* is missing.",
        "A-2-1-md"))
    cells.append(code(
        "plots.plot_missingness(df, title='Missing values across the 373 sessions')\n"
        "plt.show()\n\n"
        "print(df.groupby('group')[['ses', 'mmse', 'cdr']].apply(lambda block: block.isna().mean().round(3)))\n"
        "print('\\n(Values are the fraction missing in each group.)')",
        "A-2-1"))

    cells.append(md(
        "### 2.2 The big one — the same person on both sides of the split\n\n"
        "Machine learning assumes your test set is made of **people the model has never seen**. Here, 150 "
        "people produced 373 scans. If you split the *rows* at random, Mrs Smith's visit 1 lands in training "
        "and her visit 2 lands in testing. The model does not need to learn about dementia; it can recognise "
        "*her*, and her diagnosis rarely changes between visits.\n\n"
        "This is called **subject-level leakage**, and it is probably the single most common fatal flaw in "
        "published medical imaging AI. It is easy to introduce and invisible in the results — unless you go "
        "looking, which we now do.\n\n"
        "The fix is one argument: `split_data(X, y, groups=df['subject_id'])`.",
        "A-2-2-md"))
    cells.append(code(
        "# Keep the two unambiguous groups so the comparison is clean.\n"
        "clean = df[df.group.isin(['Nondemented', 'Demented'])].copy()\n"
        "y_all = (clean.group == 'Demented').astype(int)\n"
        "volumetric = ['age', 'sex', 'education_years', 'ses', 'nwbv', 'etiv_mm3', 'asf']\n"
        "X_all = clean[volumetric]\n\n"
        "results = {}\n"
        "for label, grouping in [('split by ROW\\n(leaky)', None), ('split by SUBJECT\\n(honest)', clean['subject_id'])]:\n"
        "    X_tr, X_te, y_tr, y_te = split_data(X_all, y_all, groups=grouping)\n"
        "    shared = set(clean.loc[X_tr.index, 'subject_id']) & set(clean.loc[X_te.index, 'subject_id'])\n"
        "    model = train_model('random_forest', X_tr, y_tr)\n"
        "    results[label] = evaluate(model, X_te, y_te)['auroc']\n"
        "    print(f'{label.splitlines()[0]:<16s} {len(shared):>3d} people appear in BOTH train and test')\n\n"
        "plots.plot_score_comparison(list(results), list(results.values()),\n"
        "                            colours=['#c0392b', '#2c6fbb'], reference=0.5,\n"
        "                            title='Identical data, identical model. The only difference is how we split.',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()\n"
        "gap = results['split by ROW\\n(leaky)'] - results['split by SUBJECT\\n(honest)']\n"
        "print(f'The leaky split inflates AUROC by {gap:+.3f}. Published as-is, that is a fabricated result.')",
        "A-2-2"))
    cells.append(thinking(
        "Module H (drug discovery) has exactly the same problem with a completely different name. What is it?",
        "**Scaffold leakage.** Chemists make dozens of near-identical analogues of one promising molecule. "
        "Split those at random and the model sees compound 17a in training and 17b in testing — two atoms "
        "different — so it looks brilliant and then fails on a genuinely new scaffold. Same maths, same fix, "
        "same `groups=` argument. If you take H as your second module you will see the identical bar chart "
        "with chemistry on the axis.",
        "A-2-2-think"))

    cells.append(md(
        "### 2.3 ✏️ Your turn — feel the leak\n\n"
        "Turn grouping on and off yourself, and change the model. The leak's size depends on how good the "
        "model is at memorising: flexible models leak more.",
        "A-2-3-md"))
    cells.append(code(
        turn(
            "Set GROUP_BY_SUBJECT to False, run, then set it back to True.\n"
            "Then repeat with MODEL = 'knn' (a model that literally memorises)\n"
            "and MODEL = 'logistic' (a model that cannot memorise much).\n"
            "Which model is helped most by the cheating?",
            "GROUP_BY_SUBJECT = True\n"
            "MODEL = 'random_forest'",
        ) + "\n\n"
        "grouping = clean['subject_id'] if GROUP_BY_SUBJECT else None\n"
        "X_tr, X_te, y_tr, y_te = split_data(X_all, y_all, groups=grouping)\n"
        "metrics = evaluate(train_model(MODEL, X_tr, y_tr), X_te, y_te)\n\n"
        "plots.plot_score_comparison(list(metrics), list(metrics.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb' if GROUP_BY_SUBJECT else '#c0392b'] * 5,\n"
        "                            title=f\"{MODEL}, grouped={GROUP_BY_SUBJECT}\", ylabel='score')\n"
        "plt.show()\n"
        "overlap = len(set(clean.loc[X_tr.index, 'subject_id']) & set(clean.loc[X_te.index, 'subject_id']))\n"
        "print(f'{overlap} people are in both halves. Anything above zero means the score is not what it claims.')",
        "A-2-3"))

    cells.append(md(
        "### 2.4 The other leak — the cognitive test\n\n"
        "`mmse` is a cognitive examination. `cdr` — and therefore `group` — was assigned by a clinician who "
        "had the cognitive picture in front of them. Predicting `group` from `mmse` is close to predicting "
        "the label from the label. Same story as module C, different modality; it is worth seeing how large "
        "the effect is here.",
        "A-2-4-md"))
    cells.append(code(
        "for label, columns in [('imaging + demographics', volumetric),\n"
        "                       ('imaging only', ['nwbv', 'etiv_mm3', 'asf']),\n"
        "                       ('+ MMSE (circular)', volumetric + ['mmse'])]:\n"
        "    X_tr, X_te, y_tr, y_te = split_data(clean[columns], y_all, groups=clean['subject_id'])\n"
        "    score = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n"
        "    results[label] = score\n\n"
        "picked = ['imaging only', 'imaging + demographics', '+ MMSE (circular)']\n"
        "plots.plot_score_comparison(picked, [results[name] for name in picked],\n"
        "                            colours=['#2c6fbb', '#2c6fbb', '#e08214'], reference=0.5,\n"
        "                            title='All subject-grouped. The orange bar is not an imaging result.',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()",
        "A-2-4"))

    cells.append(thinking(
        "Activity cliffs mean near-identical molecules can differ a thousandfold in potency. Which of today's models handles that worst?",
        "`knn` — nearest neighbours — is destroyed by it, because its entire assumption is *\"things that "
        "look alike behave alike\"*, and an activity cliff is a counterexample by definition. Tree-based "
        "models cope a little better, since they can carve out a sharp region of descriptor space, but our "
        "eleven whole-molecule descriptors cannot even *see* the single-atom change that causes the cliff: "
        "two compounds either side of one have almost identical molecular weight, logP and ring count.\n\n"
        "This is why production models use fingerprints or graph networks, which encode *which* atoms sit "
        "where rather than counting them. And it is why chemists remain sceptical of models that report a "
        "good average score: the average is dominated by easy compounds, while the interesting ones live on "
        "the cliffs.",
        "H-2-4-think"))

    cells.append(md(
        "### 2.5 QC verdict\n\n"
        "**Usable, with one non-negotiable rule and two caveats.**\n\n"
        "1. **Always pass `groups=subject_id`.** Everything below does. Without it, every number in this "
        "notebook is fiction.\n"
        "2. `ses` is missing for a substantial minority, and probably not at random — socioeconomic status is "
        "harder to collect from exactly the people whose outcomes differ most. We impute it inside the "
        "pipeline and keep the caveat.\n"
        "3. We exclude `mmse` from the imaging models, because this module asks what an *image* can do.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "A-2-verdict"))

    cells.append(go_further(
        "A-2-further",
        "in 2.3, set `MODEL = 'knn'` with grouping off and then on, and note which model the leak flatters most.",
        "the `Converted` subjects were dropped in 2.2. Add them back, labelled by their *final* diagnosis, and "
        "see what happens. Is that a fair label for their first scan?",
        "read about **immortal time bias** — a related trap where the way you define follow-up guarantees a "
        "result. Module E's take-home covers it.",
    ))

    more_cells, more_solutions = _A_model_and_results()
    cells += more_cells
    solutions.update(more_solutions)
    return cells, solutions


def _A_model_and_results():
    """Sections 3 and 4 of module A: volumetric models, an SVM on images, then a CNN."""
    cells, solutions = [], {}

    cells.append(md(
        "---\n# 3 · Build models\n\n"
        "Three rungs, in this order:\n\n"
        "1. **The numbers a pipeline already extracted** (`nwbv` and friends). Cheap, interpretable, and the "
        "bar everything else has to clear.\n"
        "2. **A support vector machine on the raw image pixels.** No feature extraction at all — 4096 numbers "
        "per brain, straight in.\n"
        "3. **A convolutional neural network on the same pixels.** The method that made medical imaging AI "
        "famous.\n\n"
        "Every rung uses the same subject-grouped split, so the comparison is fair.",
        "A-s3"))
    cells += express_catchup("A", "df = load_data('A')\nextra = load_extra('A')\nslices, groups_per_slice, nwbv_per_slice = extra['images'], extra['group'], extra['nwbv']\n\n# The two unambiguous groups, the target, and the pipeline-extracted measurements.\nclean = df[df.group.isin(['Nondemented', 'Demented'])].copy()\ny_all = (clean.group == 'Demented').astype(int)\nvolumetric = ['age', 'sex', 'education_years', 'ses', 'nwbv', 'etiv_mm3', 'asf']\nX_all = clean[volumetric]\n\nprint(f'{len(clean)} scans from {clean.subject_id.nunique()} people; {y_all.sum()} of them demented.')\nprint('Ready for section 3.')")

    cells.append(md(
        "### 3.1 Rung one — the extracted measurements\n\n"
        "Beat the dumb baseline first.",
        "A-3-1-md"))
    cells.append(code(
        "X_train, X_test, y_train, y_test = split_data(X_all, y_all, groups=clean['subject_id'])\n"
        "train_subjects = clean.loc[X_train.index, 'subject_id']\n"
        "print(f'{len(X_train)} scans from {train_subjects.nunique()} people to train on;')\n"
        "print(f'{len(X_test)} scans from {clean.loc[X_test.index, \"subject_id\"].nunique()} DIFFERENT people to test on.\\n')\n\n"
        "ladder = ['baseline', 'logistic', 'knn', 'random_forest', 'svm']\n"
        "table = compare_models(ladder, X_train, y_train, X_test, y_test)\n"
        "display(table)\n"
        "plots.plot_model_comparison(table, metric='auroc',\n"
        "                            title='Rung 1: models on the pipeline-extracted volumes (AUROC)')\n"
        "plt.show()\n"
        "volumetric_auroc = table.loc['logistic', 'auroc']",
        "A-3-1"))

    cells.append(md(
        "### 3.2 ✏️ Your turn — which measurement carries the signal?\n\n"
        "Strip the feature set down and see what survives. `nwbv` is doing most of the work; find out how much.",
        "A-3-2-md"))
    cells.append(code(
        turn(
            "Comment lines in or out (put a # at the start to remove one).\n"
            "Suggested experiments:\n"
            "  (a) nwbv alone           -> how far does one number get you?\n"
            "  (b) age alone            -> how much is just ageing?\n"
            "  (c) everything except nwbv -> is there anything left without the atrophy measure?",
            "FEATURES = [\n"
            "    'nwbv',              # brain tissue remaining\n"
            "    'age',\n"
            "    'sex',\n"
            "    'education_years',\n"
            "    'ses',\n"
            "    'etiv_mm3',          # head size\n"
            "    'asf',\n"
            "]",
        ) + "\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(clean[FEATURES], y_all, groups=clean['subject_id'])\n"
        "chosen_metrics = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)\n\n"
        "plots.plot_score_comparison(list(chosen_metrics), list(chosen_metrics.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title=f'{len(FEATURES)} feature(s): ' + ', '.join(FEATURES), ylabel='score')\n"
        "plt.show()\n\n"
        "readable = train_model('logistic', X_tr, y_tr)\n"
        "names = readable.named_steps['preprocess'].get_feature_names_out()\n"
        "weights = readable.named_steps['model'].coef_[0]\n"
        "plots.plot_importance([n.split('__')[-1] for n in names], weights,\n"
        "                      title='Logistic regression weights (blue pushes towards \"demented\")',\n"
        "                      xlabel='coefficient (standardised units)')\n"
        "plt.show()",
        "A-3-2"))

    cells.append(md(
        "### 3.3 Rung two — a support vector machine, straight on the pixels\n\n"
        "Now we throw away the extracted numbers and hand the model the picture.\n\n"
        "Each 64×64 slice becomes a row of **4096 numbers**, one per pixel. A **support vector machine (SVM)** "
        "looks for the boundary that separates the two classes with the widest possible empty corridor around "
        "it, and its *kernel* controls the boundary's shape — `'linear'` for a flat plane, `'rbf'` for a "
        "curved one.\n\n"
        "**Predict before you run:** 4096 measurements per brain and only ~270 training brains. Is that more "
        "information than `nwbv` alone, or less?",
        "A-3-3-md"))
    cells.append(code(
        "from sklearn.model_selection import GroupShuffleSplit\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.svm import SVC\n"
        "from sklearn.metrics import roc_auc_score, balanced_accuracy_score\n\n"
        "# Line the images up with the table rows we kept, and split by SUBJECT again.\n"
        "keep = np.isin(extra['session_id'], clean['session_id'].to_numpy())\n"
        "image_X = slices[keep]\n"
        "image_y = (extra['group'][keep] == 'Demented').astype(int)\n"
        "image_subjects = extra['subject_id'][keep]\n\n"
        "splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)\n"
        "train_index, test_index = next(splitter.split(image_X, image_y, image_subjects))\n"
        "print(f'{len(train_index)} training images, {len(test_index)} test images, no shared subjects: '\n"
        "      f'{len(set(image_subjects[train_index]) & set(image_subjects[test_index])) == 0}')\n\n"
        "flat_train = image_tools.flatten(image_X[train_index])\n"
        "flat_test = image_tools.flatten(image_X[test_index])\n"
        "print(f'Each brain is now a row of {flat_train.shape[1]} pixel values.\\n')\n\n"
        "svm_pixels = Pipeline([\n"
        "    ('scale', StandardScaler()),\n"
        "    ('svm', SVC(kernel='rbf', C=1.0, class_weight='balanced', probability=True, random_state=42)),\n"
        "]).fit(flat_train, image_y[train_index])\n\n"
        "svm_probability = svm_pixels.predict_proba(flat_test)[:, 1]\n"
        "svm_auroc = roc_auc_score(image_y[test_index], svm_probability)\n"
        "print(f'SVM on raw pixels — held-out AUROC: {svm_auroc:.3f}')\n\n"
        "plots.plot_roc_pr(image_y[test_index], svm_probability, title='SVM on 4096 raw pixels per brain')\n"
        "plt.show()",
        "A-3-3"))

    cells.append(md(
        "### 3.4 Compressing the images — eigenbrains\n\n"
        "4096 pixels is far more numbers than we have brains, and most of them say the same thing as their "
        "neighbours. **Principal component analysis (PCA)** finds the handful of *patterns of variation* that "
        "account for most of the difference between these images, and describes each brain as a recipe of "
        "those patterns. In face recognition these patterns are famously called *eigenfaces*; on brain images, "
        "**eigenbrains**, and they are worth looking at in their own right.\n\n"
        "**Predict before you run:** compressing 4096 numbers down to 40 throws information away. Does that "
        "help the SVM (less noise to overfit) or hurt it (less signal to use)? Both are plausible. Find out — "
        "and then look at 3.9 before you conclude anything from a single split.",
        "A-3-4-md"))
    cells.append(code(
        "from sklearn.decomposition import PCA\n\n"
        "svm_pca = Pipeline([\n"
        "    ('scale', StandardScaler()),\n"
        "    ('pca', PCA(n_components=40, random_state=42)),\n"
        "    ('svm', SVC(kernel='rbf', C=1.0, class_weight='balanced', probability=True, random_state=42)),\n"
        "]).fit(flat_train, image_y[train_index])\n\n"
        "pca_probability = svm_pca.predict_proba(flat_test)[:, 1]\n"
        "pca_auroc = roc_auc_score(image_y[test_index], pca_probability)\n"
        "explained = svm_pca.named_steps['pca'].explained_variance_ratio_.sum()\n"
        "print(f'40 components keep {explained:.0%} of the variation in the images.')\n"
        "print(f'SVM on 40 eigenbrains — held-out AUROC: {pca_auroc:.3f}  (raw pixels was {svm_auroc:.3f})\\n')\n\n"
        "# What do the patterns look like?\n"
        "components = svm_pca.named_steps['pca'].components_[:8].reshape(-1, 64, 64)\n"
        "plots.plot_image_grid(components, titles=[f'eigenbrain {i + 1}' for i in range(8)], columns=4,\n"
        "                      title='The main patterns of variation across these brains', cmap='RdBu_r')\n"
        "plt.show()\n\n"
        "# Where does each brain sit in the first two dimensions?\n"
        "coordinates = svm_pca.named_steps['pca'].transform(\n"
        "    svm_pca.named_steps['scale'].transform(flat_test))\n"
        "plots.plot_scatter(coordinates[:, 0], coordinates[:, 1],\n"
        "                   colour_by=np.where(image_y[test_index] == 1, 'Demented', 'Nondemented'),\n"
        "                   xlabel='eigenbrain 1', ylabel='eigenbrain 2',\n"
        "                   title='Held-out brains in eigenbrain space', legend_title='true group')\n"
        "plt.show()",
        "A-3-4"))

    cells.append(md(
        "### 3.5 ✏️ Your turn — the SVM's three dials\n\n"
        "An SVM has few settings, and each one does something you can describe in a sentence:\n\n"
        "- **`KERNEL`** — the shape of the boundary. `'linear'` is a flat cut; `'rbf'` bends around clusters.\n"
        "- **`C`** — how badly the SVM wants to classify every training brain correctly. Large `C` = "
        "\"get them all right\" = memorising. Small `C` = \"keep the boundary simple\".\n"
        "- **`N_COMPONENTS`** — how many eigenbrains to keep. Fewer means a blunter but steadier description.\n\n"
        "The figure sweeps `C` for whatever kernel and component count you set, so you can see the whole "
        "overfitting curve rather than one number.",
        "A-3-5-md"))
    cells.append(code(
        turn(
            "Change these three, then re-run.\n"
            "Suggested experiments:\n"
            "  (a) KERNEL='linear' vs 'rbf'   -> does a curved boundary help?\n"
            "  (b) N_COMPONENTS = 5, 40, 200  -> how much detail is useful?\n"
            "  (c) watch the orange (training) line hit 1.0 as C grows: that is memorising.",
            "KERNEL = 'rbf'          # 'linear' or 'rbf'\n"
            "N_COMPONENTS = 40       # try 5, 40, 200\n"
            "C_VALUES = [0.01, 0.1, 1.0, 10.0, 100.0]",
        ) + "\n\n"
        "train_curve, test_curve = [], []\n"
        "for c_value in C_VALUES:\n"
        "    pipeline = Pipeline([\n"
        "        ('scale', StandardScaler()),\n"
        "        ('pca', PCA(n_components=N_COMPONENTS, random_state=42)),\n"
        "        ('svm', SVC(kernel=KERNEL, C=c_value, class_weight='balanced', random_state=42)),\n"
        "    ]).fit(flat_train, image_y[train_index])\n"
        "    train_curve.append(balanced_accuracy_score(image_y[train_index], pipeline.predict(flat_train)))\n"
        "    test_curve.append(balanced_accuracy_score(image_y[test_index], pipeline.predict(flat_test)))\n\n"
        "plots.plot_parameter_sweep(C_VALUES, train_curve, test_curve, 'C',\n"
        "                           title=f'SVM ({KERNEL} kernel, {N_COMPONENTS} eigenbrains) on brain images')\n"
        "plt.show()\n"
        "print(f'Best held-out C: {C_VALUES[int(np.argmax(test_curve))]}')",
        "A-3-5"))

    cells.append(md(
        "### 3.6 Rung three — a convolutional neural network\n\n"
        "An SVM on pixels has no idea that pixel 200 sits next to pixel 201. A **convolutional neural network "
        "(CNN)** does. It slides small filters across the image looking for local patterns — an edge, a dark "
        "blob — then slides more filters across *those* results, building up from edges to shapes to \"large "
        "ventricle\". That built-in assumption, that nearby pixels belong together, is why CNNs took over "
        "medical imaging.\n\n"
        "Ours is deliberately tiny: three convolution blocks and one dense layer, about **12000 parameters** — "
        "and we have roughly **270 training brains**. Notice that ratio. A model with forty times more "
        "parameters than examples can memorise its training set completely, which is why we use dropout, "
        "class weighting, and only a dozen epochs.\n\n"
        "⏱ **This cell takes about 20–40 seconds on a laptop CPU.** If PyTorch is not installed it "
        "automatically trains a small dense network instead, and says so.",
        "A-3-6-md"))
    cells.append(code(
        "from images import SmallCNN\n\n"
        "cnn = SmallCNN(epochs=12, learning_rate=3e-3, channels=8, dropout=0.3, verbose=True)\n"
        "cnn.fit(image_X[train_index], image_y[train_index],\n"
        "        validation=(image_X[test_index], image_y[test_index]))\n\n"
        "print(f'\\nBackend: {cnn.backend}')\n"
        "print(f'Trainable parameters: {cnn.parameter_count():,}')\n"
        "print(f'Training brains:      {len(train_index)}')\n"
        "print(f'Parameters per brain: {cnn.parameter_count() / len(train_index):.0f}')\n\n"
        "cnn_probability = cnn.predict_proba(image_X[test_index])[:, 1]\n"
        "cnn_auroc = roc_auc_score(image_y[test_index], cnn_probability)\n"
        "print(f'\\nCNN — held-out AUROC: {cnn_auroc:.3f}')\n\n"
        "# The training curve is the diagnostic that matters.\n"
        "fig, ax = plt.subplots(figsize=(7, 4))\n"
        "ax.plot(cnn.history['epoch'], cnn.history['train_loss'], 'o-', color='#e08214', label='training loss')\n"
        "if cnn.history['validation_loss']:\n"
        "    ax.plot(cnn.history['epoch'], cnn.history['validation_loss'], 'o-', color='#2c6fbb',\n"
        "            label='held-out loss')\n"
        "ax.set_xlabel('epoch (one pass through the training brains)'); ax.set_ylabel('loss (lower is better)')\n"
        "ax.set_title('If the blue line turns upward while orange keeps falling, it is memorising')\n"
        "ax.legend(fontsize=9)\n"
        "plt.tight_layout(); plt.show()",
        "A-3-6"))

    cells.append(md(
        "### 3.7 ✏️ Your turn — the CNN's dials\n\n"
        "> **How practitioners actually approach this.** Beat the simple baseline before adding a single "
        "layer. Count parameters against sample size — with a few hundred biomedical images, *smaller is "
        "usually better*. Use dropout and early stopping by default. And distinguish two very different "
        "failures: if training loss falls but held-out loss rises, the model is **overfitting** (shrink it, "
        "regularise it, get more data); if *neither* falls, the model or the learning rate is **wrong** "
        "(different architecture, different rate).\n\n"
        "⏱ Each run of this cell takes roughly as long as 3.6.",
        "A-3-7-md"))
    cells.append(code(
        turn(
            "Change one at a time and re-run. Suggested experiments:\n"
            "  (a) EPOCHS = 40      -> does held-out loss start rising? that is overfitting\n"
            "  (b) CHANNELS = 2     -> a much smaller network. does it get worse, or better?\n"
            "  (c) DROPOUT = 0.0    -> remove the regulariser and watch the curves separate\n"
            "  (d) LEARNING_RATE = 0.05 -> too big; the loss bounces or flatlines",
            "EPOCHS = 12\n"
            "CHANNELS = 8            # filters in the first convolution block\n"
            "DROPOUT = 0.3           # fraction of connections randomly ignored each step\n"
            "LEARNING_RATE = 0.003",
        ) + "\n\n"
        "tuned = SmallCNN(epochs=EPOCHS, learning_rate=LEARNING_RATE, channels=CHANNELS,\n"
        "                 dropout=DROPOUT, verbose=False)\n"
        "tuned.fit(image_X[train_index], image_y[train_index],\n"
        "          validation=(image_X[test_index], image_y[test_index]))\n\n"
        "tuned_probability = tuned.predict_proba(image_X[test_index])[:, 1]\n"
        "print(f'Parameters: {tuned.parameter_count():,}   '\n"
        "      f'held-out AUROC: {roc_auc_score(image_y[test_index], tuned_probability):.3f}')\n\n"
        "fig, ax = plt.subplots(figsize=(7, 4))\n"
        "ax.plot(tuned.history['epoch'], tuned.history['train_loss'], 'o-', color='#e08214', label='training loss')\n"
        "if tuned.history['validation_loss']:\n"
        "    ax.plot(tuned.history['epoch'], tuned.history['validation_loss'], 'o-', color='#2c6fbb', label='held-out loss')\n"
        "    best_epoch = int(np.argmin(tuned.history['validation_loss'])) + 1\n"
        "    ax.axvline(best_epoch, color='#8a8a8a', linestyle=':')\n"
        "    ax.annotate(f'early stopping\\nwould stop here (epoch {best_epoch})', (best_epoch, ax.get_ylim()[1] * 0.9),\n"
        "                fontsize=8, color='#8a8a8a', textcoords='offset points', xytext=(6, -10))\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('loss')\n"
        "ax.set_title(f'{CHANNELS} channels, dropout {DROPOUT}, lr {LEARNING_RATE}')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()",
        "A-3-7"))

    cells.append(md(
        "### 3.8 🔵 Your turn to write code — data augmentation\n\n"
        "With 270 training brains, the standard trick is to manufacture more by transforming the ones you "
        "have. But **which transformations are anatomically legitimate?**\n\n"
        "- Mirroring left↔right is *arguable*: the hemispheres are roughly symmetric, though not identically "
        "affected in every dementia.\n"
        "- Flipping top↔bottom is *nonsense*: it would put the cerebellum above the cortex. A model that "
        "learns to cope with upside-down brains has wasted its capacity on an impossible case.\n\n"
        "`image_tools.augment_flips` does the legitimate one. Use it.",
        "A-3-8-md"))
    cells.append(code(
        "# TODO (🔵): augment the TRAINING images only, then retrain the CNN and compare.\n"
        "#   1. call image_tools.augment_flips(...) on image_X[train_index] and image_y[train_index]\n"
        "#   2. fit a new SmallCNN on the augmented data (validation stays the untouched test set)\n"
        "#   3. print both AUROCs\n"
        "# Why 'training only'? Augmenting the test set would mean scoring the model on brains\n"
        "# it has effectively already seen — the same leakage lesson as section 2, in a new costume.\n\n"
        "augmented_images = None   # replace me\n"
        "augmented_labels = None   # replace me\n\n"
        "if augmented_images is not None:\n"
        "    augmented_cnn = SmallCNN(epochs=12, verbose=False).fit(\n"
        "        augmented_images, augmented_labels,\n"
        "        validation=(image_X[test_index], image_y[test_index]))\n"
        "    augmented_auroc = roc_auc_score(\n"
        "        image_y[test_index], augmented_cnn.predict_proba(image_X[test_index])[:, 1])\n"
        "    plots.plot_score_comparison(['original', 'left-right augmented'], [cnn_auroc, augmented_auroc],\n"
        "                                reference=0.5, title='Does doubling the training set help?', ylabel='AUROC')\n"
        "    plt.show()\n"
        "else:\n"
        "    print('Fill in the TODO above. The solutions notebook has a worked version.')",
        "A-3-8"))
    solutions["A-3-8"] = (
        "# ✅ Worked solution.\n"
        "augmented_images, augmented_labels = image_tools.augment_flips(\n"
        "    image_X[train_index], image_y[train_index])\n"
        "print(f'{len(train_index)} training brains became {len(augmented_images)}.')\n\n"
        "augmented_cnn = SmallCNN(epochs=12, verbose=False).fit(\n"
        "    augmented_images, augmented_labels,\n"
        "    validation=(image_X[test_index], image_y[test_index]))\n"
        "augmented_auroc = roc_auc_score(\n"
        "    image_y[test_index], augmented_cnn.predict_proba(image_X[test_index])[:, 1])\n\n"
        "plots.plot_score_comparison(['original', 'left-right augmented'], [cnn_auroc, augmented_auroc],\n"
        "                            reference=0.5, title='Does doubling the training set help?', ylabel='AUROC')\n"
        "plt.show()\n\n"
        "# Why this often helps only a little here: a left-right mirror of a roughly symmetric phantom\n"
        "# is nearly the same picture, so it adds little genuinely new information. Augmentation buys\n"
        "# the most when the transformation reflects a variation the model will really meet — different\n"
        "# head positioning, different scanner intensity scaling, slightly different slice level. Those\n"
        "# are the augmentations a neuroimager would reach for, and all of them are defensible in a way\n"
        "# that a vertical flip is not."
    )

    cells.append(md(
        "### 3.9 All four approaches — with honest error bars\n\n"
        "You now have four held-out AUROCs from **one** split of 34 test people. Before comparing them, ask "
        "how much a single split can be trusted at that sample size.\n\n"
        "So we repeat the whole thing across several different subject-grouped splits and plot the spread. "
        "This is the most important figure in the module, and it usually surprises people.\n\n"
        "⏱ **This cell takes 1–2 minutes** — it retrains everything several times. Start it and read the "
        "text below while it runs.",
        "A-3-9-md"))
    cells.append(code(
        "N_REPEATS = 5   # different random subject-grouped splits\n\n"
        "collected = {'extracted volumes (logistic)': [], 'raw pixels (SVM)': [],\n"
        "             'eigenbrains (PCA + SVM)': [], 'raw pixels (CNN)': []}\n\n"
        "for seed in range(N_REPEATS):\n"
        "    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)\n"
        "    tr, te = next(splitter.split(image_X, image_y, image_subjects))\n"
        "    flat_tr, flat_te = image_tools.flatten(image_X[tr]), image_tools.flatten(image_X[te])\n\n"
        "    # rung 1: the pipeline-extracted volumes, on the SAME sessions\n"
        "    sessions = extra['session_id'][keep]\n"
        "    table_train = clean.set_index('session_id').loc[sessions[tr]]\n"
        "    table_test = clean.set_index('session_id').loc[sessions[te]]\n"
        "    volumes = train_model('logistic', table_train[volumetric], pd.Series(image_y[tr], index=table_train.index))\n"
        "    collected['extracted volumes (logistic)'].append(\n"
        "        roc_auc_score(image_y[te], volumes.predict_proba(table_test[volumetric])[:, 1]))\n\n"
        "    # rung 2a: SVM on raw pixels\n"
        "    raw = Pipeline([('scale', StandardScaler()),\n"
        "                    ('svm', SVC(kernel='rbf', C=1.0, class_weight='balanced', probability=True,\n"
        "                                random_state=42))]).fit(flat_tr, image_y[tr])\n"
        "    collected['raw pixels (SVM)'].append(roc_auc_score(image_y[te], raw.predict_proba(flat_te)[:, 1]))\n\n"
        "    # rung 2b: SVM on eigenbrains\n"
        "    compressed = Pipeline([('scale', StandardScaler()),\n"
        "                           ('pca', PCA(n_components=40, random_state=42)),\n"
        "                           ('svm', SVC(kernel='rbf', C=1.0, class_weight='balanced', probability=True,\n"
        "                                       random_state=42))]).fit(flat_tr, image_y[tr])\n"
        "    collected['eigenbrains (PCA + SVM)'].append(\n"
        "        roc_auc_score(image_y[te], compressed.predict_proba(flat_te)[:, 1]))\n\n"
        "    # rung 3: the CNN\n"
        "    network = SmallCNN(epochs=12, verbose=False, seed=seed).fit(image_X[tr], image_y[tr])\n"
        "    collected['raw pixels (CNN)'].append(roc_auc_score(image_y[te], network.predict_proba(image_X[te])[:, 1]))\n"
        "    print(f'  split {seed + 1}/{N_REPEATS} done')\n\n"
        "fig, ax = plt.subplots(figsize=(8, 4.2))\n"
        "for position, (name, scores) in enumerate(collected.items()):\n"
        "    ax.scatter(scores, [position] * len(scores), s=55, color='#2c6fbb', zorder=3, alpha=0.8)\n"
        "    ax.plot([np.mean(scores)] * 2, [position - 0.22, position + 0.22], color='#e08214', linewidth=3)\n"
        "    ax.annotate(f'{np.mean(scores):.3f} ± {np.std(scores):.3f}', (max(scores), position),\n"
        "                textcoords='offset points', xytext=(12, -4), fontsize=9)\n"
        "ax.axvline(0.5, color='#8a8a8a', linestyle='--')\n"
        "ax.set_yticks(range(len(collected)), list(collected), fontsize=10)\n"
        "ax.set_xlim(0.35, 1.05)\n"
        "ax.set_xlabel('held-out AUROC (each dot is one subject-grouped split)')\n"
        "ax.set_title(f'Four approaches, {N_REPEATS} splits each. Do the clouds actually separate?')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "for name, scores in collected.items():\n"
        "    print(f'  {name:<32s} {np.mean(scores):.3f} ± {np.std(scores):.3f}   '\n"
        "          f'(worst {min(scores):.3f}, best {max(scores):.3f})')",
        "A-3-9"))
    cells.append(thinking(
        "Look at the spread. Can you honestly say the CNN — the most sophisticated method here — beats a single number called `nwbv`?",
        "Almost certainly not, and that is the most useful thing in this module. With 34 held-out people, one "
        "split's AUROC bounces around by 0.1 or more, which is larger than any gap between the four methods. "
        "**A difference smaller than the spread is not a difference.**\n\n"
        "Three reasons the fancy method does not pull ahead here:\n\n"
        "1. **Sample size.** Deep learning's advantage appears with tens of thousands of examples. With 250 "
        "brains, a 12000-parameter network spends most of its capacity memorising.\n"
        "2. **The pipeline already did the hard part.** `nwbv` is the output of decades of neuroimaging "
        "research into how to summarise a brain. Beating a great hand-crafted feature from scratch is a high bar.\n"
        "3. **Our slices are simple.** They were drawn from `nwbv`, so there is genuinely no extra information "
        "in the pixels to find. On real scans there *is* more — regional atrophy patterns that distinguish "
        "Alzheimer's from frontotemporal dementia, for instance — and that is where CNNs earn their keep.\n\n"
        "The transferable lesson: **\"we used deep learning\" is not a result**, and neither is a single "
        "held-out number. The result is whether it beat the simple thing, repeatedly, on an honest split.",
        "A-3-9-think"))

    cells.append(go_further(
        "A-3-further",
        "in 3.7, set `EPOCHS = 40` and find the epoch where held-out loss stops improving. That is where early stopping would have stopped.",
        "complete the augmentation TODO in 3.8, then try adding small random shifts (`np.roll`) as a second augmentation.",
        "swap the CNN for a **frozen pretrained backbone**: load a network trained on natural images, use it "
        "as a fixed feature extractor, and fit a logistic regression on its output. This is what people "
        "actually do when they have a few hundred medical images.",
    ))

    # --- Section 4 ---------------------------------------------------------
    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "One imaging model gets the full treatment. Rather than pick a favourite in advance, the next cell "
        "takes whichever of the three image approaches scored best on *this* split — and section 3.9 has "
        "already warned you how much that choice depends on the split.",
        "A-s4"))

    cells.append(md("### 4.1 The standard views", "A-4-1-md"))
    cells.append(code(
        "candidates = {'SVM on raw pixels': (svm_probability, svm_auroc),\n"
        "              'SVM on eigenbrains': (pca_probability, pca_auroc),\n"
        "              'small CNN': (cnn_probability, cnn_auroc)}\n"
        "headline_name = max(candidates, key=lambda name: candidates[name][1])\n"
        "headline_probability, headline_auroc = candidates[headline_name]\n"
        "print(f'Best image model on this split: {headline_name} (AUROC {headline_auroc:.3f}).')\n"
        "print('Section 3.9 showed how much that ranking moves between splits — keep it in mind.\\n')\n\n"
        "y_true = image_y[test_index]\n"
        "predicted = (headline_probability >= 0.5).astype(int)\n\n"
        "plots.plot_confusion(y_true, predicted, labels=('nondemented', 'demented'),\n"
        "                     title=f'Held-out brains: {headline_name}')\n"
        "plt.show()\n\n"
        "plots.plot_roc_pr(y_true, headline_probability, title=f'{headline_name}, held-out subjects')\n"
        "plt.show()\n\n"
        "plots.plot_calibration(y_true, headline_probability)\n"
        "plt.show()",
        "A-4-1"))
    cells.append(md(
        "**In this setting a false negative is a person told their scan looks fine when it does not.** They "
        "leave without a referral, without a conversation about what is happening, and without the chance to "
        "plan while they still can. A false positive is a healthy person put through months of anxiety and a "
        "battery of further tests. Whether you would rather make more of one or the other is a clinical and "
        "ethical judgement, and it is made by choosing the threshold — not by the algorithm.",
        "A-4-1-read"))

    cells.append(md(
        "### 4.2 ✏️ Your turn — look at the brains it got wrong\n\n"
        "This is the payoff of working with images: you can *look* at the failures.",
        "A-4-2-md"))
    cells.append(code(
        turn(
            "Try 'wrong', then 'right', then 'uncertain'.\n"
            "Ask yourself: do the mistakes look different from the successes,\n"
            "or does the model just fail on brains that genuinely look borderline?",
            "SHOW = 'wrong'          # 'wrong', 'right' or 'uncertain'\n"
            "DECISION_THRESHOLD = 0.5",
        ) + "\n\n"
        "at_threshold = (headline_probability >= DECISION_THRESHOLD).astype(int)\n"
        "if SHOW == 'wrong':\n"
        "    which = np.where(at_threshold != y_true)[0]\n"
        "elif SHOW == 'right':\n"
        "    which = np.where(at_threshold == y_true)[0]\n"
        "else:\n"
        "    which = np.argsort(np.abs(headline_probability - 0.5))\n"
        "which = which[:12]\n\n"
        "names = ['nondemented', 'demented']\n"
        "captions = [f'true: {names[y_true[i]]}\\nsaid: {headline_probability[i]:.2f}' for i in which]\n"
        "plots.plot_image_grid(image_X[test_index][which], titles=captions, columns=6,\n"
        "                      title=f'Held-out brains the model got {SHOW} (threshold {DECISION_THRESHOLD})')\n"
        "plt.show()\n\n"
        "plots.plot_threshold_sweep(y_true, headline_probability, chosen=DECISION_THRESHOLD)\n"
        "plt.show()\n"
        "print(f'{len(np.where(at_threshold != y_true)[0])} of {len(y_true)} held-out scans misclassified '\n"
        "      f'at threshold {DECISION_THRESHOLD}.')",
        "A-4-2"))

    cells.append(md(
        "### 4.3 Which brains does it get wrong — and who are they?\n\n"
        "Errors are never evenly spread. Break them down by age and sex.",
        "A-4-3-md"))
    cells.append(code(
        "error_table = pd.DataFrame({\n"
        "    'correct': (predicted == y_true).astype(int),\n"
        "    'age': extra['age'][keep][test_index],\n"
        "    'sex': extra['sex'][keep][test_index],\n"
        "    'nwbv': extra['nwbv'][keep][test_index],\n"
        "})\n"
        "error_table['age_band'] = pd.cut(error_table['age'], [55, 70, 78, 85, 100],\n"
        "                                 labels=['<70', '70-78', '78-85', '85+'])\n\n"
        "for subgroup in ['sex', 'age_band']:\n"
        "    plots.plot_subgroup_errors(error_table, subgroup, 'correct',\n"
        "                               title=f'Proportion of held-out scans classified correctly, by {subgroup}')\n"
        "    plt.show()\n\n"
        "plots.plot_scatter(error_table['nwbv'], headline_probability, colour_by=np.where(y_true == 1, 'demented', 'nondemented'),\n"
        "                   xlabel='normalised whole-brain volume (the real measurement)',\n"
        "                   ylabel='probability of dementia the model assigned',\n"
        "                   title='The model reading the picture vs the number the picture was drawn from',\n"
        "                   legend_title='true group')\n"
        "plt.show()",
        "A-4-3"))

    cells.append(md(
        "### 4.4 Your headline result\n\n"
        "For your own notes. **No leaderboard, no comparison with anyone else's module** — the point of the "
        "wrap-up session is that these numbers are not comparable across modalities anyway.",
        "A-4-4-md"))
    cells.append(code(
        "from sklearn.metrics import balanced_accuracy_score, average_precision_score\n"
        "from sklearn.metrics import confusion_matrix as sk_confusion\n\n"
        "tn, fp, fn, tp = sk_confusion(y_true, predicted, labels=[0, 1]).ravel()\n"
        "headline = {\n"
        "    'balanced_accuracy': balanced_accuracy_score(y_true, predicted),\n"
        "    'auroc': headline_auroc,\n"
        "    'auprc': average_precision_score(y_true, headline_probability),\n"
        "    'sensitivity': tp / max(tp + fn, 1),\n"
        "    'specificity': tn / max(tn + fp, 1),\n"
        "}\n"
        "plots.plot_score_comparison(list(headline), list(headline.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title=f'Module A — {headline_name}, subject-grouped held-out scans',\n"
        "                            ylabel='score')\n"
        "plt.show()\n"
        "print(f'Trained on {len(train_index)} scans from {len(set(image_subjects[train_index]))} people.')\n"
        "print(f'Tested on {len(test_index)} scans from {len(set(image_subjects[test_index]))} DIFFERENT people.')\n"
        "for name, value in headline.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "A-4-4"))

    cells.append(md(
        "### 4.5 What would have to be true before this touched a patient?\n\n"
        "1. **Real images.** Our slices encode one summary number. A real scan carries regional detail that "
        "distinguishes Alzheimer's from vascular dementia, from frontotemporal dementia, from normal pressure "
        "hydrocephalus — the differential diagnosis that actually matters in a memory clinic.\n"
        "2. **More than one scanner.** A CNN will happily learn \"this hospital's scanner\" instead of "
        "\"this patient's brain\". Multi-site validation is mandatory.\n"
        "3. **The label is a clinical judgement.** CDR is assigned by a person, from an interview. Two "
        "clinicians disagree more often than you would like. No model beats its labels.\n"
        "4. **150 people is a pilot, not evidence.**\n"
        "5. **Coverage.** OASIS-2 is a single American city's volunteers, mostly white, mostly educated, all "
        "willing to be scanned repeatedly. Brain volume norms genuinely differ by ancestry and by head size, "
        "and a model tuned on this cohort will be least reliable for the people least represented in it.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "MRI is expensive, requires a scanner and a radiographer, and takes half an hour. A blood test (module "
        "C) costs a few euros. Given what you have seen — **where in the diagnostic pathway does imaging "
        "belong?** Screening everybody, or confirming a suspicion someone else raised?",
        "A-4-5"))

    cells.append(go_further(
        "A-4-further",
        "in 4.2 set `DECISION_THRESHOLD = 0.3` and look at how the misclassified brains change.",
        "retrain the eigenbrain SVM using only subjects' **first** visits, so every person contributes exactly "
        "one row. Does the honest score change? What did you give up?",
        "the real version of this module uses the differential-diagnosis framing: not \"dementia yes/no\" but "
        "\"which dementia\". Look up how AD, FTD and DLB differ in their atrophy patterns, and what that means "
        "for a model that only sees one slice.",
    ))

    return cells, solutions


# =============================================================================
# Module D — confounding
# =============================================================================

def build_D():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "D", "Confounding",
        "Is the model learning the disease, or learning who was recruited?",
        [
            "explain what a confounder is, and recognise one in a real dataset",
            "show that a model with a good score can be learning something you did not intend",
            "use stratification, adjustment and matching to take a confounder apart",
            "demonstrate **Simpson's paradox** on real data — a trend that reverses when you split the groups",
            "explain why 'the model is accurate' and 'the model is useful' are different claims",
        ],
        "**Real data, all of it.** This is **OASIS-1**: 416 real people scanned once each, with age, sex, "
        "education, socioeconomic status, a cognitive score, a clinical dementia rating, and the volumetric "
        "measures from their MRI. It is ideal for this module because of a design choice the OASIS team made: "
        "the cohort deliberately spans **ages 18 to 96**, and everybody under about 60 is by construction "
        "healthy. Age is therefore entangled with diagnosis in the most extreme way possible — and that is "
        "true, to a lesser degree, of nearly every dementia cohort ever assembled.",
        "Run sections 1 and 2 quickly and spend your time in section 3 — this module's whole point lives there.",
    ))
    cells.append(setup_cell("D"))

    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "One row is one person, scanned once.",
        "D-s1"))
    cells.append(md(
        "### 1.1 The table\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| `age` | 18 to 96. Look at that range — it is the whole module. |\n"
        "| `sex`, `handedness` | |\n"
        "| `education_code` | Coded 1–5, higher = more education. A proxy for **cognitive reserve**. |\n"
        "| `ses` | Socioeconomic status, 1 (highest) to 5 (lowest). Frequently missing. |\n"
        "| `mmse` | Mini-Mental State Examination, 0–30. Missing for the younger participants, who were not tested. |\n"
        "| `cdr` | Clinical Dementia Rating: 0 = none, 0.5 = very mild, 1 = mild, 2 = moderate. Missing for the young. |\n"
        "| `etiv_mm3` | Skull cavity volume — head size, which does not change with disease. |\n"
        "| `nwbv` | Normalised whole-brain volume: the fraction still filled with brain. **The atrophy measure.** |\n"
        "| `asf` | Atlas scaling factor, essentially 1/eTIV. |\n"
        "| `impaired` | Our label: `cdr > 0`. Missing wherever `cdr` is. |",
        "D-1-1-md"))
    cells.append(code(
        "df = load_data('D')\n"
        "print(f'{len(df)} people, aged {df.age.min():.0f} to {df.age.max():.0f}.')\n"
        "print(f'{df.impaired.notna().sum()} of them have a clinical dementia rating; the rest were never assessed.\\n')\n"
        "df.head()",
        "D-1-1"))

    cells.append(md(
        "### 1.2 The shape of the problem\n\n"
        "**Predict before you run:** in this cohort, how much do the ages of the impaired and unimpaired "
        "groups overlap?",
        "D-1-2-md"))
    cells.append(code(
        "labelled = df.dropna(subset=['impaired']).copy()\n"
        "labelled['status'] = np.where(labelled['impaired'] == 1, 'impaired', 'unimpaired')\n\n"
        "fig, ax = plt.subplots(figsize=(7.5, 3.6))\n"
        "ax.hist([df.loc[df.impaired.isna(), 'age'],\n"
        "         labelled.loc[labelled.impaired == 0, 'age'],\n"
        "         labelled.loc[labelled.impaired == 1, 'age']],\n"
        "        bins=20, stacked=True, color=['#cccccc', '#2c6fbb', '#e08214'],\n"
        "        label=['never assessed (young)', 'unimpaired', 'impaired'])\n"
        "ax.set_xlabel('age (years)'); ax.set_ylabel('number of people')\n"
        "ax.set_title('The cohort by age. Nobody under ~60 is in the orange group — by design.')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n\n"
        "print(labelled.groupby('status')[['age', 'nwbv', 'education_code', 'mmse']].mean().round(3))",
        "D-1-2"))

    cells.append(go_further(
        "D-1-further",
        "read the mean ages of the two groups above and predict what a model given only `age` would score.",
        "plot `nwbv` against `age` for the unimpaired group only, and fit a straight line through it. That "
        "slope is *normal ageing* — everything a model attributes to disease should be measured against it.",
        "look up how 'brain age' models work: they predict chronological age from a scan, and the *residual* "
        "(brain older than it should be) becomes the disease marker. It is confounder-adjustment turned into a method.",
    ))

    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "Two structural problems, both of which are about *who is in the table*, not about *what the numbers "
        "say*.",
        "D-s2"))
    cells.append(md(
        "### 2.1 Missingness that is structural, not accidental\n\n"
        "`cdr` and `mmse` are missing for a large block of participants — not at random, but because the "
        "young ones were never given a dementia assessment. `ses` is missing for a different reason again.\n\n"
        "Dropping the rows without a `cdr` is the right call here, but notice what it does: it removes the "
        "entire young half of the cohort, which is exactly the half that would have shown you what normal "
        "looks like.",
        "D-2-1-md"))
    cells.append(code(
        "plots.plot_missingness(df, title='Missing values across all 416 participants')\n"
        "plt.show()\n\n"
        "by_age = df.assign(no_cdr=df['cdr'].isna(),\n"
        "                   band=pd.cut(df['age'], [17, 40, 60, 75, 100], labels=['18-40', '40-60', '60-75', '75+']))\n"
        "rates = by_age.groupby('band', observed=True)['no_cdr'].mean() * 100\n"
        "plots.plot_score_comparison(rates.index.astype(str).tolist(), rates.tolist(),\n"
        "                            colours=['#e08214'] * len(rates),\n"
        "                            title='Percentage never given a dementia rating, by age band',\n"
        "                            ylabel='percent')\n"
        "plt.show()",
        "D-2-1"))

    cells.append(md(
        "### 2.2 ✏️ Your turn — the age–diagnosis entanglement\n\n"
        "Restrict the cohort to a narrow age window and watch what happens to the apparent effect of brain "
        "volume. Inside a narrow window, age can no longer explain anything — whatever survives is real.",
        "D-2-2-md"))
    cells.append(code(
        turn(
            "Change the age window and re-run. Try:\n"
            "  (60, 100)  -> the full older cohort, age varies a lot\n"
            "  (70, 80)   -> a narrow band; age is nearly constant\n"
            "  (75, 85)\n"
            "Watch the 'age-only AUROC' bar collapse as the window narrows.",
            "AGE_MIN = 60\n"
            "AGE_MAX = 100",
        ) + "\n\n"
        "window = labelled[(labelled.age >= AGE_MIN) & (labelled.age <= AGE_MAX)]\n"
        "y_window = window['impaired'].astype(int)\n"
        "print(f'{len(window)} people aged {AGE_MIN}-{AGE_MAX}; {y_window.mean():.0%} impaired.\\n')\n\n"
        "sets = {'age only': ['age'],\n"
        "        'brain volume only': ['nwbv'],\n"
        "        'both': ['age', 'nwbv']}\n"
        "scores = {}\n"
        "for name, columns in sets.items():\n"
        "    X_tr, X_te, y_tr, y_te = split_data(window[columns], y_window)\n"
        "    scores[name] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_score_comparison(list(scores), list(scores.values()), reference=0.5,\n"
        "                            colours=['#e08214', '#2c6fbb', '#5aa469'],\n"
        "                            title=f'Ages {AGE_MIN}-{AGE_MAX}: what still works when age cannot help?',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()",
        "D-2-2"))

    cells.append(md(
        "### 2.3 QC verdict\n\n"
        "**Usable, and unusually honest about its own limitation.** We keep only the 235 participants with a "
        "clinical rating, we accept that `ses` is missing for a substantial minority, and we go into section 3 "
        "knowing that age and diagnosis are almost the same variable in this cohort.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "D-2-verdict"))

    cells.append(md(
        "---\n# 3 · Build models — and then take them apart\n\n"
        "This module inverts the usual goal. **We are not trying to get the highest score.** We are trying to "
        "find out what a good score is made of.",
        "D-s3"))
    cells += express_catchup("D", "df = load_data('D')\nlabelled = df.dropna(subset=['impaired']).copy()\nlabelled['status'] = np.where(labelled['impaired'] == 1, 'impaired', 'unimpaired')\nlabelled['band'] = pd.cut(labelled['age'], [59, 70, 78, 100], labels=['60-70', '70-78', '78+'])\nprint(f'{len(labelled)} participants with a clinical dementia rating. Ready for section 3.')")

    cells.append(md(
        "### 3.1 The naive model\n\n"
        "Throw everything in. This is what most people do first, and it is not wrong — it is just not yet an "
        "answer.",
        "D-3-1-md"))
    cells.append(code(
        "features = ['age', 'sex', 'education_code', 'ses', 'etiv_mm3', 'nwbv', 'asf']\n"
        "X = labelled[features]\n"
        "y = labelled['impaired'].astype(int)\n"
        "X_train, X_test, y_train, y_test = split_data(X, y)\n\n"
        "naive = train_model('logistic', X_train, y_train)\n"
        "naive_metrics = evaluate(naive, X_test, y_test)\n"
        "probability = naive.predict_proba(X_test)[:, 1]\n\n"
        "plots.plot_roc_pr(y_test, probability, title='Everything-in model — looks respectable')\n"
        "plt.show()\n"
        "for name, value in naive_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "D-3-1"))

    cells.append(md(
        "### 3.2 Ablation — take one column away at a time\n\n"
        "The cheapest way to find out what a model is standing on: remove each feature, refit, and see how "
        "far the score falls. A feature whose removal costs nothing was contributing nothing.",
        "D-3-2-md"))
    cells.append(code(
        "full_score = evaluate(train_model('logistic', X_train, y_train), X_test, y_test)['auroc']\n"
        "drops = {}\n"
        "for feature in features:\n"
        "    remaining = [name for name in features if name != feature]\n"
        "    X_tr, X_te, y_tr, y_te = split_data(labelled[remaining], y)\n"
        "    drops[feature] = full_score - evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_importance(list(drops), list(drops.values()),\n"
        "                      title='How much AUROC is lost when each feature is removed',\n"
        "                      xlabel='drop in AUROC when this column is deleted')\n"
        "plt.show()\n"
        "print(f'Full model AUROC: {full_score:.3f}')",
        "D-3-2"))

    cells.append(md(
        "### 3.3 The uncomfortable experiment — predict age instead\n\n"
        "If our features are really measuring *disease*, they should be much better at predicting disease "
        "than at predicting how old somebody is. Let's check that directly: same features, but the target is "
        "now \"is this person over 75?\".",
        "D-3-3-md"))
    cells.append(code(
        "brain_only = ['nwbv', 'etiv_mm3', 'asf']\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(labelled[brain_only], y)\n"
        "disease_score = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "old = (labelled['age'] > 75).astype(int)\n"
        "X_tr, X_te, y_tr, y_te = split_data(labelled[brain_only], old)\n"
        "age_score = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_score_comparison(['predicting\\nimpairment', 'predicting\\nbeing over 75'],\n"
        "                            [disease_score, age_score], reference=0.5,\n"
        "                            colours=['#2c6fbb', '#e08214'],\n"
        "                            title='The same three brain measurements, two different targets',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()",
        "D-3-3"))
    cells.append(thinking(
        "The brain measurements predict *age* at least as well as they predict *impairment*. Does that make the model useless?",
        "Not useless — but it does mean the model is not doing what its name suggests. Brain volume genuinely "
        "falls with age in everyone, and it falls faster with dementia. A model that has not been shown the "
        "person's age cannot tell those two causes apart, so a large part of its apparent 'diagnostic' skill "
        "is really age detection. That matters enormously in practice: a test that mostly detects age adds "
        "nothing to a clinician who can already see the patient's date of birth.",
        "D-3-3-think"))

    cells.append(md(
        "### 3.4 Simpson's paradox, on real data\n\n"
        "The most counter-intuitive thing in this notebook. Look at the relationship between **education** "
        "and impairment across the whole cohort, and then inside each age band separately. The direction can "
        "reverse — because the older participants in this cohort had, on average, different educational "
        "opportunities from the younger ones, and age drives impairment.",
        "D-3-4-md"))
    cells.append(code(
        "labelled = labelled.copy()\n"
        "labelled['band'] = pd.cut(labelled['age'], [59, 70, 78, 100], labels=['60-70', '70-78', '78+'])\n\n"
        "overall = labelled.groupby('education_code')['impaired'].mean()\n"
        "fig, axes = plt.subplots(1, 2, figsize=(11, 4))\n"
        "axes[0].plot(overall.index, 100 * overall.values, 'o-', color='#c0392b', linewidth=2)\n"
        "axes[0].set_title('Everyone pooled together')\n"
        "axes[0].set_xlabel('education code (higher = more education)')\n"
        "axes[0].set_ylabel('percent impaired')\n\n"
        "for name, group in labelled.groupby('band', observed=True):\n"
        "    rate = group.groupby('education_code')['impaired'].mean()\n"
        "    axes[1].plot(rate.index, 100 * rate.values, 'o-', linewidth=2, label=f'age {name} (n={len(group)})')\n"
        "axes[1].set_title('The same data, split by age band')\n"
        "axes[1].set_xlabel('education code (higher = more education)')\n"
        "axes[1].set_ylabel('percent impaired')\n"
        "axes[1].legend(fontsize=9)\n"
        "fig.suptitle(\"Simpson's paradox: the pooled trend need not be any group's trend\", fontsize=12)\n"
        "plt.tight_layout(); plt.show()\n\n"
        "print(pd.crosstab(labelled['band'], labelled['education_code'], normalize='index').round(2))\n"
        "print('\\n^ The age bands do not have the same education profile. That is what causes the paradox.')",
        "D-3-4"))

    cells.append(md(
        "### 3.5 ✏️ Your turn — four ways to handle a confounder\n\n"
        "Each of these is a real technique with real trade-offs. Switch between them and watch both the score "
        "*and* the sample size change.\n\n"
        "- **`'ignore'`** — leave age in, pretend the problem does not exist.\n"
        "- **`'exclude'`** — remove age from the features. Simple, but the *other* features still carry age.\n"
        "- **`'stratify'`** — build a separate model inside each age band. Honest, but each model sees fewer people.\n"
        "- **`'adjust'`** — regress age out of every brain measure first, then model the residuals. This is the "
        "standard epidemiological move.",
        "D-3-5-md"))
    cells.append(code(
        turn(
            "Try all four in turn. For each one, note BOTH the AUROC and the\n"
            "number of people used. A higher score on fewer, more similar people\n"
            "is not automatically a better result.",
            "STRATEGY = 'ignore'     # 'ignore', 'exclude', 'stratify' or 'adjust'",
        ) + "\n\n"
        "from sklearn.linear_model import LinearRegression\n\n"
        "brain = ['nwbv', 'etiv_mm3', 'asf']\n"
        "result_labels, result_scores, result_sizes = [], [], []\n\n"
        "if STRATEGY == 'ignore':\n"
        "    X_tr, X_te, y_tr, y_te = split_data(labelled[brain + ['age', 'sex']], y)\n"
        "    result_labels = ['age left in']\n"
        "    result_scores = [evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']]\n"
        "    result_sizes = [len(labelled)]\n\n"
        "elif STRATEGY == 'exclude':\n"
        "    X_tr, X_te, y_tr, y_te = split_data(labelled[brain + ['sex']], y)\n"
        "    result_labels = ['age removed']\n"
        "    result_scores = [evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']]\n"
        "    result_sizes = [len(labelled)]\n\n"
        "elif STRATEGY == 'stratify':\n"
        "    for name, group in labelled.groupby('band', observed=True):\n"
        "        target = group['impaired'].astype(int)\n"
        "        if target.nunique() < 2 or len(group) < 40:\n"
        "            continue\n"
        "        X_tr, X_te, y_tr, y_te = split_data(group[brain + ['sex']], target)\n"
        "        result_labels.append(f'age {name}')\n"
        "        result_scores.append(evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc'])\n"
        "        result_sizes.append(len(group))\n\n"
        "else:  # 'adjust'\n"
        "    adjusted = labelled.copy()\n"
        "    age_column = labelled[['age']].to_numpy()\n"
        "    for measure in brain:\n"
        "        expected = LinearRegression().fit(age_column, labelled[measure]).predict(age_column)\n"
        "        adjusted[measure] = labelled[measure] - expected   # what is left after age is accounted for\n"
        "    X_tr, X_te, y_tr, y_te = split_data(adjusted[brain + ['sex']], y)\n"
        "    result_labels = ['age regressed out']\n"
        "    result_scores = [evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']]\n"
        "    result_sizes = [len(labelled)]\n\n"
        "plots.plot_score_comparison([f'{a}\\n(n={b})' for a, b in zip(result_labels, result_sizes)],\n"
        "                            result_scores, reference=0.5,\n"
        "                            colours=['#2c6fbb'] * len(result_scores),\n"
        "                            title=f\"Strategy: {STRATEGY}\", ylabel='AUROC')\n"
        "plt.show()\n"
        "print('Remember: the goal is not the tallest bar. It is the bar you can defend.')",
        "D-3-5"))

    cells.append(md(
        "### 3.6 🔵 Your turn to write code — matching\n\n"
        "The fifth technique, and the one closest to what a randomised trial does. **Matching** builds a "
        "subsample in which the impaired and unimpaired groups have the *same* age distribution, by pairing "
        "each impaired person with an unimpaired person of similar age and discarding everyone left over.\n\n"
        "Fill in the `# TODO`. The scaffolding around it already works.",
        "D-3-6-md"))
    cells.append(code(
        "cases = labelled[labelled.impaired == 1]\n"
        "controls = labelled[labelled.impaired == 0]\n\n"
        "# TODO (🔵): for each case, find the unused control closest in age (within 3 years).\n"
        "#   Build a list `matched_rows` of the row indices you keep — both the case and its control.\n"
        "#   Hint: iterate over cases.iterrows(); track which control indices you have already used.\n"
        "matched_rows = []\n\n"
        "if matched_rows:\n"
        "    matched = labelled.loc[matched_rows]\n"
        "    print(f'{len(matched)} people kept, {len(labelled) - len(matched)} discarded.')\n"
        "    print(matched.groupby('impaired')['age'].agg(['mean', 'std', 'count']).round(2))\n"
        "    plots.plot_by_group(matched, 'age', 'impaired',\n"
        "                        title='After matching, the age distributions should sit on top of each other')\n"
        "    plt.show()\n"
        "    X_tr, X_te, y_tr, y_te = split_data(matched[['nwbv', 'etiv_mm3', 'asf', 'sex']],\n"
        "                                        matched['impaired'].astype(int))\n"
        "    print(f\"Matched-sample AUROC: {evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']:.3f}\")\n"
        "else:\n"
        "    print('Fill in the TODO above. The solutions notebook has a worked version.')",
        "D-3-6"))
    solutions["D-3-6"] = (
        "cases = labelled[labelled.impaired == 1]\n"
        "controls = labelled[labelled.impaired == 0]\n\n"
        "# ✅ Worked solution: greedy nearest-neighbour matching on age, without replacement.\n"
        "matched_rows = []\n"
        "used = set()\n"
        "for case_index, case in cases.iterrows():\n"
        "    available = controls.drop(index=list(used), errors='ignore')\n"
        "    if available.empty:\n"
        "        break\n"
        "    distance = (available['age'] - case['age']).abs()\n"
        "    nearest = distance.idxmin()\n"
        "    if distance[nearest] <= 3:            # only accept a close match\n"
        "        used.add(nearest)\n"
        "        matched_rows += [case_index, nearest]\n\n"
        "# Why greedy-without-replacement: reusing one control for several cases would make the\n"
        "# control group artificially homogeneous and understate its variance. Refusing matches\n"
        "# worse than 3 years is the 'caliper' — it keeps the balance tight at the cost of throwing\n"
        "# away cases with no comparable control, which is itself informative: if the oldest cases\n"
        "# have no age-matched controls, then for those people the question is unanswerable in this\n"
        "# cohort, and no amount of statistical adjustment can conjure the missing comparison.\n\n"
        "matched = labelled.loc[matched_rows]\n"
        "print(f'{len(matched)} people kept, {len(labelled) - len(matched)} discarded.')\n"
        "print(matched.groupby('impaired')['age'].agg(['mean', 'std', 'count']).round(2))\n"
        "plots.plot_by_group(matched, 'age', 'impaired',\n"
        "                    title='After matching, the age distributions should sit on top of each other')\n"
        "plt.show()\n"
        "X_tr, X_te, y_tr, y_te = split_data(matched[['nwbv', 'etiv_mm3', 'asf', 'sex']],\n"
        "                                    matched['impaired'].astype(int))\n"
        "print(f\"Matched-sample AUROC: {evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']:.3f}\")"
    )

    cells.append(go_further(
        "D-3-further",
        "run 3.5 with all four strategies and write down, in one sentence each, what each one assumes.",
        "complete the matching TODO, then compare the matched-sample AUROC with the 'adjust' strategy's. "
        "Which do you trust more, and why?",
        "propensity-score matching generalises 3.6 to many confounders at once. Look it up and consider what "
        "happens when the confounder you did not measure is the important one.",
    ))

    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "The deliverable of this module is not a score. It is a **judgement about what the score means**.",
        "D-s4"))
    cells.append(md(
        "### 4.1 Every framing, side by side\n\n"
        "One figure summarising the whole module.",
        "D-4-1-md"))
    cells.append(code(
        "from sklearn.linear_model import LinearRegression\n\n"
        "summary = {}\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(labelled[features], y)\n"
        "summary['everything in'] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(labelled[['age']], y)\n"
        "summary['age alone'] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(labelled[['nwbv', 'etiv_mm3', 'asf']], y)\n"
        "summary['brain alone'] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "adjusted = labelled.copy()\n"
        "age_column = labelled[['age']].to_numpy()\n"
        "for measure in ['nwbv', 'etiv_mm3', 'asf']:\n"
        "    adjusted[measure] = labelled[measure] - LinearRegression().fit(age_column, labelled[measure]).predict(age_column)\n"
        "X_tr, X_te, y_tr, y_te = split_data(adjusted[['nwbv', 'etiv_mm3', 'asf']], y)\n"
        "summary['brain, age removed'] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "narrow = labelled[(labelled.age >= 70) & (labelled.age <= 80)]\n"
        "X_tr, X_te, y_tr, y_te = split_data(narrow[['nwbv', 'etiv_mm3', 'asf']], narrow['impaired'].astype(int))\n"
        "summary['brain, ages 70-80 only'] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_score_comparison(list(summary), list(summary.values()), reference=0.5,\n"
        "                            colours=['#e08214', '#c0392b', '#2c6fbb', '#5aa469', '#8e44ad'],\n"
        "                            title='Five honest analyses of one dataset. They do not agree.',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()\n"
        "for name, value in summary.items():\n"
        "    print(f'  {name:<26s} {value:.3f}')",
        "D-4-1"))

    cells.append(md(
        "### 4.2 Where the errors land\n\n"
        "Subgroup analysis, which in this module is not a footnote but the finding.",
        "D-4-2-md"))
    cells.append(code(
        "X_tr, X_te, y_tr, y_te = split_data(labelled[features], y)\n"
        "final_model = train_model('logistic', X_tr, y_tr)\n"
        "final_probability = final_model.predict_proba(X_te)[:, 1]\n"
        "final_predicted = (final_probability >= 0.5).astype(int)\n\n"
        "plots.plot_confusion(y_te, final_predicted, labels=('unimpaired', 'impaired'),\n"
        "                     title='Everything-in model on held-out participants')\n"
        "plt.show()\n\n"
        "check = labelled.loc[X_te.index].copy()\n"
        "check['correct'] = (final_predicted == y_te).astype(int)\n"
        "check['band'] = pd.cut(check['age'], [59, 70, 78, 100], labels=['60-70', '70-78', '78+'])\n"
        "for subgroup in ['band', 'sex', 'education_code']:\n"
        "    plots.plot_subgroup_errors(check.dropna(subset=[subgroup]), subgroup, 'correct',\n"
        "                               title=f'Proportion correct by {subgroup}')\n"
        "    plt.show()",
        "D-4-2"))

    cells.append(md(
        "### 4.3 Shapley values — how much of the prediction *is* age?\n\n"
        "Section 3.2 removed features one at a time and watched the score fall. **Shapley values** ask a "
        "sharper question, per person: how much did *this participant's* age, specifically, move *their* "
        "predicted risk?\n\n"
        "The idea comes from game theory. Treat the features as players on a team and the prediction as the "
        "prize; a feature's Shapley value is its fair share, averaged over every order in which the team "
        "could have been assembled. With seven features that is all 2⁷ = 128 combinations, so we compute the "
        "**exact** values rather than the approximations the `shap` package uses.\n\n"
        "Look at where `age` lands — and then compare it with the ablation figure in 3.2, which said "
        "something quite different.",
        "D-4-3-md"))
    cells.append(code(
        "from interpret import shapley_values, shapley_importance, baseline_prediction\n\n"
        "explain_columns = ['age', 'nwbv', 'etiv_mm3', 'asf', 'education_code', 'ses']\n"
        "X_tr3, X_te3, y_tr3, y_te3 = split_data(labelled[explain_columns], y)\n"
        "explain_model = train_model('random_forest', X_tr3, y_tr3)\n\n"
        "shap_frame = shapley_values(explain_model, X_te3.head(60), X_tr3, features=explain_columns)\n"
        "importance = shapley_importance(shap_frame)\n"
        "plots.plot_importance(importance.index, importance.values,\n"
        "                      title='Average influence on the predicted probability of impairment',\n"
        "                      xlabel='mean |contribution| (exact Shapley values)')\n"
        "plt.show()\n\n"
        "share = importance / importance.sum()\n"
        "for name, value in share.items():\n"
        "    print(f'  {name:<16s} {value:.0%} of all the movement in this model\\'s predictions')\n"
        "print()\n"
        "print(f\"Age accounts for {share['age']:.0%} of it — yet section 3.2 showed that DELETING the age\")\n"
        "print('column costs the model almost nothing. Hold both of those facts in your head, then')\n"
        "print('open the box below.')",
        "D-4-3"))
    cells.append(thinking(
        "Ablation said deleting `age` costs roughly nothing. Shapley says age drives about a quarter of every prediction. Which is wrong?",
        "Neither. They answer different questions, and the gap between them is the single most useful thing "
        "in this module.\n\n"
        "**Ablation** asks *\"what happens to the score if I delete this column?\"* Almost nothing happens — "
        "because `nwbv`, `asf` and `etiv_mm3` are themselves correlated with age, so when you remove the age "
        "column the model simply reads age off the brain measurements instead. Ablation therefore reports "
        "\"unimportant\" for a confounder whenever *anything else* can stand in for it.\n\n"
        "**Shapley values** ask *\"among the features actually present, how is the credit for this "
        "prediction divided?\"* Age is genuinely doing about a quarter of the work, and it says so.\n\n"
        "The practical lesson, and it is a trap people fall into constantly: **a feature you can delete "
        "without losing accuracy is not a feature the model was ignoring.** To find out whether age matters "
        "you have to break its link with the outcome — stratify, adjust or match, as in 3.5 and 3.6 — not "
        "merely drop the column and watch the score.",
        "D-4-3-think"))

    cells.append(md(
        "### 4.4 ✏️ Your turn — one participant at a time\n\n"
        "Pick individual people and read what the model based their prediction on. Look for somebody whose "
        "risk was driven almost entirely by their age.",
        "D-4-4-md"))
    cells.append(code(
        turn(
            "Try several values of PERSON (0 to 59).\n"
            "For each, read the bars as a sentence: 'their predicted risk was\n"
            "pushed up mainly by ___ and pulled down by ___'.\n"
            "Then ask: would a clinician have needed a model to say that?",
            "PERSON = 0",
        ) + "\n\n"
        "contributions = shap_frame.iloc[PERSON].sort_values()\n"
        "plots.plot_importance(contributions.index, contributions.values,\n"
        "                      title=f'Participant {X_te3.index[PERSON]}: what drove their predicted risk',\n"
        "                      xlabel='contribution to predicted probability (blue raises risk)')\n"
        "plt.show()\n\n"
        "print('Their actual measurements:')\n"
        "print(X_te3.iloc[PERSON].round(3).to_string())\n"
        "average = baseline_prediction(explain_model, X_tr3)\n"
        "print()\n"
        "print(f'  cohort average risk   {average:.3f}')\n"
        "print(f'  + contributions       {contributions.sum():+.3f}')\n"
        "print(f'  = predicted risk      {average + contributions.sum():.3f}')\n"
        "print(f'  actually impaired?    {\"yes\" if y_te3.iloc[PERSON] == 1 else \"no\"}')",
        "D-4-4"))

    cells.append(md(
        "### 4.5 What this module is for\n\n"
        "You built a model with a respectable AUROC and then showed that a large part of it was **age**, and "
        "that the apparent effect of education **reverses** depending on how you slice the data. Neither "
        "finding is a bug in the code. Both are properties of how the cohort was recruited.\n\n"
        "Three things worth carrying into every other module today:\n\n"
        "1. **A confounder is not noise.** It is a real cause of both the feature and the outcome. You cannot "
        "average it away; you have to design around it.\n"
        "2. **A high score is a question, not an answer.** The right response to 'my model got 0.92' is "
        "'0.92 of what, measured how, on whom?'\n"
        "3. **The choice of analysis is a scientific claim.** Adjusting for age, or not, is an assertion about "
        "what you think is causing what. Make it explicitly, and say so in the write-up.\n\n"
        "**On bias.** OASIS-1 is volunteers from one American city — predominantly white, predominantly "
        "educated, healthy enough to lie still in a scanner. `ses` is missing most often for the people whose "
        "socioeconomic circumstances are hardest to record. Every confounding problem in this notebook exists "
        "in a harsher form for groups who are underrepresented, because there are fewer of them to adjust with.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "Somebody shows you a dementia-screening model with an AUROC of 0.94, trained on a hospital's memory "
        "clinic records. **What three questions do you ask before believing it?**",
        "D-4-3"))

    cells.append(go_further(
        "D-4-further",
        "pick which of the five bars in 4.1 you would put in a paper's abstract, and be ready to defend it.",
        "add `mmse` to the everything-in model and watch the AUROC jump. Then explain why that is the least "
        "interesting model in the notebook.",
        "read one paper that reports a dementia-prediction AUROC and find out how it handled age. Many do not say.",
    ))

    return cells, solutions


# =============================================================================
# Module E — clinical records and epidemiology
# =============================================================================

def build_E():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "E", "Clinical records and epidemiology",
        "Which life-course factors predict a later dementia diagnosis?",
        [
            "read a survival dataset — where the outcome is not just *whether* but *when*",
            "draw and interpret a Kaplan–Meier curve, the workhorse plot of clinical epidemiology",
            "fit both an epidemiological model (hazard ratios) and a machine-learning model to the same question, and say what each one is for",
            "compute **Shapley values** to explain a single person's predicted risk",
            "name three ways an observational cohort can produce a confident, wrong conclusion",
        ],
        "**This cohort is simulated.** Individual-level electronic health records are never openly "
        "redistributable — there is no version of this dataset we could legally ship you. So 900 participants "
        "were generated from a survival model whose hazard ratios are set to *published* population estimates: "
        "APOE ε4 roughly 2.6× per allele, diabetes ~1.45×, depression history ~1.6×, more education "
        "protective, and so on. The associations you recover should therefore match the literature — because "
        "we put them there. What is real is the **method**, and the traps.",
        "Skim section 2, then work through 3.2 (Kaplan–Meier) and section 4 (Shapley values) properly.",
        warning="Simulated cohort with published effect sizes built in. You are learning the method, not discovering the biology.",
    ))
    cells.append(setup_cell("E"))

    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "One row is one person, followed from a baseline visit until one of three things happens: they are "
        "diagnosed with dementia, they die, or the study ends. **Which of those three happened matters as "
        "much as when.**",
        "E-s1"))
    cells.append(md(
        "### 1.1 The columns\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| `age_baseline` | Age when they joined the study. |\n"
        "| `sex`, `education_years` | |\n"
        "| `apoe4_dose` | Number of *APOE* ε4 alleles: 0, 1 or 2. The strongest common genetic risk factor. |\n"
        "| `hypertension`, `diabetes`, `smoking` | Midlife vascular risk factors — the modifiable ones. |\n"
        "| `physical_activity` | 1 = regularly active. Protective in most cohorts. |\n"
        "| `depression_history` | 1 = history of depression. **Read the 🧠 box in 1.3 before you interpret this one.** |\n"
        "| `baseline_mmse`, `systolic_bp` | Measurements at the baseline visit. |\n"
        "| `followup_years` | **How long we watched them.** |\n"
        "| `diagnosis_event` | 1 = diagnosed with dementia during follow-up. |\n"
        "| `died_without_diagnosis` | 1 = died first. This is a **competing risk** — you cannot be diagnosed after you die. |\n\n"
        "The pair (`followup_years`, `diagnosis_event`) is what makes this **survival data**. Someone with "
        "`diagnosis_event = 0` and `followup_years = 2.1` is not \"a healthy person\" — they are \"a person we "
        "only watched for two years\". Treating those two as the same is the classic beginner's error.",
        "E-1-1-md"))
    cells.append(code(
        "df = load_data('E')\n"
        "print(f'{len(df)} participants.')\n"
        "print(f'  diagnosed during follow-up : {int(df.diagnosis_event.sum())}')\n"
        "print(f'  died without a diagnosis   : {int(df.died_without_diagnosis.sum())}')\n"
        "print(f'  still undiagnosed at the end: {int(((df.diagnosis_event == 0) & (df.died_without_diagnosis == 0)).sum())}')\n"
        "print(f'  median follow-up           : {df.followup_years.median():.1f} years\\n')\n"
        "df.head()",
        "E-1-1"))

    cells.append(md(
        "### 1.2 Who is in the cohort, and how long did we watch them?",
        "E-1-2-md"))
    cells.append(code(
        "fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))\n"
        "axes[0].hist(df['age_baseline'], bins=25, color='#2c6fbb')\n"
        "axes[0].set_xlabel('age at baseline (years)'); axes[0].set_ylabel('number of people')\n"
        "axes[0].set_title('Age when they joined')\n"
        "axes[1].hist([df.loc[df.diagnosis_event == 1, 'followup_years'],\n"
        "              df.loc[df.diagnosis_event == 0, 'followup_years']],\n"
        "             bins=20, stacked=True, color=['#e08214', '#cccccc'],\n"
        "             label=['diagnosed', 'not diagnosed (censored)'])\n"
        "axes[1].set_xlabel('years of follow-up'); axes[1].set_ylabel('number of people')\n"
        "axes[1].set_title('How long each person was observed')\n"
        "axes[1].legend(fontsize=9)\n"
        "plt.tight_layout(); plt.show()\n\n"
        "print(df.groupby('diagnosis_event')[['age_baseline', 'apoe4_dose', 'education_years', 'followup_years']].mean().round(2))",
        "E-1-2"))

    cells.append(md(
        "### 1.3 ✏️ Your turn — one risk factor at a time\n\n"
        "For a binary exposure, epidemiology's simplest tool is the **2×2 table** and the **odds ratio**: how "
        "many times more likely is a diagnosis among the exposed than the unexposed?",
        "E-1-3-md"))
    cells.append(code(
        turn(
            "Try each of these in turn:\n"
            "  'apoe4_dose', 'hypertension', 'diabetes', 'smoking',\n"
            "  'physical_activity', 'depression_history', 'sex'\n"
            "Which has the biggest odds ratio? Is that the one you would\n"
            "run a public-health campaign about?",
            "RISK_FACTOR = 'apoe4_dose'",
        ) + "\n\n"
        "table = pd.crosstab(df[RISK_FACTOR], df['diagnosis_event'])\n"
        "table.columns = ['no diagnosis', 'diagnosed']\n"
        "display(table)\n\n"
        "rates = 100 * df.groupby(RISK_FACTOR)['diagnosis_event'].mean()\n"
        "counts = df.groupby(RISK_FACTOR).size()\n"
        "plots.plot_score_comparison([f'{level}\\n(n={counts[level]})' for level in rates.index],\n"
        "                            rates.tolist(), colours=['#2c6fbb'] * len(rates),\n"
        "                            title=f'Percentage diagnosed, by {RISK_FACTOR}',\n"
        "                            ylabel='percent diagnosed')\n"
        "plt.show()\n\n"
        "if table.shape[0] == 2:\n"
        "    (a, b), (c, d) = table.to_numpy()\n"
        "    print(f'Odds ratio for {RISK_FACTOR}: {(d * a) / (c * b):.2f}')\n"
        "    print('An odds ratio of 1.0 means no association. 2.0 means the odds double.')\n"
        "else:\n"
        "    print('More than two levels — compare the bars directly, or group them into two.')",
        "E-1-3"))
    cells.append(thinking(
        "`depression_history` shows a strong association with later dementia. Does treating depression prevent dementia?",
        "You cannot tell from this. There are at least three explanations, and the data cannot separate them:\n\n"
        "1. **Causation** — depression damages the brain, or reduces the social and cognitive activity that "
        "protects it.\n"
        "2. **Reverse causation** — the earliest changes of dementia, years before diagnosis, *present* as "
        "apathy and low mood. The 'risk factor' is actually an early symptom. This is called the "
        "**prodromal** period and it is a serious problem for every dementia risk factor measured near the end.\n"
        "3. **Confounding** — something else (vascular disease, social isolation, inflammation) causes both.\n\n"
        "The standard partial fix is a **lag**: exclude everyone diagnosed within, say, five years of the "
        "exposure measurement, and see if the association survives. It is a take-home exercise below.",
        "E-1-3-think"))

    cells.append(go_further(
        "E-1-further",
        "run 1.3 for every risk factor and rank them by odds ratio.",
        "compute odds ratios for all of them in a loop and plot them on a single horizontal bar chart with a "
        "line at 1.0. That plot is called a **forest plot** and it is how epidemiology results are published.",
        "look up the 2024 Lancet Commission on dementia prevention. It lists 14 modifiable risk factors and "
        "estimates what fraction of cases each could prevent — a calculation called the *population attributable fraction*.",
    ))

    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "The flaws in a cohort study are rarely missing values. They are structural, and they are the reason "
        "epidemiology is a discipline rather than a spreadsheet.",
        "E-s2"))

    cells.append(md(
        "### 2.1 Competing risk — the people who died first\n\n"
        "In a cohort with a median age near 70, a substantial number of participants die before they could "
        "ever have been diagnosed with dementia. If you count them as \"did not get dementia\", you will "
        "systematically **underestimate** risk in exactly the oldest and sickest people.\n\n"
        "Worse: a factor that kills people quickly (heavy smoking, say) can look *protective* against "
        "dementia, purely because its victims are not around to be diagnosed. This is a real, documented "
        "phenomenon and it has misled published studies.",
        "E-2-1-md"))
    cells.append(code(
        "outcome = np.where(df.diagnosis_event == 1, 'diagnosed',\n"
        "                   np.where(df.died_without_diagnosis == 1, 'died first', 'still undiagnosed'))\n"
        "plots.plot_class_balance(pd.Series(outcome), title='What actually happened to the 900 participants')\n"
        "plt.show()\n\n"
        "band = pd.cut(df['age_baseline'], [54, 65, 72, 80, 95], labels=['55-65', '65-72', '72-80', '80+'])\n"
        "death_rate = 100 * df.groupby(band, observed=True)['died_without_diagnosis'].mean()\n"
        "plots.plot_score_comparison(death_rate.index.astype(str).tolist(), death_rate.tolist(),\n"
        "                            colours=['#c0392b'] * len(death_rate),\n"
        "                            title='Percentage who died before any dementia diagnosis, by baseline age',\n"
        "                            ylabel='percent')\n"
        "plt.show()",
        "E-2-1"))

    cells.append(md(
        "### 2.2 ✏️ Your turn — how you treat the dead changes the answer\n\n"
        "Three defensible choices, three different numbers.",
        "E-2-2-md"))
    cells.append(code(
        turn(
            "Try all three:\n"
            "  'as_healthy' -> count deaths as 'no dementia'  (the naive default)\n"
            "  'exclude'    -> drop everyone who died          (also biased, differently)\n"
            "  'censor'     -> keep them, but only up to their death (the right answer)\n"
            "Watch the estimated risk move.",
            "HANDLE_DEATHS = 'as_healthy'",
        ) + "\n\n"
        "if HANDLE_DEATHS == 'exclude':\n"
        "    working = df[df.died_without_diagnosis == 0].copy()\n"
        "elif HANDLE_DEATHS == 'censor':\n"
        "    working = df.copy()   # already censored at death in the followup_years column\n"
        "else:\n"
        "    working = df.copy()\n\n"
        "overall = 100 * working['diagnosis_event'].mean()\n"
        "by_age = 100 * working.groupby(pd.cut(working['age_baseline'], [54, 65, 72, 80, 95],\n"
        "                                      labels=['55-65', '65-72', '72-80', '80+']),\n"
        "                               observed=True)['diagnosis_event'].mean()\n\n"
        "plots.plot_score_comparison(by_age.index.astype(str).tolist(), by_age.tolist(),\n"
        "                            colours=['#2c6fbb'] * len(by_age), reference=overall,\n"
        "                            title=f\"'{HANDLE_DEATHS}': {overall:.1f}% diagnosed overall (dashed line)\",\n"
        "                            ylabel='percent diagnosed')\n"
        "plt.show()\n"
        "print(f'{len(working)} people in this analysis.')\n"
        "print('Note especially what happens to the OLDEST band under each choice.')",
        "E-2-2"))

    cells.append(md(
        "### 2.3 Immortal time\n\n"
        "A third trap, and the subtlest. Suppose you define an exposure group by something that takes time to "
        "happen — \"people who attended at least three follow-up visits\", say. To be in that group you must "
        "have *survived* long enough to attend three visits. Those months are **immortal time**: by "
        "construction, nobody in the group could have had the outcome during them.\n\n"
        "The result is a group that looks miraculously protected. This has produced dozens of retracted "
        "or corrected findings, including several apparent 'benefits' of medications.",
        "E-2-3-md"))
    cells.append(code(
        "# A deliberately wrong analysis: define 'long attenders' by their total follow-up.\n"
        "long_attender = df['followup_years'] > df['followup_years'].median()\n"
        "rates = 100 * df.groupby(long_attender)['diagnosis_event'].mean()\n\n"
        "plots.plot_score_comparison(['short follow-up', 'long follow-up (\"good attenders\")'],\n"
        "                            rates.tolist(), colours=['#2c6fbb', '#c0392b'],\n"
        "                            title='A fabricated \"protective effect\" of attending for longer',\n"
        "                            ylabel='percent diagnosed')\n"
        "plt.show()\n"
        "print('This bar chart is nonsense, and it is the kind of nonsense that gets published.')\n"
        "print('Anything that uses follow-up duration to define groups builds the answer into the question.')",
        "E-2-3"))

    cells.append(md(
        "### 2.4 QC verdict\n\n"
        "**Usable for association, never for causation.** Three standing caveats:\n\n"
        "1. Deaths are censored, not counted as healthy. Any absolute risk we quote is a risk *conditional on "
        "surviving*.\n"
        "2. Exposures measured at baseline may be early symptoms rather than causes (see 1.3).\n"
        "3. Never define a group using anything that happened after baseline.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "E-2-verdict"))

    cells.append(md(
        "---\n# 3 · Two ways to model the same question\n\n"
        "Epidemiology and machine learning ask *different questions of the same table*, and confusing them is "
        "a common mistake:\n\n"
        "| | Epidemiology | Machine learning |\n|---|---|---|\n"
        "| Asks | \"Is smoking associated with dementia, and how strongly?\" | \"For this person, what is the risk?\" |\n"
        "| Wants | An unbiased estimate of one effect, with a confidence interval | The best possible prediction, by any means |\n"
        "| Fears | Confounding | Overfitting |\n"
        "| Success | A number you can act on as policy | A score on people it has never seen |\n\n"
        "We do both.",
        "E-s3"))
    cells += express_catchup("E", "df = load_data('E')\nprint(f'{len(df)} participants; {int(df.diagnosis_event.sum())} diagnosed during follow-up.')\nprint('Ready for section 3.')")

    cells.append(md(
        "### 3.1 The epidemiologist's plot — Kaplan–Meier\n\n"
        "A Kaplan–Meier curve answers: *of the people still undiagnosed at year t, what fraction remain "
        "undiagnosed?* It handles the fact that people were watched for different lengths of time, which a "
        "simple percentage cannot.\n\n"
        "It is computed by walking through time and multiplying survival probabilities at each event. "
        "`plots.kaplan_meier` does exactly that in eight readable lines — open `src/plots.py` if you want to "
        "see the arithmetic.",
        "E-3-1-md"))
    cells.append(code(
        "plots.plot_survival(df, 'followup_years', 'diagnosis_event', 'apoe4_dose',\n"
        "                    title='Time to dementia diagnosis by APOE e4 dose')\n"
        "plt.show()\n"
        "print('Curves that separate early and stay separated indicate a strong, sustained effect.')\n"
        "print('Curves that cross mean the effect changes over time — and a single hazard ratio would hide that.')",
        "E-3-1"))

    cells.append(md(
        "### 3.2 ✏️ Your turn — split the curve by anything\n\n"
        "Change `SPLIT_BY` and watch the curves separate — or not.",
        "E-3-2-md"))
    cells.append(code(
        turn(
            "Try each of:\n"
            "  'apoe4_dose', 'diabetes', 'smoking', 'physical_activity',\n"
            "  'depression_history', 'hypertension', 'sex', 'education_group'\n"
            "Which factor separates the curves most? Which one would you\n"
            "rather be able to change about your own life?",
            "SPLIT_BY = 'physical_activity'",
        ) + "\n\n"
        "working = df.copy()\n"
        "working['education_group'] = np.where(working['education_years'] >= 13, '13+ years', 'under 13 years')\n\n"
        "plots.plot_survival(working, 'followup_years', 'diagnosis_event', SPLIT_BY,\n"
        "                    title=f'Time to diagnosis, split by {SPLIT_BY}')\n"
        "plt.show()\n\n"
        "for name, group in working.groupby(SPLIT_BY):\n"
        "    at_five = group[group.followup_years >= 5]\n"
        "    print(f'  {SPLIT_BY} = {name}: {len(group)} people, {group.diagnosis_event.mean():.1%} diagnosed')",
        "E-3-2"))

    cells.append(md(
        "### 3.3 Hazard ratios — the epidemiologist's model\n\n"
        "A **Cox proportional-hazards model** estimates, for each factor, how much it multiplies the "
        "instantaneous rate of diagnosis, holding the others fixed. That multiplier is the **hazard ratio**: "
        "1.0 = no effect, 2.0 = twice the rate, 0.5 = half.\n\n"
        "If `lifelines` is installed we fit a real Cox model. If not, we fall back to a logistic regression, "
        "whose odds ratios tell a similar story here. Either way you get the same figure: **a forest plot**.",
        "E-3-3-md"))
    cells.append(code(
        "predictors = ['age_baseline', 'apoe4_dose', 'education_years', 'hypertension',\n"
        "              'diabetes', 'smoking', 'physical_activity', 'depression_history']\n\n"
        "try:\n"
        "    from lifelines import CoxPHFitter\n"
        "    cox_frame = df[predictors + ['followup_years', 'diagnosis_event']].copy()\n"
        "    cox = CoxPHFitter().fit(cox_frame, duration_col='followup_years', event_col='diagnosis_event')\n"
        "    ratios = np.exp(cox.params_)\n"
        "    lower, upper = np.exp(cox.confidence_intervals_.iloc[:, 0]), np.exp(cox.confidence_intervals_.iloc[:, 1])\n"
        "    kind = 'hazard ratio (Cox model)'\n"
        "except ImportError:\n"
        "    from sklearn.linear_model import LogisticRegression\n"
        "    from sklearn.preprocessing import StandardScaler\n"
        "    print('lifelines is not installed — using logistic regression odds ratios instead.')\n"
        "    print('Install with: pip install lifelines\\n')\n"
        "    scaler = StandardScaler().fit(df[predictors])\n"
        "    fitted = LogisticRegression(max_iter=2000).fit(scaler.transform(df[predictors]), df['diagnosis_event'])\n"
        "    scale = pd.Series(scaler.scale_, index=predictors)\n"
        "    ratios = np.exp(pd.Series(fitted.coef_[0], index=predictors) / scale)\n"
        "    lower = upper = None\n"
        "    kind = 'odds ratio (logistic regression)'\n\n"
        "fig, ax = plt.subplots(figsize=(7.5, 4.2))\n"
        "positions = np.arange(len(ratios))\n"
        "ax.scatter(ratios.values, positions, s=70, color='#2c6fbb', zorder=3)\n"
        "if lower is not None:\n"
        "    ax.hlines(positions, lower.values, upper.values, color='#2c6fbb', linewidth=2)\n"
        "ax.axvline(1.0, color='#c0392b', linestyle='--')\n"
        "ax.set_yticks(positions, ratios.index, fontsize=9)\n"
        "ax.set_xscale('log')\n"
        "ax.set_xlabel(f'{kind} — right of the red line means higher risk')\n"
        "ax.set_title('Forest plot: each factor, adjusted for all the others')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "print(ratios.round(3))",
        "E-3-3"))

    cells.append(md(
        "### 3.4 The machine-learning model\n\n"
        "Same table, different question: *for a person we have never met, how likely is a diagnosis?* "
        "Everything is scored on people the model has not seen.",
        "E-3-4-md"))
    cells.append(code(
        "X = df[predictors]\n"
        "y = df['diagnosis_event']\n"
        "X_train, X_test, y_train, y_test = split_data(X, y)\n\n"
        "ladder = ['baseline', 'logistic', 'tree', 'random_forest', 'gradient_boosting']\n"
        "table = compare_models(ladder, X_train, y_train, X_test, y_test)\n"
        "display(table)\n"
        "plots.plot_model_comparison(table, metric='auroc', title='Predicting who will be diagnosed (AUROC)')\n"
        "plt.show()\n"
        "print('Expect roughly 0.70-0.80. Risk prediction from ordinary risk factors is genuinely hard,')\n"
        "print('and anyone claiming 0.95 from data like this has leaked something.')",
        "E-3-4"))

    cells.append(md(
        "### 3.5 ✏️ Your turn — one tree you can actually read\n\n"
        "A decision tree is a flowchart, and a shallow one can be printed and understood by a clinician. "
        "That is worth something: a model nobody can inspect is a model nobody can challenge.",
        "E-3-5-md"))
    cells.append(code(
        turn(
            "Try DEPTH = 1, 2, 3, then 8.\n"
            "At what depth does the flowchart stop being readable?\n"
            "At what depth does the held-out score stop improving?\n"
            "Those two depths are rarely the same, and choosing between them\n"
            "is a real decision, not a technical one.",
            "DEPTH = 3",
        ) + "\n\n"
        "from sklearn.tree import DecisionTreeClassifier, plot_tree\n\n"
        "tree = DecisionTreeClassifier(max_depth=DEPTH, class_weight='balanced', random_state=42)\n"
        "tree.fit(X_train, y_train)\n\n"
        "fig, ax = plt.subplots(figsize=(min(4 + 3 * DEPTH, 20), 3 + 1.6 * DEPTH))\n"
        "plot_tree(tree, feature_names=list(X_train.columns), class_names=['no diagnosis', 'diagnosed'],\n"
        "          filled=True, rounded=True, fontsize=8, impurity=False, ax=ax)\n"
        "ax.set_title(f'A decision tree of depth {DEPTH}')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "swept, train_scores, test_scores = sweep_parameter(\n"
        "    'tree', 'max_depth', [1, 2, 3, 5, 8, 12], X_train, y_train, X_test, y_test)\n"
        "plots.plot_parameter_sweep(swept, train_scores, test_scores, 'max_depth',\n"
        "                           title='Deeper trees memorise. The blue line is what matters.')\n"
        "plt.show()",
        "E-3-5"))

    cells.append(md(
        "### 3.6 🔵 Your turn to write code — the five-year lag\n\n"
        "The reverse-causation fix from 1.3. If depression really *causes* dementia, the association should "
        "survive when we ignore everyone diagnosed soon after baseline — because those are the people whose "
        "'depression' was most likely an early symptom.\n\n"
        "Fill in the `# TODO`.",
        "E-3-6-md"))
    cells.append(code(
        "# TODO (🔵): build `lagged`, a copy of df that EXCLUDES anyone diagnosed within 5 years.\n"
        "#   Careful: you must drop those people entirely, not relabel them — otherwise you have\n"
        "#   invented an immortal-time bias of your own (section 2.3).\n"
        "#   Then compute the odds ratio for depression_history in both df and lagged.\n"
        "LAG_YEARS = 5\n"
        "lagged = None   # replace me\n\n"
        "def odds_ratio(frame, column):\n"
        "    counts = pd.crosstab(frame[column], frame['diagnosis_event'])\n"
        "    (a, b), (c, d) = counts.to_numpy()\n"
        "    return (d * a) / (c * b)\n\n"
        "if lagged is not None:\n"
        "    plots.plot_score_comparison(\n"
        "        [f'all {len(df)} people', f'excluding early cases\\n({len(lagged)} people)'],\n"
        "        [odds_ratio(df, 'depression_history'), odds_ratio(lagged, 'depression_history')],\n"
        "        colours=['#c0392b', '#2c6fbb'], reference=1.0,\n"
        "        title='Does the depression association survive a 5-year lag?', ylabel='odds ratio')\n"
        "    plt.show()\n"
        "else:\n"
        "    print('Fill in the TODO above. The solutions notebook has a worked version.')",
        "E-3-6"))
    solutions["E-3-6"] = (
        "# ✅ Worked solution.\n"
        "LAG_YEARS = 5\n"
        "early_case = (df['diagnosis_event'] == 1) & (df['followup_years'] < LAG_YEARS)\n"
        "lagged = df[~early_case].copy()\n\n"
        "def odds_ratio(frame, column):\n"
        "    counts = pd.crosstab(frame[column], frame['diagnosis_event'])\n"
        "    (a, b), (c, d) = counts.to_numpy()\n"
        "    return (d * a) / (c * b)\n\n"
        "plots.plot_score_comparison(\n"
        "    [f'all {len(df)} people', f'excluding early cases\\n({len(lagged)} people)'],\n"
        "    [odds_ratio(df, 'depression_history'), odds_ratio(lagged, 'depression_history')],\n"
        "    colours=['#c0392b', '#2c6fbb'], reference=1.0,\n"
        "    title='Does the depression association survive a 5-year lag?', ylabel='odds ratio')\n"
        "plt.show()\n\n"
        "# What to expect and how to read it. In THIS dataset the association was generated as a\n"
        "# genuine causal effect, so it survives the lag almost unchanged — the exposure really did\n"
        "# come first. In real cohorts the depression-dementia odds ratio typically shrinks under a\n"
        "# lag, sometimes a lot, which is the signature of reverse causation: part of what looked\n"
        "# like a risk factor was prodromal disease.\n"
        "#\n"
        "# Note the cost. Excluding early cases throws away the events that occurred soonest, which\n"
        "# are often the most informative ones, so the lagged estimate is less precise. And the lag\n"
        "# is a judgement call: five years is convention, not physiology. Report the result at\n"
        "# several lags rather than picking the one you like."
    )

    cells.append(go_further(
        "E-3-further",
        "in 3.2, find the factor that separates the survival curves most and the one that separates them least.",
        "install `lifelines` (`pip install lifelines`) and re-run 3.3 to get real hazard ratios with confidence "
        "intervals, then check whether the intervals cross 1.0.",
        "fit a **Fine–Gray competing-risks model**, which handles death properly rather than censoring it. "
        "Compare its estimates with the Cox model's for the oldest participants.",
    ))

    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "Including the question that matters most for a risk model somebody might actually be shown: "
        "**why did it say that about *me*?**",
        "E-s4"))

    cells.append(md("### 4.1 The standard views", "E-4-1-md"))
    cells.append(code(
        "final_model = train_model('gradient_boosting', X_train, y_train)\n"
        "probability = final_model.predict_proba(X_test)[:, 1]\n"
        "predicted = (probability >= 0.5).astype(int)\n"
        "final_metrics = evaluate(final_model, X_test, y_test)\n\n"
        "plots.plot_confusion(y_test, predicted, labels=('no diagnosis', 'diagnosed'),\n"
        "                     title='Held-out participants')\n"
        "plt.show()\n"
        "plots.plot_roc_pr(y_test, probability, title='Predicting a future dementia diagnosis')\n"
        "plt.show()\n"
        "plots.plot_calibration(y_test, probability)\n"
        "plt.show()\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "E-4-1"))
    cells.append(md(
        "**Calibration matters more than usual here.** Nobody acts on \"you are in the high-risk group\"; they "
        "act on \"your ten-year risk is about 18%\". If the model says 18% and the true rate among such people "
        "is 40%, the number is not just imprecise — it is misleading in a way that changes decisions about "
        "wills, driving, and care.",
        "E-4-1-read"))

    cells.append(md(
        "### 4.2 Shapley values — why did it say that about this person?\n\n"
        "A risk score is only usable in a consultation if you can say what drove it. **Shapley values** do "
        "exactly that, and they come with a guarantee no other method offers: each person's contributions "
        "**add up exactly** to their prediction.\n\n"
        "The idea is borrowed from cooperative game theory. Imagine the eight risk factors as players who "
        "join a team one at a time; each one's Shapley value is its average contribution to the final "
        "prediction, over every possible joining order. With eight features that is all 2⁸ = 256 subsets, "
        "which is small enough to compute **exactly** — the widely used `shap` package approximates this "
        "because real models have hundreds of features.\n\n"
        "⏱ This cell takes a few seconds.",
        "E-4-2-md"))
    cells.append(code(
        "from interpret import shapley_values, shapley_importance, baseline_prediction\n\n"
        "shap_frame = shapley_values(final_model, X_test.head(80), X_train, features=predictors)\n"
        "average_risk = baseline_prediction(final_model, X_train)\n\n"
        "# (a) Globally — which factors move this model's predictions the most?\n"
        "importance = shapley_importance(shap_frame)\n"
        "plots.plot_importance(importance.index, importance.values,\n"
        "                      title='Average influence on predicted dementia risk (exact Shapley values)',\n"
        "                      xlabel='mean |contribution| to predicted probability')\n"
        "plt.show()\n\n"
        "# (b) A beeswarm-style view: every person, every feature, coloured by whether the value was high.\n"
        "fig, ax = plt.subplots(figsize=(8, 4.6))\n"
        "order = importance.index[::-1]\n"
        "for position, feature in enumerate(order):\n"
        "    contributions = shap_frame[feature].to_numpy()\n"
        "    values = X_test.head(80)[feature].to_numpy().astype(float)\n"
        "    spread = np.linspace(-0.18, 0.18, len(contributions))\n"
        "    scatter = ax.scatter(contributions, position + spread, c=values, cmap='coolwarm', s=18, alpha=0.85)\n"
        "ax.axvline(0, color='black', linewidth=0.8)\n"
        "ax.set_yticks(range(len(order)), order, fontsize=9)\n"
        "ax.set_xlabel('contribution to this person\\'s predicted risk')\n"
        "ax.set_title('Every held-out person, every factor. Colour = that person\\'s value (blue low, red high).')\n"
        "fig.colorbar(scatter, ax=ax, shrink=0.8, label='feature value')\n"
        "plt.tight_layout(); plt.show()",
        "E-4-2"))

    cells.append(md(
        "### 4.3 ✏️ Your turn — explain one person\n\n"
        "This is the figure you would actually put in front of somebody. Change `PERSON` and read their story.",
        "E-4-3-md"))
    cells.append(code(
        turn(
            "Try several values of PERSON (0 to 79). Look for:\n"
            "  - somebody the model thought was high risk\n"
            "  - somebody it got WRONG (the printout tells you)\n"
            "For each, read the bars as a sentence: 'their risk was pushed up\n"
            "mainly by ___, and pulled down by ___'.",
            "PERSON = 0",
        ) + "\n\n"
        "contributions = shap_frame.iloc[PERSON].sort_values()\n"
        "plots.plot_importance(contributions.index, contributions.values,\n"
        "                      title=f'Person {X_test.index[PERSON]}: what drove their predicted risk',\n"
        "                      xlabel='contribution to predicted probability (blue = raises risk)')\n"
        "plt.show()\n\n"
        "print('Their actual characteristics:')\n"
        "print(X_test.iloc[PERSON].to_string())\n"
        "print()\n"
        "print(f'  cohort average risk        {average_risk:.3f}')\n"
        "print(f'  + their contributions      {contributions.sum():+.3f}')\n"
        "print(f'  = predicted risk           {average_risk + contributions.sum():.3f}')\n"
        "print(f'  (model actually says       {probability[PERSON]:.3f})')\n"
        "print(f'\\n  What really happened: {\"diagnosed\" if y_test.iloc[PERSON] == 1 else \"not diagnosed\"} '\n"
        "      f'during follow-up.')",
        "E-4-3"))
    cells.append(thinking(
        "Shapley values tell you what the *model* used. Do they tell you what *causes* dementia?",
        "No, and conflating the two is the most common misuse of interpretability tools. A Shapley value says "
        "\"the model's prediction moved by this much because of this feature\". If the model learned a "
        "confounded association — say, that people with less education are diagnosed more often, partly "
        "because cognitive tests are calibrated on the better educated — then the Shapley plot will faithfully "
        "report that confounded association as an important feature. Interpretability makes a model "
        "*transparent*, not *correct*. Module D is the antidote.",
        "E-4-3-think"))

    cells.append(md(
        "### 4.4 Who does this model fail?",
        "E-4-4-md"))
    cells.append(code(
        "check = X_test.copy()\n"
        "check['correct'] = (predicted == y_test).astype(int)\n"
        "check['sex'] = df.loc[X_test.index, 'sex']\n"
        "check['age_band'] = pd.cut(check['age_baseline'], [54, 65, 72, 80, 95],\n"
        "                           labels=['55-65', '65-72', '72-80', '80+'])\n"
        "check['education_group'] = np.where(check['education_years'] >= 13, '13+ years', 'under 13')\n\n"
        "for subgroup in ['sex', 'age_band', 'education_group', 'apoe4_dose']:\n"
        "    plots.plot_subgroup_errors(check.dropna(subset=[subgroup]), subgroup, 'correct',\n"
        "                               title=f'Proportion correct by {subgroup}')\n"
        "    plt.show()",
        "E-4-4"))

    cells.append(md(
        "### 4.5 Your headline result\n\n"
        "For your own notes. No shared scoreboard.",
        "E-4-5-md"))
    cells.append(code(
        "plots.plot_score_comparison(list(final_metrics), list(final_metrics.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title='Module E — gradient boosting on baseline risk factors',\n"
        "                            ylabel='score')\n"
        "plt.show()\n"
        "print(f'Trained on {len(X_train)} participants, tested on {len(X_test)} unseen ones.')\n"
        "print('Top three factors by Shapley importance:', ', '.join(importance.index[:3]))\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "E-4-5"))

    cells.append(md(
        "### 4.6 What would have to be true before this touched a patient?\n\n"
        "1. **The cohort is simulated.** The hazard ratios were put there by us, from published estimates. "
        "Nothing here is new evidence about dementia risk.\n"
        "2. **Association is not causation, and this notebook cannot bridge that gap.** Section 2 shows three "
        "distinct ways an observational cohort produces a confident, wrong causal claim.\n"
        "3. **A risk score is not a diagnosis.** Telling a healthy 68-year-old they have a 20% ten-year risk "
        "has real consequences — insurance, employment, how their family treats them — and there is currently "
        "no treatment that changes that number much.\n"
        "4. **Who was recruited?** Cohort studies over-recruit the healthy, the educated and the willing. "
        "Risk models built on them systematically misestimate risk for everyone else — and the modifiable "
        "risk factors here (hypertension, diabetes, education, physical activity) are precisely the ones "
        "distributed most unequally along lines of income and race. A model that quantifies those factors "
        "accurately will also reproduce those inequalities in its outputs.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "The Lancet Commission estimates roughly 40% of dementia cases are associated with modifiable risk "
        "factors. **Given the models you built today, would you rather have a good prediction model, or a "
        "good public-health intervention?** What is each one *for*?",
        "E-4-6"))

    cells.append(go_further(
        "E-4-further",
        "in 4.3, find a person the model got wrong and read their Shapley plot to see what misled it.",
        "restrict the model to only the *modifiable* factors (drop age and APOE) and see how much predictive "
        "power is left. That number is roughly the ceiling on what prevention advice can achieve.",
        "install `shap` and compare its `TreeExplainer` output with our exact values on the same model. "
        "How close is the approximation, and how much faster is it?",
    ))

    return cells, solutions


# =============================================================================
# Module F — genetics
# =============================================================================

def build_F():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "F", "Genetics",
        "How much of Alzheimer's risk can we read off the genome?",
        [
            "read a GWAS Catalog table: risk allele, odds ratio, p-value, mapped gene",
            "explain why genetics uses p < 5×10⁻⁸ instead of p < 0.05",
            "build a **polygenic risk score** by hand, from published effect sizes",
            "explain why an AUROC of 0.65 is a *good* result in this field, not a failure",
            "state clearly why a polygenic score built in one population transfers badly to another",
        ],
        "**Real effects, simulated people.** The variant table is the genuine **GWAS Catalog** record for "
        "Alzheimer's disease: 24 real risk variants with their real risk alleles, real allele frequencies, "
        "real odds ratios and real p-values, downloaded from EMBL-EBI. *APOE* is in there, with the largest "
        "effect, exactly as it should be.\n\n"
        "The **genotypes** are simulated. Individual-level AD genotype data is access-controlled everywhere, "
        "so each of our 1200 participants had their alleles drawn from the real published frequencies and "
        "their disease status drawn from the real published odds ratios. If the model recovers the "
        "literature, that is because the literature is what generated it — the point is the method.",
        "Skim section 2, then do 3.2 (build the score) and section 4.",
        warning="Real published variant effects; simulated genotypes. Section 1 explains which is which.",
    ))
    cells.append(setup_cell("F"))

    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "Two tables. One is a summary of the published literature; the other is our simulated cohort.",
        "F-s1"))
    cells.append(md(
        "### 1.1 The real variant table\n\n"
        "This is what a **genome-wide association study (GWAS)** produces. Researchers genotype hundreds of "
        "thousands of people, test every common variant in the genome for association with the disease, and "
        "publish the ones that survive.\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| `rsid` | The variant's catalogue number, e.g. `rs429358`. |\n"
        "| `gene` | The nearest or most plausible gene. **Nearest ≠ causal.** |\n"
        "| `risk_allele` | Which of the two DNA letters at that position carries the risk. |\n"
        "| `risk_allele_freq` | How common that letter is in the studied population. |\n"
        "| `odds_ratio` | How much one copy multiplies the odds of disease. |\n"
        "| `p_value` | Evidence against 'this variant has no effect'. |\n"
        "| `log_odds` | log(odds ratio) — the weight we use to build the score in section 3. |",
        "F-1-1-md"))
    cells.append(code(
        "df = load_data('F')\n"
        "variants = load_extra('F')['variants']\n\n"
        "print(f'{len(variants)} real risk variants from the GWAS Catalog.')\n"
        "print(f'{len(df)} simulated participants, {(df.diagnosis == \"AD\").mean():.0%} of them cases.\\n')\n"
        "display(variants[['rsid', 'gene', 'risk_allele', 'risk_allele_freq', 'odds_ratio', 'p_value']].head(12))",
        "F-1-1"))

    cells.append(md(
        "### 1.2 The shape of genetic risk\n\n"
        "**Predict before you run:** *APOE* is famous. Will the other 23 variants have effects roughly as big, "
        "or much smaller?",
        "F-1-2-md"))
    cells.append(code(
        "ordered = variants.sort_values('odds_ratio', ascending=False)\n"
        "plots.plot_importance(ordered['gene'] + ' (' + ordered['rsid'] + ')', ordered['odds_ratio'] - 1.0,\n"
        "                      title='Effect size of each real AD risk variant',\n"
        "                      xlabel='odds ratio minus 1 (0 = no effect)')\n"
        "plt.show()\n\n"
        "print('Note the scale. APOE roughly triples the odds. Most of the rest change them by 10-20%.')\n"
        "print('That is what \"polygenic\" means: hundreds of tiny effects, not a handful of big ones.')",
        "F-1-2"))

    cells.append(md(
        "### 1.3 Why p < 5×10⁻⁸?\n\n"
        "A genome-wide scan tests roughly a million independent positions. At the usual p < 0.05, **50,000 "
        "variants would pass by pure chance** — every single one a false discovery.\n\n"
        "The genetics field's fix is a Bonferroni correction for a million tests: 0.05 / 10⁶ = 5×10⁻⁸. Every "
        "variant in our table clears it. This is not statistical pedantry: it is the reason genetics stopped "
        "producing irreproducible 'candidate gene' findings in the 2000s and started producing results that "
        "replicate.",
        "F-1-3-md"))
    cells.append(code(
        "rng = np.random.default_rng(0)\n"
        "n_tests = 1_000_000\n"
        "null_p = rng.uniform(size=n_tests)   # a million variants with NO real effect at all\n\n"
        "fig, ax = plt.subplots(figsize=(7, 3.8))\n"
        "ax.bar(['p < 0.05', 'p < 5e-8'], [(null_p < 0.05).sum(), max((null_p < 5e-8).sum(), 0)],\n"
        "       color=['#c0392b', '#2c6fbb'])\n"
        "ax.set_yscale('symlog')\n"
        "ax.set_ylabel('false discoveries (log scale)')\n"
        "ax.set_title('One million variants, none of them real. How many would you \"find\"?')\n"
        "for index, count in enumerate([(null_p < 0.05).sum(), (null_p < 5e-8).sum()]):\n"
        "    ax.text(index, count, f'  {count:,}', ha='center', va='bottom', fontsize=10)\n"
        "plt.tight_layout(); plt.show()",
        "F-1-3"))

    cells.append(md(
        "### 1.4 ✏️ Your turn — one variant at a time\n\n"
        "`0`, `1` or `2` in a genotype column means how many copies of the risk allele that person carries.",
        "F-1-4-md"))
    cells.append(code(
        turn(
            "Change VARIANT to any rsid from the table above.\n"
            "Try rs429358 (APOE) first, then one of the weaker ones.\n"
            "Ask: could you diagnose anybody from this one variant?",
            "VARIANT = 'rs429358'",
        ) + "\n\n"
        "info = variants[variants.rsid == VARIANT].iloc[0]\n"
        "print(f\"{VARIANT} — near {info['gene']}, risk allele {info['risk_allele']}, \"\n"
        "      f\"published odds ratio {info['odds_ratio']:.2f}\\n\")\n\n"
        "rates = 100 * df.groupby(VARIANT)['diagnosis'].apply(lambda values: (values == 'AD').mean())\n"
        "counts = df.groupby(VARIANT).size()\n"
        "plots.plot_score_comparison([f'{dose} copies\\n(n={counts[dose]})' for dose in rates.index],\n"
        "                            rates.tolist(), colours=['#2c6fbb'] * len(rates),\n"
        "                            reference=100 * (df.diagnosis == 'AD').mean(),\n"
        "                            title=f'Percentage with AD, by number of {VARIANT} risk alleles',\n"
        "                            ylabel='percent with AD')\n"
        "plt.show()\n"
        "print('Dashed line = the cohort average. Even for APOE, plenty of carriers are unaffected')\n"
        "print('and plenty of non-carriers are affected. Genetic risk is a shift, not a verdict.')",
        "F-1-4"))

    cells.append(go_further(
        "F-1-further",
        "compare rs429358 (APOE) with any variant near the bottom of the effect-size plot.",
        "plot the number of risk alleles a person carries in total against their diagnosis rate. That plot is "
        "the whole idea of a polygenic score, before any weighting.",
        "look up *APOE* ε2, ε3 and ε4 — the gene has three common forms, and ε2 is *protective*. Our binary "
        "coding hides that. How would you encode it properly?",
    ))

    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "Genetics has its own characteristic failure modes.",
        "F-s2"))
    cells.append(md(
        "### 2.1 Population stratification\n\n"
        "Allele frequencies differ between ancestry groups for reasons that have nothing to do with disease. "
        "If your cases and controls are drawn from populations in different proportions, **every variant that "
        "differs in frequency between those populations looks associated with the disease**. This is the "
        "oldest and most dangerous artefact in genetic epidemiology.\n\n"
        "Our cohort deliberately contains two groups with slightly shifted frequencies, so you can see the effect.",
        "F-2-1-md"))
    cells.append(code(
        "print(df.groupby('ancestry')['diagnosis'].value_counts(normalize=True).round(3))\n"
        "print()\n\n"
        "genotype_columns = [column for column in df.columns if column.startswith('rs')]\n"
        "difference = (df[df.ancestry == 'reference'][genotype_columns].mean()\n"
        "              - df[df.ancestry == 'underrepresented'][genotype_columns].mean())\n\n"
        "plots.plot_importance(difference.index, difference.values,\n"
        "                      title='Difference in average risk-allele count between the two ancestry groups',\n"
        "                      xlabel='mean dose difference (reference minus underrepresented)')\n"
        "plt.show()\n"
        "print('These differences are ancestry, not disease. A model cannot tell them apart on its own.')",
        "F-2-1"))

    cells.append(thinking(
        "Could you fix population stratification by simply adding `ancestry` as a feature to the model?",
        "It helps the *prediction*, and it does not fix the *science*. Adding ancestry lets the model stop "
        "confusing group membership with disease, so the score improves. But the published effect sizes we "
        "used as weights were themselves estimated in a mostly European cohort, so they may be wrong "
        "elsewhere — and no amount of adjustment inside our cohort can repair a weight that was measured in "
        "a different population.\n\n"
        "Real GWAS handle this with **principal components of genome-wide genotype**, included as covariates: "
        "a continuous, data-driven summary of ancestry rather than a self-reported label. That controls the "
        "artefact well. It still does not make a European-derived score transferable, which is the point of "
        "section 3.4.",
        "F-2-1-think"))

    cells.append(md(
        "### 2.2 ✏️ Your turn — what \"nearest gene\" hides\n\n"
        "GWAS finds *positions*, not genes. The `gene` column is usually just whatever gene is closest, and "
        "the causal variant may act on something else entirely — sometimes hundreds of kilobases away. The "
        "textbook example is *FTO* and obesity, where the signal turned out to regulate *IRX3*, a different gene.\n\n"
        "This cell just prints the table sorted however you like — a reminder to read the columns critically.",
        "F-2-2-md"))
    cells.append(code(
        turn(
            "Sort by different columns and look at what changes:\n"
            "  'p_value'          -> strongest statistical evidence\n"
            "  'odds_ratio'       -> biggest biological effect\n"
            "  'risk_allele_freq' -> how many people carry it\n"
            "Do the same variants come top under all three? Which ranking\n"
            "would a drug company use, and which would a clinician?",
            "SORT_BY = 'p_value'\n"
            "ASCENDING = True",
        ) + "\n\n"
        "display(variants.sort_values(SORT_BY, ascending=ASCENDING)[\n"
        "    ['rsid', 'gene', 'risk_allele', 'risk_allele_freq', 'odds_ratio', 'p_value', 'reported_trait']].head(12))\n\n"
        "plots.plot_scatter(variants['risk_allele_freq'], variants['odds_ratio'],\n"
        "                   xlabel='how common the risk allele is', ylabel='odds ratio',\n"
        "                   title='Common variants have small effects; that is not a coincidence')\n"
        "plt.show()\n"
        "print('Strong-effect variants get selected against over evolutionary time, so they stay rare.')\n"
        "print('Common variants survive precisely because their effects are small. Hence: polygenic.')",
        "F-2-2"))

    cells.append(md(
        "### 2.3 QC verdict\n\n"
        "**Usable, with the field's standing caveats.** Ancestry is in the table and must be either adjusted "
        "for or reported. The gene labels are approximate. And the whole enterprise is calibrated on people "
        "of European ancestry, which section 4 makes concrete.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "F-2-verdict"))

    cells.append(md(
        "---\n# 3 · Build a polygenic risk score\n\n"
        "A **polygenic risk score (PRS)** is one of the simplest useful models in all of biomedicine: for each "
        "variant, multiply how many risk alleles you carry by the published log-odds, and add it all up.\n\n"
        "    PRS = Σ  (number of risk alleles)  ×  log(odds ratio)\n\n"
        "That is it. No training, no fitting — the weights come from the published literature. We build it by "
        "hand so you can see there is no magic in it.",
        "F-s3"))
    cells += express_catchup("F", "df = load_data('F')\nvariants = load_extra('F')['variants']\nprint(f'{len(variants)} real GWAS variants, {len(df)} simulated participants. Ready for section 3.')")

    cells.append(md("### 3.1 The simplest model — count APOE alleles", "F-3-1-md"))
    cells.append(code(
        "y = (df['diagnosis'] == 'AD').astype(int)\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(df[['rs429358']], y)\n"
        "apoe_only = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)\n"
        "plots.plot_roc_pr(y_te, train_model('logistic', X_tr, y_tr).predict_proba(X_te)[:, 1],\n"
        "                  title='APOE alone')\n"
        "plt.show()\n"
        "print(f\"APOE alone: AUROC {apoe_only['auroc']:.3f}\")",
        "F-3-1"))

    cells.append(md(
        "### 3.2 ✏️ Your turn — build the score yourself\n\n"
        "Change how many variants go into the score and watch what it buys you. Adding weak variants helps a "
        "little and then stops helping — which is why real PRS use hundreds of thousands of variants and "
        "*still* only reach modest accuracy.",
        "F-3-2-md"))
    cells.append(code(
        turn(
            "Change N_VARIANTS and re-run. Try 1, 3, 10, 24.\n"
            "Also try INCLUDE_APOE = False to see what the *rest* of the\n"
            "genome contributes once the famous gene is removed.",
            "N_VARIANTS = 24\n"
            "INCLUDE_APOE = True",
        ) + "\n\n"
        "chosen = variants.sort_values('p_value')\n"
        "if not INCLUDE_APOE:\n"
        "    chosen = chosen[~chosen.gene.isin(['APOE', 'TOMM40', 'NECTIN2', 'APOC1'])]\n"
        "chosen = chosen.head(N_VARIANTS)\n\n"
        "# The polygenic score, written out in full. This is the entire method.\n"
        "score = np.zeros(len(df))\n"
        "for _, variant in chosen.iterrows():\n"
        "    score += df[variant['rsid']].to_numpy() * variant['log_odds']\n"
        "df['prs'] = score\n\n"
        "print(f'Score built from {len(chosen)} variants: {\", \".join(chosen.gene.head(6))}...\\n')\n\n"
        "plots.plot_by_group(df, 'prs', 'diagnosis',\n"
        "                    title=f'Polygenic risk score from {len(chosen)} variants — note the overlap')\n"
        "plt.show()\n\n"
        "# Risk by decile of the score: the plot that gets shown to patients.\n"
        "decile = pd.qcut(df['prs'], 10, labels=False, duplicates='drop')\n"
        "risk_by_decile = 100 * df.assign(decile=decile).groupby('decile')['diagnosis'].apply(\n"
        "    lambda values: (values == 'AD').mean())\n"
        "plots.plot_score_comparison([f'{int(d) + 1}' for d in risk_by_decile.index], risk_by_decile.tolist(),\n"
        "                            colours=['#2c6fbb'] * len(risk_by_decile),\n"
        "                            reference=100 * y.mean(),\n"
        "                            title='Percentage with AD, by tenth of the polygenic score',\n"
        "                            ylabel='percent with AD')\n"
        "plt.show()\n\n"
        "X_tr, X_te, y_tr, y_te = split_data(df[['prs']], y)\n"
        "prs_metrics = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)\n"
        "print(f\"PRS from {len(chosen)} variants: AUROC {prs_metrics['auroc']:.3f}\")",
        "F-3-2"))

    cells.append(md(
        "### 3.3 The ladder\n\n"
        "Four models, from a single gene to everything we have.",
        "F-3-3-md"))
    cells.append(code(
        "genotype_columns = [column for column in df.columns if column.startswith('rs')]\n"
        "ladder = {\n"
        "    'APOE only': df[['rs429358']],\n"
        "    'PRS only': df[['prs']],\n"
        "    'PRS + age + sex': df[['prs', 'age', 'sex']],\n"
        "    'all 24 variants + age + sex': df[genotype_columns + ['age', 'sex']],\n"
        "    'age + sex only': df[['age', 'sex']],\n"
        "}\n"
        "scores = {}\n"
        "for name, table in ladder.items():\n"
        "    X_tr, X_te, y_tr, y_te = split_data(table, y)\n"
        "    scores[name] = evaluate(train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_score_comparison(list(scores), list(scores.values()), reference=0.5,\n"
        "                            colours=['#8a8a8a', '#2c6fbb', '#2c6fbb', '#2c6fbb', '#e08214'],\n"
        "                            title='Genetic risk models — read the y-axis carefully',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()\n"
        "for name, value in scores.items():\n"
        "    print(f'  {name:<30s} {value:.3f}')",
        "F-3-3"))
    cells.append(thinking(
        "The best model here reaches an AUROC in the low 0.7s. In module C the blood test reached 0.9. Is genetics just worse?",
        "It is answering a **completely different question**, and 0.7 is a strong result for it. A blood "
        "biomarker measures pathology *that is already happening in the brain of a person who came to a memory "
        "clinic*. A polygenic score is measured at birth, decades before anything happens, in someone with no "
        "symptoms at all. Predicting a lifetime outcome from a genome is a far harder problem — real published "
        "AD polygenic scores reach AUROC around 0.65–0.75 including *APOE*, and the field considers that "
        "genuinely useful for stratifying trial recruitment. **Judge a score against what the alternative was, "
        "not against another module.**",
        "F-3-3-think"))

    cells.append(md(
        "### 3.4 🔵 Your turn to write code — does the score transfer?\n\n"
        "The most important equity question in modern genetics. Our PRS weights come from studies conducted "
        "overwhelmingly in people of European ancestry. Allele frequencies and linkage patterns differ "
        "between populations, so the same weights do not carry the same meaning elsewhere.\n\n"
        "Fill in the `# TODO`: score the two ancestry groups separately.",
        "F-3-4-md"))
    cells.append(code(
        "# TODO (🔵): compute the PRS-only AUROC separately within each ancestry group.\n"
        "#   1. loop over df.groupby('ancestry')\n"
        "#   2. inside each group, split_data on group[['prs']] and the group's AD indicator\n"
        "#   3. store the AUROC in transfer[name]\n"
        "transfer = {}\n\n"
        "if transfer:\n"
        "    plots.plot_score_comparison(list(transfer), list(transfer.values()), reference=0.5,\n"
        "                                colours=['#2c6fbb', '#c0392b'],\n"
        "                                title='The same polygenic score, evaluated in two populations',\n"
        "                                ylabel='AUROC')\n"
        "    plt.show()\n"
        "else:\n"
        "    print('Fill in the TODO above. The solutions notebook has a worked version.')",
        "F-3-4"))
    solutions["F-3-4"] = (
        "# ✅ Worked solution.\n"
        "transfer = {}\n"
        "for name, group in df.groupby('ancestry'):\n"
        "    target = (group['diagnosis'] == 'AD').astype(int)\n"
        "    X_tr, X_te, y_tr, y_te = split_data(group[['prs']], target)\n"
        "    transfer[f'{name}\\n(n={len(group)})'] = evaluate(\n"
        "        train_model('logistic', X_tr, y_tr), X_te, y_te)['auroc']\n\n"
        "plots.plot_score_comparison(list(transfer), list(transfer.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb', '#c0392b'],\n"
        "                            title='The same polygenic score, evaluated in two populations',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()\n\n"
        "# Two things to notice, and the second is the important one.\n"
        "#\n"
        "# First, the underrepresented group's score is usually lower AND much noisier, because there\n"
        "# are fewer of them. In our simulation the gap is modest; in reality it is often severe -\n"
        "# published work finds European-derived AD polygenic scores lose a large share of their\n"
        "# predictive accuracy in African-ancestry cohorts.\n"
        "#\n"
        "# Second, and worse: the smaller group also gets a wider error bar, so you cannot even\n"
        "# reliably measure how badly the score is doing for them. Under-representation degrades\n"
        "# both the tool and our ability to audit it. That is why 'we validated it and it was fine'\n"
        "# is not reassuring when the validation cohort was 95% European.\n"
        "#\n"
        "# The fix is not statistical. It is recruiting diverse cohorts in the first place."
    )

    cells.append(go_further(
        "F-3-further",
        "in 3.2 set `INCLUDE_APOE = False` and see how much of the genetic signal was one gene.",
        "complete 3.4, then repeat it for the full 24-variant model instead of the PRS.",
        "real PRS use hundreds of thousands of variants with shrinkage methods (LDpred, PRS-CS) that account "
        "for correlation between nearby variants. Read how one of them works.",
    ))

    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "Genetics results demand an unusually careful reading, because the temptation to over-interpret them "
        "is unusually strong.",
        "F-s4"))

    cells.append(md("### 4.1 The standard views", "F-4-1-md"))
    cells.append(code(
        "X = df[['prs', 'age', 'sex']]\n"
        "X_train, X_test, y_train, y_test = split_data(X, y)\n"
        "final_model = train_model('logistic', X_train, y_train)\n"
        "probability = final_model.predict_proba(X_test)[:, 1]\n"
        "predicted = (probability >= 0.5).astype(int)\n"
        "final_metrics = evaluate(final_model, X_test, y_test)\n\n"
        "plots.plot_confusion(y_test, predicted, labels=('no AD', 'AD'), title='PRS + age + sex')\n"
        "plt.show()\n"
        "plots.plot_roc_pr(y_test, probability, title='Polygenic risk model, held-out participants')\n"
        "plt.show()\n"
        "plots.plot_calibration(y_test, probability)\n"
        "plt.show()\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "F-4-1"))

    cells.append(md(
        "### 4.2 Shapley values — what is the score made of?\n\n"
        "Exact Shapley values on a small feature set, computed by enumerating all 2⁵ = 32 coalitions. "
        "Here they separate the genetic contribution from the demographic one.",
        "F-4-2-md"))
    cells.append(code(
        "from interpret import shapley_values, shapley_importance, baseline_prediction\n\n"
        "top_variants = variants.sort_values('p_value').head(4)['rsid'].tolist()\n"
        "explain_columns = ['age', 'prs'] + top_variants\n"
        "explain_frame = df[explain_columns]\n"
        "X_tr2, X_te2, y_tr2, y_te2 = split_data(explain_frame, y)\n"
        "explain_model = train_model('random_forest', X_tr2, y_tr2)\n\n"
        "shap_frame = shapley_values(explain_model, X_te2.head(60), X_tr2, features=explain_columns)\n"
        "importance = shapley_importance(shap_frame)\n"
        "plots.plot_importance(importance.index, importance.values,\n"
        "                      title='What drives the predicted risk (exact Shapley values)',\n"
        "                      xlabel='mean |contribution| to predicted probability')\n"
        "plt.show()\n\n"
        "PERSON = 0\n"
        "one = shap_frame.iloc[PERSON].sort_values()\n"
        "plots.plot_importance(one.index, one.values,\n"
        "                      title=f'Participant {X_te2.index[PERSON]}: what raised and lowered their risk',\n"
        "                      xlabel='contribution to predicted probability')\n"
        "plt.show()\n"
        "print(f'Cohort average risk {baseline_prediction(explain_model, X_tr2):.3f} '\n"
        "      f'{one.sum():+.3f} = {baseline_prediction(explain_model, X_tr2) + one.sum():.3f}')",
        "F-4-2"))

    cells.append(md(
        "### 4.3 ✏️ Your turn — where would you set the threshold?\n\n"
        "PRS are not used to diagnose. They are used to *stratify*: to decide who to invite into a prevention "
        "trial, or who to monitor more closely. That means picking a top slice of the distribution.",
        "F-4-3-md"))
    cells.append(code(
        turn(
            "TOP_PERCENT is how much of the population you would flag as high risk.\n"
            "Try 1, 5, 10, 25.\n"
            "For each: how many real future cases are inside your flagged group,\n"
            "and how many did you miss? This is exactly the trade-off a trial\n"
            "recruiter faces with a fixed budget.",
            "TOP_PERCENT = 10",
        ) + "\n\n"
        "cutoff = np.percentile(df['prs'], 100 - TOP_PERCENT)\n"
        "flagged = df['prs'] >= cutoff\n"
        "cases = df['diagnosis'] == 'AD'\n\n"
        "captured = (flagged & cases).sum() / cases.sum()\n"
        "enrichment = cases[flagged].mean() / cases.mean()\n\n"
        "fig, ax = plt.subplots(figsize=(7.5, 3.8))\n"
        "ax.hist([df.loc[~cases, 'prs'], df.loc[cases, 'prs']], bins=35, stacked=True,\n"
        "        color=['#cccccc', '#e08214'], label=['no AD', 'AD'])\n"
        "ax.axvline(cutoff, color='#c0392b', linewidth=2)\n"
        "ax.annotate(f'top {TOP_PERCENT}%', (cutoff, ax.get_ylim()[1] * 0.85),\n"
        "            xytext=(6, 0), textcoords='offset points', color='#c0392b', fontsize=9)\n"
        "ax.set_xlabel('polygenic risk score'); ax.set_ylabel('number of people')\n"
        "ax.set_title(f'Flagging the top {TOP_PERCENT}% captures {captured:.0%} of all cases')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n\n"
        "print(f'You would invite {flagged.sum()} of {len(df)} people.')\n"
        "print(f'Among them, {cases[flagged].mean():.1%} develop AD, versus {cases.mean():.1%} in the whole cohort.')\n"
        "print(f'That is a {enrichment:.2f}x enrichment — the number a trial designer actually cares about.')\n"
        "print(f'But you also missed {(cases & ~flagged).sum()} future cases who scored below the line.')",
        "F-4-3"))

    cells.append(md(
        "### 4.4 Does it work equally well for everybody?",
        "F-4-4-md"))
    cells.append(code(
        "check = df.loc[X_test.index].copy()\n"
        "check['correct'] = (predicted == y_test.to_numpy()).astype(int)\n"
        "check['age_band'] = pd.cut(check['age'], [54, 68, 76, 84, 96], labels=['<68', '68-76', '76-84', '84+'])\n\n"
        "for subgroup in ['ancestry', 'sex', 'age_band']:\n"
        "    plots.plot_subgroup_errors(check.dropna(subset=[subgroup]), subgroup, 'correct',\n"
        "                               title=f'Proportion correct by {subgroup}')\n"
        "    plt.show()",
        "F-4-4"))

    cells.append(md(
        "### 4.5 Your headline result",
        "F-4-5-md"))
    cells.append(code(
        "plots.plot_score_comparison(list(final_metrics), list(final_metrics.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title='Module F — polygenic score + age + sex, held-out participants',\n"
        "                            ylabel='score')\n"
        "plt.show()\n"
        "print(f'{len(variants)} real GWAS Catalog variants; {len(df)} simulated participants.')\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')\n"
        "print('\\nRemember: 0.70 here is a good result. Compare it to what you could have said')\n"
        "print('about the same person with no information at all, not to another module.')",
        "F-4-5"))

    cells.append(md(
        "### 4.6 What would have to be true before this touched a patient?\n\n"
        "1. **The genotypes are simulated.** The variant effects are real and published; the people are not.\n"
        "2. **A PRS is not a diagnosis and never becomes one.** Someone in the top 1% may well never develop "
        "dementia. Someone in the bottom 1% may. It shifts a probability.\n"
        "3. **Ancestry bias is not a technical footnote.** Around 80% of GWAS participants to date are of "
        "European ancestry. A score built from those studies works less well elsewhere — and, as 3.4 shows, "
        "the groups it works worst for are also the groups where we can least reliably measure how badly it "
        "works. Deploying such a score at scale would widen an existing health gap while looking objective.\n"
        "4. **There is no treatment to offer.** Risk information without an intervention is a burden, not a "
        "benefit. This is why *APOE* genotyping is not routinely offered outside research.\n"
        "5. **Genetic information is not only about the person tested.** It is about their siblings and "
        "children, who did not consent.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "You can be genotyped for about €50, once, forever. **Should everyone get an AD polygenic score at "
        "birth?** If not now, what would have to change first?",
        "F-4-6"))

    cells.append(go_further(
        "F-4-further",
        "in 4.3, pick the `TOP_PERCENT` you would use to recruit a prevention trial and justify it.",
        "combine the polygenic score with a biomarker-like feature and see whether they add to each other. "
        "(Genes and biomarkers measure different stages of the same process.)",
        "read about the ethics of returning *APOE* results to research participants — including the "
        "REVEAL study, which actually measured what happens to people who are told.",
    ))

    return cells, solutions


# =============================================================================
# Module G — brain transcriptomics
# =============================================================================

def build_G():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "G", "Brain transcriptomics",
        "Which genes differ in the Alzheimer's brain?",
        [
            "work with a dataset that has 2000 measurements and only 31 samples, and say why that is dangerous",
            "use **unsupervised** methods — PCA and clustering — to find structure with no labels at all",
            "run a differential-expression analysis with multiple-testing correction, and read a volcano plot",
            "watch a classifier reach 100% accuracy on noise, and understand exactly how",
            "explain why a 'downregulated neuronal gene' in AD tissue might mean no gene was regulated at all",
        ],
        "**Real human brain tissue.** This is **GEO GSE1297** (Blalock et al., PNAS 2004): microarray "
        "measurements from post-mortem **hippocampal CA1** tissue of 31 people, graded from Control through "
        "Incipient and Moderate to Severe Alzheimer's disease. Each sample carries its real MMSE score, real "
        "Braak stage, real neurofibrillary tangle count, real age, sex and post-mortem interval.\n\n"
        "We kept the 2000 most variable genes. Nothing is simulated. These are 31 real donated brains.",
        "Run section 1, then go to 3.1 (PCA) and 3.3 (differential expression) — those two carry the module.",
    ))
    cells.append(setup_cell("G"))

    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "**This module is different from every other one today.** There is no patient to classify. The output "
        "is a list of genes and a picture — a *hypothesis*, not a prediction.",
        "G-s1"))
    cells.append(md(
        "### 1.1 Two tables\n\n"
        "`load_data('G')` gives the expression matrix: **one row per brain, one column per gene**. "
        "`load_extra('G')['samples']` gives what we know about each donor.\n\n"
        "| Sample column | Meaning |\n|---|---|\n"
        "| `group` | Control / Incipient / Moderate / Severe — clinical severity at death. |\n"
        "| `mmse` | Last Mini-Mental State Examination before death. |\n"
        "| `braak_stage` | 0–6, how far tau tangles had spread through the brain at autopsy. The neuropathological gold standard. |\n"
        "| `nft_count` | Neurofibrillary tangle density in this tissue. |\n"
        "| `post_mortem_interval_h` | **Hours between death and tissue freezing.** RNA degrades. Remember this. |\n\n"
        "The expression values are log2 microarray intensities: roughly 4 means barely detectable, 14 means "
        "abundant.",
        "G-1-1-md"))
    cells.append(code(
        "expression = load_data('G').set_index('sample_id')\n"
        "samples = load_extra('G')['samples'].set_index('sample_id')\n"
        "samples = samples.loc[expression.index]\n\n"
        "print(f'Expression matrix: {expression.shape[0]} brains x {expression.shape[1]} genes')\n"
        "print(f'That is {expression.shape[1] // expression.shape[0]} times more measurements than samples.\\n')\n"
        "display(samples)",
        "G-1-1"))

    cells.append(md(
        "### 1.2 What p ≫ n means\n\n"
        "Statisticians write **p ≫ n**: many more variables (p = 2000 genes) than observations (n = 31 "
        "brains). It is the defining condition of molecular biology data, and it breaks intuitions built on "
        "ordinary datasets.\n\n"
        "Here is the consequence, in one figure: with 2000 genes and 31 samples, you can *always* find genes "
        "that separate any two groups perfectly — even groups you made up at random.",
        "G-1-2-md"))
    cells.append(code(
        "rng = np.random.default_rng(0)\n"
        "fake_label = rng.permutation([0] * 15 + [1] * 16)   # a meaningless coin-flip label\n\n"
        "real_label = (samples['group'] != 'Control').to_numpy().astype(int)\n"
        "values = expression.to_numpy()\n\n"
        "def best_separation(labels):\n"
        "    group_a, group_b = values[labels == 0], values[labels == 1]\n"
        "    spread = np.sqrt(group_a.var(axis=0) / len(group_a) + group_b.var(axis=0) / len(group_b)) + 1e-9\n"
        "    return np.abs(group_a.mean(axis=0) - group_b.mean(axis=0)) / spread\n\n"
        "fig, ax = plt.subplots(figsize=(7.5, 4))\n"
        "ax.hist(best_separation(real_label), bins=50, alpha=0.7, color='#2c6fbb', label='real AD vs control label')\n"
        "ax.hist(best_separation(fake_label), bins=50, alpha=0.7, color='#c0392b', label='a random made-up label')\n"
        "ax.set_xlabel('separation between the two groups (t-like statistic)')\n"
        "ax.set_ylabel('number of genes')\n"
        "ax.set_title('With 2000 genes, even a meaningless label finds \"good\" genes')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n\n"
        "print(f'Genes separating the REAL groups at t > 3:   {(best_separation(real_label) > 3).sum()}')\n"
        "print(f'Genes separating a RANDOM label at t > 3:    {(best_separation(fake_label) > 3).sum()}')\n"
        "print('\\nIf those two numbers are close, your \"discovery\" is arithmetic, not biology.')",
        "G-1-2"))

    cells.append(md(
        "### 1.3 ✏️ Your turn — look at one gene\n\n"
        "Some of these genes are famous in Alzheimer's research. Try them, and try a few you have never heard of.",
        "G-1-3-md"))
    cells.append(code(
        turn(
            "Change GENE and re-run. Genes worth trying if they are present:\n"
            "  'GFAP'  - astrocyte marker, goes UP as glia react to damage\n"
            "  'SNAP25', 'SYT1' - synaptic genes, go DOWN as synapses are lost\n"
            "  'APOE', 'CLU', 'MAPT', 'APP' - the classic AD genes\n"
            "  'XIST'  - expressed from the inactive X. Try it and see what it separates!\n"
            "The available genes are printed underneath if yours is missing.",
            "GENE = 'GFAP'",
        ) + "\n\n"
        "if GENE not in expression.columns:\n"
        "    print(f'{GENE} is not among the 2000 most variable genes. A few that are:')\n"
        "    print(', '.join(expression.columns[:40]))\n"
        "else:\n"
        "    frame = samples.copy()\n"
        "    frame[GENE] = expression[GENE].to_numpy()\n"
        "    plots.plot_by_group(frame, GENE, 'group', unit='(log2 intensity)',\n"
        "                        title=f'{GENE} expression by clinical severity')\n"
        "    plt.show()\n"
        "    plots.plot_scatter(frame['mmse'], frame[GENE], colour_by=frame['group'],\n"
        "                       xlabel='MMSE before death (30 = normal)', ylabel=f'{GENE} (log2)',\n"
        "                       title=f'{GENE} against how impaired the person was', legend_title='group')\n"
        "    plt.show()\n"
        "    correlation = np.corrcoef(frame['mmse'], frame[GENE])[0, 1]\n"
        "    print(f'Correlation with MMSE: {correlation:+.3f}   (n = 31 brains, so this is a noisy estimate)')",
        "G-1-3"))

    cells.append(go_further(
        "G-1-further",
        "try `'XIST'` in 1.3 and work out what it is actually separating. (Hint: check the `sex` column.)",
        "rank all 2000 genes by their correlation with MMSE and print the top 20. Do any of them appear in the "
        "differential-expression results later?",
        "GSE1297 measures whole tissue. Look up how single-nucleus RNA sequencing changed the picture — and "
        "what it costs.",
    ))

    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "Post-mortem tissue has failure modes that living-patient data does not.",
        "G-s2"))
    cells.append(md(
        "### 2.1 The technical confounds\n\n"
        "**Post-mortem interval** is how long the brain sat before freezing. RNA degrades in that window, "
        "unevenly across genes. If AD brains happened to have longer intervals — perhaps because those deaths "
        "occurred in nursing homes rather than hospitals — then 'degraded RNA' would masquerade as 'AD biology'.\n\n"
        "**Age** is the other one. AD donors are older. Age changes brain expression on its own.",
        "G-2-1-md"))
    cells.append(code(
        "samples['is_ad'] = (samples['group'] != 'Control').astype(int)\n"
        "for column, unit in [('post_mortem_interval_h', '(hours)'), ('age', '(years)'), ('braak_stage', '(0-6)')]:\n"
        "    plots.plot_by_group(samples.assign(status=np.where(samples.is_ad == 1, 'AD', 'control')),\n"
        "                        column, 'status', unit=unit,\n"
        "                        title=f'{column} in AD versus control donors')\n"
        "    plt.show()\n\n"
        "print(samples.groupby('is_ad')[['age', 'post_mortem_interval_h', 'braak_stage', 'mmse']].mean().round(2))\n"
        "print('\\nIf these differ between the groups, they are confounded with diagnosis.')",
        "G-2-1"))

    cells.append(md(
        "### 2.2 The biological confound — you are counting cells, not measuring regulation\n\n"
        "This is the deepest point in the module and it is easy to miss.\n\n"
        "A tissue sample is a **mixture** of neurons, astrocytes, microglia and oligodendrocytes. Bulk "
        "expression measures the average over that mixture. In an Alzheimer's hippocampus **there are fewer "
        "neurons** — they have died — and **more reactive glia**.\n\n"
        "So if a neuronal gene looks 'downregulated in AD', there are two completely different explanations:\n\n"
        "1. Each surviving neuron is expressing less of it — a *regulatory* change.\n"
        "2. Each surviving neuron expresses exactly as much as before, but there are fewer neurons in the "
        "tube — a *compositional* change.\n\n"
        "**Bulk data cannot distinguish these.** Many published 'AD gene signatures' are substantially "
        "measuring cell loss. Below we make the problem visible using marker genes.",
        "G-2-2-md"))
    cells.append(code(
        "markers = {\n"
        "    'neurons': ['SNAP25', 'SYT1', 'RBFOX3', 'NEFL', 'SYN1', 'STMN2'],\n"
        "    'astrocytes': ['GFAP', 'AQP4', 'S100B', 'SLC1A2', 'ALDH1L1'],\n"
        "    'microglia': ['AIF1', 'CD68', 'ITGAM', 'CSF1R', 'C1QB'],\n"
        "}\n"
        "available = {kind: [gene for gene in genes if gene in expression.columns]\n"
        "             for kind, genes in markers.items()}\n"
        "for kind, genes in available.items():\n"
        "    print(f'{kind}: found {len(genes)} marker gene(s) — {\", \".join(genes) if genes else \"none in the top 2000\"}')\n\n"
        "scores = pd.DataFrame({kind: expression[genes].mean(axis=1)\n"
        "                       for kind, genes in available.items() if genes})\n"
        "scores['status'] = np.where(samples['is_ad'].to_numpy() == 1, 'AD', 'control')\n\n"
        "for kind in [column for column in scores.columns if column != 'status']:\n"
        "    plots.plot_by_group(scores, kind, 'status', unit='(mean log2 of marker genes)',\n"
        "                        title=f'Average {kind} marker expression — a proxy for how many {kind} are in the tube')\n"
        "    plt.show()",
        "G-2-2"))
    cells.append(thinking(
        "The neuronal markers are lower in AD tissue. Have neuronal genes been switched off?",
        "You cannot tell from this data, and that is the honest answer. Fewer neurons in the sample produces "
        "exactly this figure, with no change in gene regulation at all. To separate the two you need either "
        "single-cell/single-nucleus sequencing (measure each cell separately) or computational "
        "**deconvolution** (estimate the mixture and adjust for it). Any bulk-tissue paper that claims a "
        "regulatory mechanism without addressing composition is making a claim its data cannot support.",
        "G-2-2-think"))

    cells.append(md(
        "### 2.3 QC verdict\n\n"
        "**Usable for hypothesis generation only.** Three caveats that go in every sentence we write about "
        "this data:\n\n"
        "1. n = 31. Every estimate is noisy, and the multiple-testing burden is severe.\n"
        "2. Post-mortem interval and age differ between groups and cannot be fully adjusted at this sample size.\n"
        "3. Cell-composition change is indistinguishable from regulatory change.\n\n"
        "And a fourth that is not a flaw but a limit: **this is end-stage tissue.** These brains are from "
        "people who died with advanced disease. Whatever we find came *after* decades of pathology, so "
        "nothing here can tell us about cause.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "G-2-verdict"))

    cells.append(md(
        "---\n# 3 · Unsupervised discovery\n\n"
        "In every other module today we told the algorithm the answer and asked it to learn the rule. Here we "
        "tell it **nothing** and ask whether it finds structure by itself. If the brains separate by "
        "diagnosis without ever being told the diagnosis, that is real evidence of a molecular difference.",
        "G-s3"))
    cells += express_catchup("G", "expression = load_data('G').set_index('sample_id')\nsamples = load_extra('G')['samples'].set_index('sample_id').loc[expression.index]\nsamples['is_ad'] = (samples['group'] != 'Control').astype(int)\nprint(f'{expression.shape[0]} brains x {expression.shape[1]} genes, '\n      f'{int(samples.is_ad.sum())} of them from donors with Alzheimer disease.')\nprint('Ready for section 3.')")

    cells.append(md(
        "### 3.1 PCA — 2000 dimensions squeezed into 2\n\n"
        "**Principal component analysis** finds the directions along which the samples differ most, and lets "
        "us plot 2000-dimensional data on a page. PC1 is the single biggest axis of variation between these "
        "brains — whatever it happens to be.\n\n"
        "**Predict before you run:** will PC1 line up with diagnosis? With age? With post-mortem interval? "
        "Nothing tells the algorithm which one to find.",
        "G-3-1-md"))
    cells.append(code(
        "from sklearn.decomposition import PCA\n"
        "from sklearn.preprocessing import StandardScaler\n\n"
        "scaled = StandardScaler().fit_transform(expression.to_numpy())\n"
        "pca = PCA(n_components=6, random_state=42).fit(scaled)\n"
        "coordinates = pca.transform(scaled)\n\n"
        "fig, ax = plt.subplots(figsize=(6.5, 3.4))\n"
        "ax.bar(range(1, 7), 100 * pca.explained_variance_ratio_, color='#2c6fbb')\n"
        "ax.set_xlabel('principal component'); ax.set_ylabel('percent of variation explained')\n"
        "ax.set_title('How much of the difference between brains each axis captures')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "for colour_column, label in [('group', 'clinical severity'), ('sex', 'sex'),\n"
        "                             ('post_mortem_interval_h', 'post-mortem interval'), ('braak_stage', 'Braak stage')]:\n"
        "    values = samples[colour_column]\n"
        "    if values.dtype.kind in 'if':\n"
        "        fig, ax = plt.subplots(figsize=(6.2, 4.4))\n"
        "        scatter = ax.scatter(coordinates[:, 0], coordinates[:, 1], c=values, cmap='viridis', s=70,\n"
        "                             edgecolor='white')\n"
        "        fig.colorbar(scatter, ax=ax, label=label)\n"
        "        ax.set_xlabel(f'PC1 ({100 * pca.explained_variance_ratio_[0]:.0f}% of variation)')\n"
        "        ax.set_ylabel(f'PC2 ({100 * pca.explained_variance_ratio_[1]:.0f}%)')\n"
        "        ax.set_title(f'31 brains, coloured by {label}')\n"
        "        plt.tight_layout()\n"
        "    else:\n"
        "        plots.plot_scatter(coordinates[:, 0], coordinates[:, 1], colour_by=values,\n"
        "                           xlabel=f'PC1 ({100 * pca.explained_variance_ratio_[0]:.0f}% of variation)',\n"
        "                           ylabel=f'PC2 ({100 * pca.explained_variance_ratio_[1]:.0f}%)',\n"
        "                           title=f'31 brains, coloured by {label}', legend_title=label)\n"
        "    plt.show()",
        "G-3-1"))
    cells.append(md(
        "**Whatever you see here is the finding.** If the groups separate along PC1, the molecular difference "
        "is the dominant source of variation between these brains. If they do not — if PC1 turns out to track "
        "sex, or post-mortem interval, or nothing recognisable — that is a *more* important result, because "
        "it tells you that any 'AD signature' extracted from this tissue is a minority of the variation and "
        "is competing with technical noise.",
        "G-3-1-read"))

    cells.append(md(
        "### 3.2 ✏️ Your turn — clustering without labels\n\n"
        "**k-means** splits the samples into `k` groups purely by similarity. It has never seen a diagnosis. "
        "If its groups line up with the clinical ones, that is genuine unsupervised discovery.",
        "G-3-2-md"))
    cells.append(code(
        turn(
            "Change these and re-run.\n"
            "  N_CLUSTERS: try 2, 3, 4. There are 4 clinical groups - does k=4 recover them?\n"
            "  N_GENES:    try 100, 500, 2000. Does using more genes help, or add noise?\n"
            "Look at the crosstab: perfect agreement would be one number per row.",
            "N_CLUSTERS = 2\n"
            "N_GENES = 2000",
        ) + "\n\n"
        "from sklearn.cluster import KMeans\n\n"
        "most_variable = expression.var().sort_values(ascending=False).index[:N_GENES]\n"
        "subset = StandardScaler().fit_transform(expression[most_variable].to_numpy())\n"
        "clusters = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10).fit_predict(subset)\n\n"
        "reduced = PCA(n_components=2, random_state=42).fit_transform(subset)\n"
        "plots.plot_scatter(reduced[:, 0], reduced[:, 1], colour_by=[f'cluster {c}' for c in clusters],\n"
        "                   xlabel='PC1', ylabel='PC2',\n"
        "                   title=f'k-means found {N_CLUSTERS} groups using {N_GENES} genes — no labels involved',\n"
        "                   legend_title='unsupervised cluster')\n"
        "plt.show()\n\n"
        "agreement = pd.crosstab(samples['group'], clusters)\n"
        "print('Rows = the real clinical group. Columns = what the algorithm decided.')\n"
        "display(agreement)\n\n"
        "purity = agreement.max(axis=1).sum() / agreement.to_numpy().sum()\n"
        "print(f'Cluster purity: {purity:.2f}  (1.0 would mean the clusters exactly match the clinical groups)')",
        "G-3-2"))

    cells.append(md(
        "### 3.3 Differential expression — which genes, specifically?\n\n"
        "Now a gene-by-gene test: for each of the 2000 genes, is its average different between AD and control "
        "brains? That is 2000 t-tests, so we **must** correct for multiple testing — at p < 0.05 we would "
        "expect 100 false positives from noise alone.\n\n"
        "We use the **Benjamini–Hochberg false discovery rate**: instead of controlling the chance of *any* "
        "false positive, it controls the *proportion* of your findings that are false. An FDR of 0.05 means "
        "\"about 5% of the genes on this list are wrong\", which is the right trade-off for hypothesis generation.",
        "G-3-3-md"))
    cells.append(code(
        "from scipy import stats\n\n"
        "ad_values = expression[samples['is_ad'] == 1].to_numpy()\n"
        "control_values = expression[samples['is_ad'] == 0].to_numpy()\n\n"
        "statistic, raw_p = stats.ttest_ind(ad_values, control_values, axis=0, equal_var=False)\n"
        "log_fold_change = ad_values.mean(axis=0) - control_values.mean(axis=0)   # already log2, so a difference IS a ratio\n\n"
        "# Benjamini-Hochberg, written out rather than imported, so you can see it.\n"
        "order = np.argsort(raw_p)\n"
        "ranks = np.arange(1, len(raw_p) + 1)\n"
        "adjusted = np.minimum.accumulate((raw_p[order] * len(raw_p) / ranks)[::-1])[::-1]\n"
        "fdr = np.empty_like(adjusted)\n"
        "fdr[order] = np.clip(adjusted, 0, 1)\n\n"
        "results = pd.DataFrame({'gene': expression.columns, 'log2_fold_change': log_fold_change,\n"
        "                        'p_value': raw_p, 'fdr': fdr}).sort_values('p_value')\n\n"
        "print(f'Genes with raw p < 0.05:      {(raw_p < 0.05).sum():4d}   <- of which ~{int(0.05 * len(raw_p))} are noise')\n"
        "print(f'Genes with FDR < 0.05:        {(fdr < 0.05).sum():4d}   <- the defensible list')\n"
        "print(f'Genes with FDR < 0.10:        {(fdr < 0.10).sum():4d}\\n')\n\n"
        "plots.plot_volcano(results['log2_fold_change'], results['fdr'], results['gene'].tolist(),\n"
        "                   alpha=0.05, top=14,\n"
        "                   title='Volcano plot: right = higher in AD, up = more certain')\n"
        "plt.show()\n"
        "display(results.head(15).round(4))",
        "G-3-3"))

    cells.append(thinking(
        "Why not just report the genes with raw p < 0.05, and mention the caveat in the discussion?",
        "Because with 2000 tests you expect about 100 of them to pass at p < 0.05 **when nothing is going "
        "on at all** — section 1.2 showed exactly that with a made-up label. A list of a hundred genes, of "
        "which a hundred could be noise, is not a finding with a caveat; it is a caveat with no finding.\n\n"
        "Benjamini–Hochberg changes what you are promising. Rather than *\"probably no false positives\"* "
        "(Bonferroni, which at n = 31 would leave you with nothing), it promises *\"about 5% of this list is "
        "wrong\"* — which is honest, achievable, and exactly the right guarantee when the output is a "
        "shortlist of hypotheses that somebody will now test at the bench.",
        "G-3-3-think"))

    cells.append(md(
        "### 3.4 ✏️ Your turn — the heatmap\n\n"
        "The classic transcriptomics figure. Each row is a gene, each column a brain, colour is expression "
        "relative to that gene's average.",
        "G-3-4-md"))
    cells.append(code(
        turn(
            "Change these and re-run.\n"
            "  N_TOP:    how many genes to show (try 15, 30, 60)\n"
            "  ORDER_BY: 'braak_stage', 'mmse', 'group' or 'post_mortem_interval_h'\n"
            "If the colour pattern lines up with the ordering, the genes track it.",
            "N_TOP = 30\n"
            "ORDER_BY = 'braak_stage'",
        ) + "\n\n"
        "top_genes = results.head(N_TOP)['gene'].tolist()\n"
        "column_order = samples.sort_values(ORDER_BY).index\n"
        "block = expression.loc[column_order, top_genes]\n"
        "z_scores = ((block - block.mean()) / block.std()).transpose()\n\n"
        "column_labels = [f\"{sample.split('GSM')[-1]} {samples.loc[sample, 'group'][:4]} \"\n"
        "                 f\"{ORDER_BY[:4]}={samples.loc[sample, ORDER_BY]}\" for sample in column_order]\n"
        "plots.plot_heatmap(z_scores.to_numpy(), top_genes, column_labels,\n"
        "                   title=f'Top {N_TOP} differentially expressed genes, brains ordered by {ORDER_BY}')\n"
        "plt.show()",
        "G-3-4"))

    cells.append(md(
        "### 3.5 The cautionary demonstration — a classifier that cannot fail\n\n"
        "Suppose you ignored everything in section 2 and trained a classifier on all 2000 genes. With 31 "
        "samples it will fit perfectly. Here is the point: **it fits perfectly on made-up labels too.**",
        "G-3-5-md"))
    cells.append(code(
        "from sklearn.model_selection import cross_val_score, StratifiedKFold\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.svm import SVC\n\n"
        "pipeline = Pipeline([('scale', StandardScaler()), ('svm', SVC(kernel='linear', C=1.0))])\n"
        "X_genes = expression.to_numpy()\n"
        "real_y = samples['is_ad'].to_numpy()\n"
        "fake_y = np.random.default_rng(1).permutation(real_y)   # same labels, shuffled: pure noise\n\n"
        "pipeline.fit(X_genes, real_y)\n"
        "training_accuracy = pipeline.score(X_genes, real_y)\n"
        "pipeline.fit(X_genes, fake_y)\n"
        "fake_training_accuracy = pipeline.score(X_genes, fake_y)\n\n"
        "folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)\n"
        "real_cv = cross_val_score(pipeline, X_genes, real_y, cv=folds, scoring='balanced_accuracy').mean()\n"
        "fake_cv = cross_val_score(pipeline, X_genes, fake_y, cv=folds, scoring='balanced_accuracy').mean()\n\n"
        "plots.plot_score_comparison(\n"
        "    ['real labels\\ntraining score', 'SHUFFLED labels\\ntraining score',\n"
        "     'real labels\\ncross-validated', 'SHUFFLED labels\\ncross-validated'],\n"
        "    [training_accuracy, fake_training_accuracy, real_cv, fake_cv],\n"
        "    colours=['#c0392b', '#c0392b', '#2c6fbb', '#2c6fbb'], reference=0.5,\n"
        "    title='2000 genes, 31 brains. The red bars are meaningless; only the blue ones are evidence.',\n"
        "    ylabel='balanced accuracy')\n"
        "plt.show()\n"
        "print('Both red bars are 1.00. A model that perfectly classifies random noise has')\n"
        "print('demonstrated nothing except that p >> n lets you draw a line anywhere.')",
        "G-3-5"))

    cells.append(md(
        "### 3.6 🔵 Your turn to write code — is the signal above chance?\n\n"
        "The honest way to test an unsupervised finding: a **permutation test**. Shuffle the labels many "
        "times, redo the analysis, and ask how often noise produces a result as good as yours.\n\n"
        "Fill in the `# TODO`.",
        "G-3-6-md"))
    cells.append(code(
        "# TODO (🔵): how many genes reach FDR < 0.05 when the labels are SHUFFLED?\n"
        "#   1. repeat 30 times: shuffle samples['is_ad'], redo the t-test, apply the same BH correction\n"
        "#   2. collect how many genes pass FDR < 0.05 each time\n"
        "#   3. compare that distribution with your real count\n"
        "\n"
        "def count_significant(labels, alpha=0.05):\n"
        "    a = expression[labels == 1].to_numpy()\n"
        "    b = expression[labels == 0].to_numpy()\n"
        "    _, p = stats.ttest_ind(a, b, axis=0, equal_var=False)\n"
        "    order = np.argsort(p)\n"
        "    ranks = np.arange(1, len(p) + 1)\n"
        "    adjusted = np.minimum.accumulate((p[order] * len(p) / ranks)[::-1])[::-1]\n"
        "    return int((np.clip(adjusted, 0, 1) < alpha).sum())\n\n"
        "real_count = count_significant(samples['is_ad'].to_numpy())\n"
        "null_counts = []   # TODO: fill this with 30 shuffled counts\n\n"
        "if null_counts:\n"
        "    fig, ax = plt.subplots(figsize=(7, 3.8))\n"
        "    ax.hist(null_counts, bins=15, color='#cccccc', label='shuffled labels (noise)')\n"
        "    ax.axvline(real_count, color='#c0392b', linewidth=2, label=f'real labels ({real_count} genes)')\n"
        "    ax.set_xlabel('genes passing FDR < 0.05'); ax.set_ylabel('how often')\n"
        "    ax.set_title('Permutation test: is the real finding outside the noise distribution?')\n"
        "    ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n"
        "    print(f'Empirical p-value: {(np.sum(np.array(null_counts) >= real_count) + 1) / (len(null_counts) + 1):.3f}')\n"
        "else:\n"
        "    print(f'Real analysis found {real_count} genes at FDR < 0.05.')\n"
        "    print('Fill in the TODO to find out whether that is more than noise would give.')",
        "G-3-6"))
    solutions["G-3-6"] = (
        "# ✅ Worked solution.\n"
        "def count_significant(labels, alpha=0.05):\n"
        "    a = expression[labels == 1].to_numpy()\n"
        "    b = expression[labels == 0].to_numpy()\n"
        "    _, p = stats.ttest_ind(a, b, axis=0, equal_var=False)\n"
        "    order = np.argsort(p)\n"
        "    ranks = np.arange(1, len(p) + 1)\n"
        "    adjusted = np.minimum.accumulate((p[order] * len(p) / ranks)[::-1])[::-1]\n"
        "    return int((np.clip(adjusted, 0, 1) < alpha).sum())\n\n"
        "real_count = count_significant(samples['is_ad'].to_numpy())\n"
        "generator = np.random.default_rng(7)\n"
        "labels = samples['is_ad'].to_numpy()\n"
        "null_counts = [count_significant(generator.permutation(labels)) for _ in range(30)]\n\n"
        "fig, ax = plt.subplots(figsize=(7, 3.8))\n"
        "ax.hist(null_counts, bins=15, color='#cccccc', label='shuffled labels (noise)')\n"
        "ax.axvline(real_count, color='#c0392b', linewidth=2, label=f'real labels ({real_count} genes)')\n"
        "ax.set_xlabel('genes passing FDR < 0.05'); ax.set_ylabel('how often')\n"
        "ax.set_title('Permutation test: is the real finding outside the noise distribution?')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n"
        "print(f'Empirical p-value: {(np.sum(np.array(null_counts) >= real_count) + 1) / (len(null_counts) + 1):.3f}')\n\n"
        "# Why this is the right test. The FDR correction already assumes a particular null model\n"
        "# (independent tests). Gene expression is emphatically NOT independent - genes in a pathway\n"
        "# rise and fall together - so the analytic FDR can be optimistic. A permutation test makes\n"
        "# no such assumption: it destroys the label-to-sample link while preserving every correlation\n"
        "# between genes, which is exactly the null hypothesis we care about.\n"
        "#\n"
        "# Read the histogram, not just the p-value. If the shuffled runs regularly return dozens of\n"
        "# 'significant' genes, then a list of dozens is not a discovery, whatever the FDR column says."
    )

    cells.append(go_further(
        "G-3-further",
        "in 3.4, set `ORDER_BY = 'post_mortem_interval_h'` and check whether the pattern also lines up with a purely technical variable.",
        "repeat the differential expression using **Braak stage** as a continuous variable (correlate each "
        "gene with Braak) rather than a binary AD/control split. Neuropathology is graded, not binary.",
        "take your top gene list to a free enrichment tool (Enrichr, g:Profiler, DAVID) and see which pathways "
        "come out. Then ask whether those pathways are neuronal, glial, or immune — and what that implies "
        "given section 2.2.",
    ))

    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "A discovery module's deliverable is **a gene list, a figure, and a carefully hedged sentence**. "
        "There is no accuracy score, and inventing one would misrepresent what was done.",
        "G-s4"))

    cells.append(md("### 4.1 Your findings", "G-4-1-md"))
    cells.append(code(
        "significant = results[results['fdr'] < 0.05]\n"
        "up = significant[significant['log2_fold_change'] > 0].head(10)\n"
        "down = significant[significant['log2_fold_change'] < 0].head(10)\n\n"
        "print(f'{len(significant)} genes differ at FDR < 0.05 between {int(samples.is_ad.sum())} AD '\n"
        "      f'and {int((1 - samples.is_ad).sum())} control hippocampi.\\n')\n\n"
        "combined = pd.concat([up, down])\n"
        "plots.plot_importance(combined['gene'], combined['log2_fold_change'],\n"
        "                      title='Top differentially expressed genes (blue = higher in AD)',\n"
        "                      xlabel='log2 fold change, AD versus control')\n"
        "plt.show()\n\n"
        "print('Higher in AD:', ', '.join(up['gene'].tolist()) or 'none')\n"
        "print('Lower in AD: ', ', '.join(down['gene'].tolist()) or 'none')",
        "G-4-1"))

    cells.append(md(
        "### 4.2 ✏️ Your turn — does your gene track severity, or just diagnosis?\n\n"
        "A gene that scales smoothly with Braak stage or MMSE is a much stronger candidate than one that "
        "merely differs between two crude groups.",
        "G-4-2-md"))
    cells.append(code(
        turn(
            "Pick any gene from your top list above.\n"
            "Then change AGAINST to 'braak_stage', 'mmse', 'nft_count'\n"
            "or 'post_mortem_interval_h'.\n"
            "A convincing candidate tracks the pathology AND NOT the\n"
            "post-mortem interval. Check both before you believe it.",
            "GENE_OF_INTEREST = results.iloc[0]['gene']\n"
            "AGAINST = 'braak_stage'",
        ) + "\n\n"
        "frame = samples.copy()\n"
        "frame['expression'] = expression[GENE_OF_INTEREST].to_numpy()\n"
        "plots.plot_scatter(frame[AGAINST], frame['expression'], colour_by=frame['group'],\n"
        "                   xlabel=AGAINST, ylabel=f'{GENE_OF_INTEREST} (log2 intensity)',\n"
        "                   title=f'{GENE_OF_INTEREST} against {AGAINST}', legend_title='clinical group')\n"
        "plt.show()\n\n"
        "usable = frame[[AGAINST, 'expression']].dropna()\n"
        "r, p = stats.pearsonr(usable[AGAINST], usable['expression'])\n"
        "print(f'{GENE_OF_INTEREST} vs {AGAINST}: r = {r:+.3f}, p = {p:.4f}  (n = {len(usable)} brains)')\n"
        "print('With 31 samples, treat any single correlation as a hint, not a result.')",
        "G-4-2"))

    cells.append(md(
        "### 4.3 What this module produced, and what it did not\n\n"
        "**What you can honestly say:**\n\n"
        "- A list of genes whose average expression differs between AD and control hippocampal tissue at a "
        "controlled false discovery rate.\n"
        "- A picture showing how much — or how little — of the total variation between these brains is "
        "explained by diagnosis.\n"
        "- A demonstration that a classifier on this data can reach perfect training accuracy on random labels.\n\n"
        "**What you cannot say:**\n\n"
        "- That any of these genes *causes* Alzheimer's disease. This is end-stage post-mortem tissue; "
        "everything observed came decades after the disease began.\n"
        "- That a gene was *regulated* up or down. It may simply reflect which cells survived (2.2).\n"
        "- That the finding will replicate. n = 31, and independent replication in transcriptomics is hard.\n\n"
        "**The honest framing** is the one this module exists to teach: *these genes are worth looking at next.* "
        "That is what discovery science produces. It is upstream of everything else in today's menu — the "
        "biomarkers in module C and the drug targets in module H exist because analyses like this pointed at "
        "them first.\n\n"
        "**Ethics.** These are 31 donated human brains. Consent for brain donation is given by the donor "
        "before death or by family after it, and covers research use — but donors could not have anticipated "
        "every future analysis. Cohorts like this also skew towards people connected to academic medical "
        "centres, which is its own kind of unrepresentativeness.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "Modules A–F all try to **predict** something about a patient. This one tries to **understand** "
        "something about a disease. **Which one is more useful?** And: if a drug company had to choose "
        "between funding a better diagnostic model and funding a study like this one, which should they pick?",
        "G-4-3"))

    cells.append(go_further(
        "G-4-further",
        "in 4.2, check your top gene against `post_mortem_interval_h` as well as `braak_stage`. Does it survive?",
        "adjust the differential expression for post-mortem interval by regressing it out of each gene first, "
        "then redo the t-tests. How many genes survive?",
        "compare your gene list with a published AD single-nucleus atlas and see which of your genes turn out "
        "to be markers of a cell type rather than a disease process.",
    ))

    return cells, solutions


# =============================================================================
# Module H — small-molecule chemistry
# =============================================================================

def build_H():
    cells, solutions = [], {}

    cells.append(intro_cell(
        "H", "Small-molecule chemistry",
        "Which molecules are worth making in the lab?",
        [
            "read a molecule's structure written as text (SMILES) and the numbers computed from it",
            "explain what BACE1 is and why it was one of the most-pursued drug targets in Alzheimer's research",
            "build models that predict whether a compound inhibits BACE1, from structure alone",
            "demonstrate **scaffold leakage** — the chemistry twin of the subject-leakage problem in imaging",
            "explain the gap between 'binds the target in a dish' and 'helps a patient'",
        ],
        "**Entirely real.** This is the **MoleculeNet BACE-1 benchmark**: 1513 real compounds with real "
        "measured binding affinities (pIC50) against human β-secretase 1, curated from published medicinal "
        "chemistry, distributed under the MIT licence. Each compound comes with its structure as a SMILES "
        "string and around 590 precomputed molecular descriptors, of which we keep the eleven most "
        "interpretable.\n\n"
        "*(One thing is computed by us: the `analogue_series` grouping, which stands in for a true chemical "
        "scaffold. Section 2 explains why it exists and what it approximates.)*",
        "Run section 1 quickly, then do section 2.3 (the leakage demo) and section 3 properly.",
    ))
    cells.append(setup_cell("H"))

    cells.append(md(
        "---\n# 1 · Understand the data\n\n"
        "### Why BACE1?\n\n"
        "The amyloid hypothesis says Alzheimer's begins when amyloid-β accumulates in the brain. Amyloid-β is "
        "cut out of a larger protein (APP) by two enzymes in sequence. **β-secretase 1 — BACE1 — makes the "
        "first cut.** Block BACE1 and, in principle, you stop amyloid-β being made at all.\n\n"
        "This made BACE1 one of the most intensively pursued drug targets in the history of neurology. "
        "Billions were spent. Potent, brain-penetrant BACE1 inhibitors were developed, and they worked: they "
        "cut amyloid-β production dramatically in humans.\n\n"
        "**Then the trials failed.** Verubecestat, lanabecestat, atabecestat — halted, one after another. "
        "Several showed patients on the drug declining *faster* than those on placebo. Whether that means "
        "the amyloid hypothesis is wrong, or the drugs were given too late, or BACE1 does something else "
        "essential we should not have blocked, is still argued.\n\n"
        "Hold both halves of that story. The model you build today is a real, useful tool for the step it "
        "addresses — and it would have been just as confident about the compounds that failed.",
        "H-s1"))

    cells.append(md(
        "### 1.1 The table\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| `smiles` | The molecule's structure, written as text. `c1ccccc1` is a benzene ring. |\n"
        "| `pic50` | Measured potency: −log₁₀ of the concentration needed to inhibit half the enzyme. **Higher = more potent.** 9 means nanomolar; 5 means barely active. |\n"
        "| `active` | 1 if pIC50 ≥ 7. This threshold is a convention, not a law of nature — see 2.1. |\n"
        "| `analogue_series` | Which family of near-identical molecules this belongs to. Computed by us. |\n"
        "| `mw` | Molecular weight (daltons). |\n"
        "| `alogp` | Calculated fat-solubility. Drugs must cross membranes — and, for the brain, the blood–brain barrier. |\n"
        "| `hbd`, `hba` | Hydrogen-bond donors and acceptors — how it sticks to a protein. |\n"
        "| `rb` | Rotatable bonds — how floppy it is. |\n"
        "| `psa` | Polar surface area. Above ~90 Å², getting into the brain becomes hard. |\n"
        "| `ringcount`, `heavyatomcount`, `chiralcentercount`, `mr`, `polar` | Further shape and size descriptors. |",
        "H-1-1-md"))
    cells.append(code(
        "df = load_data('H')\n"
        "print(f'{len(df)} real compounds, {df.active.sum()} of them active (pIC50 >= 7).')\n"
        "print(f'Grouped into {df.analogue_series.nunique()} analogue series.\\n')\n"
        "display(df.head()[['compound_id', 'pic50', 'active', 'analogue_series', 'mw', 'alogp', 'hbd', 'hba', 'psa']])\n"
        "print('\\nAn example SMILES string:')\n"
        "print(' ', df.iloc[0]['smiles'])",
        "H-1-1"))

    cells.append(md(
        "### 1.2 Potency is continuous; the label is not\n\n"
        "**Predict before you run:** where should the active/inactive line go?",
        "H-1-2-md"))
    cells.append(code(
        "fig, ax = plt.subplots(figsize=(7.5, 3.8))\n"
        "ax.hist(df['pic50'], bins=45, color='#2c6fbb')\n"
        "ax.axvline(7.0, color='#c0392b', linewidth=2)\n"
        "ax.annotate('the \"active\" cutoff\\n(a convention)', (7.0, ax.get_ylim()[1] * 0.75),\n"
        "            xytext=(10, 0), textcoords='offset points', color='#c0392b', fontsize=9)\n"
        "ax.set_xlabel('pIC50 (higher = more potent)'); ax.set_ylabel('number of compounds')\n"
        "ax.set_title('Real measured potencies against BACE1')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "plots.plot_class_balance(df['active'].map({0: 'inactive', 1: 'active'}),\n"
        "                         title='After applying the cutoff')\n"
        "plt.show()",
        "H-1-2"))

    cells.append(md(
        "### 1.3 ✏️ Your turn — do the simple rules work?\n\n"
        "Medicinal chemists have long used quick rules of thumb about which molecules can become drugs — "
        "**Lipinski's rule of five** (molecular weight under 500, logP under 5, ≤5 H-bond donors, ≤10 "
        "acceptors) being the famous one. Do those numbers separate active BACE1 inhibitors from inactive ones?",
        "H-1-3-md"))
    cells.append(code(
        turn(
            "Change DESCRIPTOR and re-run. Try each of:\n"
            "  'mw', 'alogp', 'hbd', 'hba', 'psa', 'rb', 'ringcount'\n"
            "Which single descriptor separates active from inactive best?\n"
            "Is any of them good enough on its own?",
            "DESCRIPTOR = 'mw'",
        ) + "\n\n"
        "labelled = df.assign(status=df['active'].map({0: 'inactive', 1: 'active'}))\n"
        "plots.plot_by_group(labelled, DESCRIPTOR, 'status', title=f'{DESCRIPTOR} for active and inactive compounds')\n"
        "plt.show()\n\n"
        "plots.plot_scatter(df[DESCRIPTOR], df['pic50'], colour_by=labelled['status'],\n"
        "                   xlabel=DESCRIPTOR, ylabel='pIC50 (measured potency)',\n"
        "                   title=f'Does {DESCRIPTOR} predict potency?', legend_title='class')\n"
        "plt.show()\n\n"
        "correlation = df[DESCRIPTOR].corr(df['pic50'])\n"
        "print(f'Correlation between {DESCRIPTOR} and potency: {correlation:+.3f}')\n\n"
        "lipinski = ((df['mw'] <= 500) & (df['alogp'] <= 5) & (df['hbd'] <= 5) & (df['hba'] <= 10))\n"
        "print(f\"\\nCompounds passing Lipinski's rule of five: {lipinski.sum()} of {len(df)}\")\n"
        "print(f'  ... of the ACTIVE compounds:   {lipinski[df.active == 1].mean():.0%} pass')\n"
        "print(f'  ... of the INACTIVE compounds: {lipinski[df.active == 0].mean():.0%} pass')\n"
        "print('\\nBACE1 inhibitors are famously large and greasy. Rules of thumb are thumbs, not rules.')",
        "H-1-3"))

    cells.append(thinking(
        "Most known BACE1 inhibitors break Lipinski's rule of five. Should we discard the rule, or discard the compounds?",
        "Neither, quite. The rule of five describes what *orally absorbed* drugs have historically looked "
        "like — it is a summary of past successes, not a law of chemistry. BACE1's active site is a long "
        "groove that needs a long molecule to fill it, so potent inhibitors are large and greasy almost by "
        "necessity, and getting them into the brain as well is genuinely hard.\n\n"
        "The transferable point: **a rule of thumb learned from one distribution quietly becomes a filter "
        "that excludes anything new.** If you had screened with Lipinski as a hard gate, you would have "
        "thrown away most of this dataset before modelling it — which is the same failure as a diagnostic "
        "model trained on one cohort refusing to work on another.",
        "H-1-3-think"))

    cells.append(go_further(
        "H-1-further",
        "run 1.3 for every descriptor and find the one with the strongest correlation with potency.",
        "make a scatter plot of `mw` against `alogp` coloured by activity. That plot is called **chemical "
        "space**, and it is how chemists picture a compound library.",
        "install RDKit (`pip install rdkit`) and draw a few molecules from their SMILES with "
        "`rdkit.Chem.Draw.MolToImage`. Compare the most and least potent compounds by eye.",
    ))

    cells.append(md(
        "---\n# 2 · Quality control\n\n"
        "Chemistry datasets have their own characteristic traps, and one of them is an exact structural twin "
        "of the problem in the imaging module.",
        "H-s2"))

    cells.append(md(
        "### 2.1 The cutoff is arbitrary, and it moves your results\n\n"
        "Nothing biological happens at pIC50 = 7. A compound at 6.99 and one at 7.01 are indistinguishable in "
        "the lab, and yet one is 'active' and the other is not. Accuracy measured near the threshold is "
        "measuring the threshold.",
        "H-2-1-md"))
    cells.append(code(
        "near_line = df[(df['pic50'] > 6.7) & (df['pic50'] < 7.3)]\n"
        "print(f'{len(near_line)} compounds ({len(near_line) / len(df):.0%}) sit within 0.3 log units of the cutoff.')\n"
        "print('Assay-to-assay variation is often larger than that.\\n')\n\n"
        "cutoffs = [6.0, 6.5, 7.0, 7.5, 8.0]\n"
        "shares = [100 * (df['pic50'] >= cutoff).mean() for cutoff in cutoffs]\n"
        "plots.plot_score_comparison([f'pIC50 >= {c}' for c in cutoffs], shares,\n"
        "                            colours=['#2c6fbb'] * len(cutoffs),\n"
        "                            title='What counts as \"active\" depends entirely on where you draw the line',\n"
        "                            ylabel='percent of the library called active')\n"
        "plt.show()",
        "H-2-1"))

    cells.append(md(
        "### 2.2 Analogue series — why these molecules are not independent\n\n"
        "Medicinal chemistry does not generate compounds at random. A chemist finds one promising molecule "
        "and then makes fifty close relatives, changing one group at a time. Those fifty are **not fifty "
        "independent data points** — they are one idea, measured fifty times.\n\n"
        "In real practice you group compounds by their **Murcko scaffold**: strip away the side chains and "
        "keep the core ring system. That needs RDKit, which we do not require, so `analogue_series` was "
        "computed by clustering the full descriptor profile — compounds with near-identical descriptors are "
        "near-identical molecules. It is an approximation of the real thing, and the 🔵 extension below "
        "computes true scaffolds if you have RDKit installed.",
        "H-2-2-md"))
    cells.append(code(
        "sizes = df.groupby('analogue_series').size().sort_values(ascending=False)\n"
        "fig, ax = plt.subplots(figsize=(8, 3.4))\n"
        "ax.bar(range(len(sizes)), sizes.values, color='#2c6fbb')\n"
        "ax.set_xlabel('analogue series (sorted by size)'); ax.set_ylabel('compounds in the series')\n"
        "ax.set_title(f'{len(sizes)} series covering {len(df)} compounds — the biggest has {sizes.max()}')\n"
        "plt.tight_layout(); plt.show()\n\n"
        "activity_by_series = df.groupby('analogue_series')['active'].mean()\n"
        "fig, ax = plt.subplots(figsize=(7, 3.4))\n"
        "ax.hist(activity_by_series, bins=20, color='#e08214')\n"
        "ax.set_xlabel('fraction of the series that is active'); ax.set_ylabel('number of series')\n"
        "ax.set_title('Series tend to be all-active or all-inactive — that is the leakage risk')\n"
        "plt.tight_layout(); plt.show()",
        "H-2-2"))

    cells.append(md(
        "### 2.3 ✏️ Your turn — scaffold leakage, the chemistry twin of subject leakage\n\n"
        "Here is the parallel, made explicit:\n\n"
        "| Module A (imaging) | Module H (chemistry) |\n|---|---|\n"
        "| One patient, several scans | One scaffold, several analogues |\n"
        "| Split by row → the model recognises *the patient* | Split by row → the model recognises *the series* |\n"
        "| Fix: `groups=subject_id` | Fix: `groups=analogue_series` |\n"
        "| The lie: it will fail on a new patient | The lie: it will fail on a new chemical series |\n\n"
        "**Identical mathematics, two disciplines that rarely talk to each other, and the same fix: one "
        "argument.** And in drug discovery the consequence is expensive — a model that only recognises "
        "series it has already seen tells you nothing about the genuinely new chemistry you were hoping to find.",
        "H-2-3-md"))
    cells.append(code(
        turn(
            "Flip GROUP_BY_SERIES between True and False and re-run.\n"
            "Then try different models. Which model is flattered most by cheating?\n"
            "(Same question, same answer, as module A section 2.3.)",
            "GROUP_BY_SERIES = True\n"
            "MODEL = 'random_forest'",
        ) + "\n\n"
        "descriptors = ['mw', 'alogp', 'hbd', 'hba', 'rb', 'heavyatomcount',\n"
        "               'chiralcentercount', 'ringcount', 'psa', 'mr', 'polar']\n"
        "X = df[descriptors]\n"
        "y = df['active']\n\n"
        "both = {}\n"
        "for label, grouping in [('split by COMPOUND\\n(leaky)', None),\n"
        "                        ('split by SERIES\\n(honest)', df['analogue_series'])]:\n"
        "    X_tr, X_te, y_tr, y_te = split_data(X, y, groups=grouping)\n"
        "    shared = set(df.loc[X_tr.index, 'analogue_series']) & set(df.loc[X_te.index, 'analogue_series'])\n"
        "    both[label] = evaluate(train_model(MODEL, X_tr, y_tr), X_te, y_te)['auroc']\n"
        "    print(f'{label.splitlines()[0]:<22s} {len(shared):>3d} series appear in BOTH halves')\n\n"
        "plots.plot_score_comparison(list(both), list(both.values()),\n"
        "                            colours=['#c0392b', '#2c6fbb'], reference=0.5,\n"
        "                            title=f'{MODEL}: identical data, identical model, different split',\n"
        "                            ylabel='AUROC')\n"
        "plt.show()\n\n"
        "grouping = df['analogue_series'] if GROUP_BY_SERIES else None\n"
        "X_train, X_test, y_train, y_test = split_data(X, y, groups=grouping)\n"
        "print(f'\\nEverything below uses GROUP_BY_SERIES = {GROUP_BY_SERIES}. '\n"
        "      f'{len(X_train)} train, {len(X_test)} test.')",
        "H-2-3"))

    cells.append(md(
        "### 2.4 Activity cliffs\n\n"
        "The other thing that makes chemistry hard: two molecules can differ by a single atom and differ by a "
        "thousandfold in potency. Chemists call this an **activity cliff**. Any model that assumes \"similar "
        "molecules have similar activity\" — which is essentially all of them — will fall off it.",
        "H-2-4-md"))
    cells.append(code(
        "spread = df.groupby('analogue_series')['pic50'].agg(['min', 'max', 'count'])\n"
        "spread['range'] = spread['max'] - spread['min']\n"
        "cliffs = spread[spread['count'] >= 5].sort_values('range', ascending=False).head(10)\n\n"
        "fig, ax = plt.subplots(figsize=(7.5, 4))\n"
        "positions = np.arange(len(cliffs))\n"
        "ax.hlines(positions, cliffs['min'], cliffs['max'], color='#2c6fbb', linewidth=3)\n"
        "ax.scatter(cliffs['min'], positions, color='#c0392b', s=45, zorder=3, label='weakest in series')\n"
        "ax.scatter(cliffs['max'], positions, color='#5aa469', s=45, zorder=3, label='most potent in series')\n"
        "ax.set_yticks(positions, [f'series {int(index)} (n={int(row[\"count\"])})' for index, row in cliffs.iterrows()],\n"
        "              fontsize=8)\n"
        "ax.set_xlabel('pIC50'); ax.legend(fontsize=9)\n"
        "ax.set_title('Within one family of near-identical molecules, potency can span 4 log units')\n"
        "plt.tight_layout(); plt.show()\n"
        "print('A 4-unit pIC50 range means a 10000-fold difference in potency, within molecules a chemist')\n"
        "print('would call \"the same compound with a tweak\". This is why chemistry resists prediction.')",
        "H-2-4"))

    cells.append(md(
        "### 2.5 QC verdict\n\n"
        "**Usable and genuinely useful, with three rules.**\n\n"
        "1. **Always group by `analogue_series`.** Everything below does.\n"
        "2. The binary label is a convention. Where it matters, model the continuous pIC50 instead (⚫ below).\n"
        "3. Expect a lower score than the imaging or biomarker modules, and do not read that as failure. "
        "Predicting new chemistry is *supposed* to be hard; a model that triages a million compounds down to "
        "a thousand worth synthesising has done its job even at AUROC 0.7.\n\n"
        "*(**Express path:** you can start from section 3 — run its catch-up cell first and everything below stands alone.)*",
        "H-2-verdict"))

    cells.append(md(
        "---\n# 3 · Build models\n\n"
        "All models below use the **series-grouped** split, so the held-out compounds come from chemistry the "
        "model has never seen. That is the realistic test: can it rank molecules from a *new* series?",
        "H-s3"))
    cells += express_catchup("H", "df = load_data('H')\ndescriptors = ['mw', 'alogp', 'hbd', 'hba', 'rb', 'heavyatomcount',\n               'chiralcentercount', 'ringcount', 'psa', 'mr', 'polar']\nX = df[descriptors]\ny = df['active']\nprint(f'{len(df)} compounds in {df.analogue_series.nunique()} analogue series; '\n      f'{int(y.sum())} active. Ready for section 3.')")

    cells.append(md("### 3.1 The ladder", "H-3-1-md"))
    cells.append(code(
        "X_train, X_test, y_train, y_test = split_data(X, y, groups=df['analogue_series'])\n"
        "print(f'{len(X_train)} training compounds from {df.loc[X_train.index, \"analogue_series\"].nunique()} series;')\n"
        "print(f'{len(X_test)} test compounds from {df.loc[X_test.index, \"analogue_series\"].nunique()} '\n"
        "      f'completely different series.\\n')\n\n"
        "ladder = ['baseline', 'logistic', 'knn', 'tree', 'random_forest', 'gradient_boosting', 'svm', 'mlp']\n"
        "table = compare_models(ladder, X_train, y_train, X_test, y_test)\n"
        "display(table)\n"
        "plots.plot_model_comparison(table, metric='auroc',\n"
        "                            title='Predicting BACE1 activity from 11 descriptors (series-grouped)')\n"
        "plt.show()",
        "H-3-1"))

    cells.append(md(
        "### 3.2 ✏️ Your turn — tune it\n\n"
        "Same dial-turning as the other modules, on real chemistry.",
        "H-3-2-md"))
    cells.append(code(
        turn(
            "Pick a model and re-run. Try 'random_forest', 'gradient_boosting',\n"
            "'svm', 'knn', 'tree'.\n"
            "Note how much lower these curves sit than in the biomarker module.\n"
            "That is the difficulty of the problem, not a fault in the code.",
            "MODEL = 'gradient_boosting'",
        ) + "\n\n"
        "description, parameter, values = MODEL_CHOICES[MODEL]\n"
        "print(f'{MODEL}: {description}\\nSweeping {parameter} over {values}\\n')\n\n"
        "swept, train_scores, test_scores = sweep_parameter(\n"
        "    MODEL, parameter, values, X_train, y_train, X_test, y_test)\n"
        "plots.plot_parameter_sweep(swept, train_scores, test_scores, parameter,\n"
        "                           title=f'{MODEL} on BACE1 compounds from unseen series')\n"
        "plt.show()\n"
        "print(f'Best held-out {parameter}: {values[int(np.argmax(test_scores))]}')",
        "H-3-2"))

    cells.append(md(
        "### 3.3 Chemical space\n\n"
        "Where do the compounds sit relative to each other, and does the model's opinion follow the chemistry?",
        "H-3-3-md"))
    cells.append(code(
        "from sklearn.decomposition import PCA\n"
        "from sklearn.preprocessing import StandardScaler\n\n"
        "space = PCA(n_components=2, random_state=42).fit_transform(\n"
        "    StandardScaler().fit_transform(df[descriptors].to_numpy()))\n\n"
        "plots.plot_scatter(space[:, 0], space[:, 1],\n"
        "                   colour_by=df['active'].map({0: 'inactive', 1: 'active'}),\n"
        "                   xlabel='chemical space, axis 1', ylabel='chemical space, axis 2',\n"
        "                   title='All 1513 compounds, coloured by measured activity', legend_title='class')\n"
        "plt.show()\n\n"
        "final_model = train_model('gradient_boosting', X_train, y_train)\n"
        "probability = final_model.predict_proba(X_test)[:, 1]\n\n"
        "fig, ax = plt.subplots(figsize=(6.6, 4.6))\n"
        "test_positions = [df.index.get_loc(index) for index in X_test.index]\n"
        "scatter = ax.scatter(space[test_positions, 0], space[test_positions, 1], c=probability,\n"
        "                     cmap='coolwarm', s=40, edgecolor='white', linewidth=0.4)\n"
        "fig.colorbar(scatter, ax=ax, label='predicted probability of being active')\n"
        "ax.set_xlabel('chemical space, axis 1'); ax.set_ylabel('chemical space, axis 2')\n"
        "ax.set_title('Held-out compounds, coloured by what the model believes')\n"
        "plt.tight_layout(); plt.show()",
        "H-3-3"))

    cells.append(md(
        "### 3.4 🔵 Your turn to write code — predict potency, not a label\n\n"
        "The binary label threw away information (2.1). Real triage ranks compounds by expected potency. "
        "Swap the classifier for a **regressor** on `pic50` and see how well the ranking holds up.\n\n"
        "> **How practitioners think about this:** in virtual screening you rarely care about accuracy. You "
        "care about **enrichment** — if you synthesise the top 100 compounds the model suggests, how many "
        "more actives do you get than by picking 100 at random? A model with a mediocre AUROC can still be "
        "worth millions if its top slice is good.",
        "H-3-4-md"))
    cells.append(code(
        "from sklearn.ensemble import GradientBoostingRegressor\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.metrics import r2_score\n\n"
        "potency_train = df.loc[X_train.index, 'pic50']\n"
        "potency_test = df.loc[X_test.index, 'pic50']\n\n"
        "# TODO (🔵): fit a GradientBoostingRegressor on X_train -> potency_train,\n"
        "#   predict on X_test, and store the predictions in `predicted_potency`.\n"
        "#   Wrap it in a Pipeline with StandardScaler, exactly as train_model does for classifiers.\n"
        "predicted_potency = None\n\n"
        "if predicted_potency is not None:\n"
        "    plots.plot_scatter(potency_test, predicted_potency,\n"
        "                       xlabel='measured pIC50', ylabel='predicted pIC50',\n"
        "                       title=f'Predicting potency on unseen series (R2 = {r2_score(potency_test, predicted_potency):.2f})')\n"
        "    plt.plot([4, 10], [4, 10], '--', color='#8a8a8a')\n"
        "    plt.show()\n"
        "    top = np.argsort(predicted_potency)[::-1][:100]\n"
        "    hit_rate = (potency_test.to_numpy()[top] >= 7).mean()\n"
        "    print(f'Top 100 by prediction: {hit_rate:.0%} are truly active.')\n"
        "    print(f'Picking 100 at random: {(potency_test >= 7).mean():.0%} would be.')\n"
        "else:\n"
        "    print('Fill in the TODO above. The solutions notebook has a worked version.')",
        "H-3-4"))
    solutions["H-3-4"] = (
        "from sklearn.ensemble import GradientBoostingRegressor\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.metrics import r2_score\n\n"
        "potency_train = df.loc[X_train.index, 'pic50']\n"
        "potency_test = df.loc[X_test.index, 'pic50']\n\n"
        "# ✅ Worked solution.\n"
        "regressor = Pipeline([\n"
        "    ('scale', StandardScaler()),\n"
        "    ('model', GradientBoostingRegressor(n_estimators=200, max_depth=3, random_state=42)),\n"
        "]).fit(X_train, potency_train)\n"
        "predicted_potency = regressor.predict(X_test)\n\n"
        "plots.plot_scatter(potency_test, predicted_potency,\n"
        "                   xlabel='measured pIC50', ylabel='predicted pIC50',\n"
        "                   title=f'Predicting potency on unseen series (R2 = {r2_score(potency_test, predicted_potency):.2f})')\n"
        "plt.plot([4, 10], [4, 10], '--', color='#8a8a8a')\n"
        "plt.show()\n\n"
        "top = np.argsort(predicted_potency)[::-1][:100]\n"
        "hit_rate = (potency_test.to_numpy()[top] >= 7).mean()\n"
        "print(f'Top 100 by prediction: {hit_rate:.0%} are truly active.')\n"
        "print(f'Picking 100 at random: {(potency_test >= 7).mean():.0%} would be.')\n"
        "print(f'Enrichment factor: {hit_rate / max((potency_test >= 7).mean(), 1e-9):.2f}x')\n\n"
        "# How to read the R2, which will be low - possibly near zero or negative.\n"
        "#\n"
        "# That is not a broken model, it is the honest difficulty of the task: we are asking it to\n"
        "# predict potency for chemical series it has never seen, from eleven crude whole-molecule\n"
        "# descriptors that say nothing about which atoms point where. A real project would use\n"
        "# fingerprints or a graph network, and would still find cross-series prediction hard.\n"
        "#\n"
        "# The enrichment factor is the number that decides whether this is worth doing. Synthesis\n"
        "# costs thousands per compound, so even a 2x enrichment halves the cost of finding a hit.\n"
        "# R2 measures whether you can predict the number; enrichment measures whether you can pick\n"
        "# the winners. In screening, only the second one buys anything."
    )

    cells.append(thinking(
        "The series-grouped AUROC is far lower than the leaky one. Which number should go in the paper — and which describes what the model will do next Monday?",
        "The same number answers both: the series-grouped one. The leaky score describes performance on "
        "chemistry the model has already seen, and nobody needs a model for that — they can look the answer "
        "up.\n\n"
        "The reason the leaky number keeps getting published is that it is produced by the *default* "
        "behaviour of every machine-learning library. `train_test_split` with no `groups` argument is one "
        "keystroke shorter than the correct call, and it silently gives a better answer. Whenever the "
        "convenient default flatters you, that is exactly when to check what it assumed — here, that every "
        "row is an independent draw, which is false for both molecules and patients.",
        "H-3-2-think"))

    cells.append(go_further(
        "H-3-further",
        "in 3.2, compare `'gradient_boosting'` and `'knn'`. Why does the nearest-neighbour model do badly on unseen series?",
        "complete 3.4, then compute the enrichment factor for the top 5% instead of the top 100.",
        "install RDKit and replace the eleven descriptors with **Morgan fingerprints** — a 2048-bit vector "
        "recording which substructures are present. That is what production models actually use, and it "
        "usually adds several AUROC points.",
    ))

    cells.append(md(
        "---\n# 4 · Read the results\n\n"
        "In drug discovery a model's output is not a diagnosis but a **shopping list**: which compounds get "
        "made next. So the figures that matter are about the top of the ranking.",
        "H-s4"))

    cells.append(md("### 4.1 The standard views", "H-4-1-md"))
    cells.append(code(
        "predicted = (probability >= 0.5).astype(int)\n"
        "final_metrics = evaluate(final_model, X_test, y_test)\n\n"
        "plots.plot_confusion(y_test, predicted, labels=('inactive', 'active'),\n"
        "                     title='Held-out compounds from unseen chemical series')\n"
        "plt.show()\n"
        "plots.plot_roc_pr(y_test, probability, title='BACE1 activity prediction, series-grouped')\n"
        "plt.show()\n"
        "plots.plot_calibration(y_test, probability)\n"
        "plt.show()\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "H-4-1"))
    cells.append(md(
        "**The errors mean money, not medicine, and they are not symmetric.** A false positive costs a "
        "chemist a few weeks and a few thousand euros making something that turns out to be inert — "
        "annoying, survivable, and you find out quickly. A **false negative** is a genuinely good compound "
        "that never gets made, and nobody ever finds out. That asymmetry is why screening models are usually "
        "run at a *low* threshold: cast wide, let the assay do the rejecting.",
        "H-4-1-read"))

    cells.append(md(
        "### 4.2 ✏️ Your turn — how many compounds would you make?\n\n"
        "The real decision. You have a synthesis budget. The model ranks the library. How deep do you go?",
        "H-4-2-md"))
    cells.append(code(
        turn(
            "BUDGET is how many compounds you can afford to synthesise.\n"
            "Try 10, 50, 200.\n"
            "Compare your hit rate to the 'pick at random' rate. The ratio\n"
            "between them is the enrichment factor, and it is the only\n"
            "number a project leader actually cares about.",
            "BUDGET = 50",
        ) + "\n\n"
        "ranking = np.argsort(probability)[::-1]\n"
        "chosen = ranking[:BUDGET]\n"
        "truth = y_test.to_numpy()\n\n"
        "hit_rate = truth[chosen].mean()\n"
        "random_rate = truth.mean()\n\n"
        "plots.plot_score_comparison(\n"
        "    [f'your top {BUDGET}', f'{BUDGET} picked at random'],\n"
        "    [100 * hit_rate, 100 * random_rate], colours=['#2c6fbb', '#8a8a8a'],\n"
        "    title=f'Enrichment factor: {hit_rate / max(random_rate, 1e-9):.2f}x',\n"
        "    ylabel='percent of chosen compounds that are truly active')\n"
        "plt.show()\n\n"
        "# The full picture: how the hit rate decays as you go deeper down the ranking.\n"
        "depths = np.arange(5, len(truth) + 1, 5)\n"
        "rates = [100 * truth[ranking[:depth]].mean() for depth in depths]\n"
        "fig, ax = plt.subplots(figsize=(7, 3.8))\n"
        "ax.plot(depths, rates, color='#2c6fbb', linewidth=2, label='model ranking')\n"
        "ax.axhline(100 * random_rate, color='#8a8a8a', linestyle='--', label='random picking')\n"
        "ax.axvline(BUDGET, color='#e08214', linewidth=2, label=f'your budget ({BUDGET})')\n"
        "ax.set_xlabel('how many compounds you synthesise, in ranked order')\n"
        "ax.set_ylabel('percent that turn out active')\n"
        "ax.set_title('The enrichment curve — the actual product of a screening model')\n"
        "ax.legend(fontsize=9); plt.tight_layout(); plt.show()\n"
        "print(f'Making the top {BUDGET}: {int(truth[chosen].sum())} real actives found.')\n"
        "print(f'Making {BUDGET} at random: about {random_rate * BUDGET:.0f} would be expected.')",
        "H-4-2"))

    cells.append(md(
        "### 4.3 What is the model looking at?\n\n"
        "Feature importance plus exact Shapley values on the six most useful descriptors.",
        "H-4-3-md"))
    cells.append(code(
        "from interpret import shapley_values, shapley_importance, baseline_prediction\n\n"
        "built_in = final_model.named_steps['model'].feature_importances_\n"
        "names = [name.split('__')[-1] for name in final_model.named_steps['preprocess'].get_feature_names_out()]\n"
        "plots.plot_importance(names, built_in,\n"
        "                      title='Gradient boosting: how often each descriptor was used to split',\n"
        "                      xlabel='built-in importance')\n"
        "plt.show()\n\n"
        "top_six = [names[index] for index in np.argsort(built_in)[::-1][:6]]\n"
        "print('Explaining the six most-used descriptors with exact Shapley values:', ', '.join(top_six), '\\n')\n"
        "shap_frame = shapley_values(final_model, X_test.head(60), X_train, features=top_six)\n"
        "importance = shapley_importance(shap_frame)\n"
        "plots.plot_importance(importance.index, importance.values,\n"
        "                      title='Average influence on the predicted probability of activity',\n"
        "                      xlabel='mean |contribution|')\n"
        "plt.show()\n\n"
        "COMPOUND = 0\n"
        "one = shap_frame.iloc[COMPOUND].sort_values()\n"
        "plots.plot_importance(one.index, one.values,\n"
        "                      title=f'{df.loc[X_test.index[COMPOUND], \"compound_id\"]}: why the model rated it as it did',\n"
        "                      xlabel='contribution to predicted probability')\n"
        "plt.show()\n"
        "print('SMILES:', df.loc[X_test.index[COMPOUND], 'smiles'])\n"
        "print(f'Measured pIC50: {df.loc[X_test.index[COMPOUND], \"pic50\"]:.2f} '\n"
        "      f'({\"active\" if y_test.iloc[COMPOUND] else \"inactive\"})')\n"
        "print(f'Cohort average {baseline_prediction(final_model, X_train):.3f} {one.sum():+.3f} '\n"
        "      f'= {baseline_prediction(final_model, X_train) + one.sum():.3f}')",
        "H-4-3"))

    cells.append(md(
        "### 4.4 The compounds it got wrong",
        "H-4-4-md"))
    cells.append(code(
        "wrong = np.where(predicted != truth)[0]\n"
        "confident_and_wrong = wrong[np.argsort(np.abs(probability[wrong] - 0.5))[::-1]][:6]\n\n"
        "print('The six compounds the model was most confident about — and wrong about:\\n')\n"
        "for position in confident_and_wrong:\n"
        "    row = df.loc[X_test.index[position]]\n"
        "    print(f\"  {row['compound_id']:>10s}  model said {probability[position]:.2f}, \"\n"
        "          f\"truth: pIC50 {row['pic50']:.2f} ({'active' if row['active'] else 'inactive'})\")\n"
        "    print(f\"             {row['smiles'][:90]}\")\n\n"
        "check = X_test.copy()\n"
        "check['correct'] = (predicted == truth).astype(int)\n"
        "check['size_band'] = pd.cut(check['mw'], [0, 400, 500, 600, 2000],\n"
        "                            labels=['<400', '400-500', '500-600', '600+'])\n"
        "check['greasiness'] = pd.cut(check['alogp'], [-5, 2, 4, 20], labels=['polar', 'medium', 'greasy'])\n"
        "for subgroup in ['size_band', 'greasiness']:\n"
        "    plots.plot_subgroup_errors(check.dropna(subset=[subgroup]), subgroup, 'correct',\n"
        "                               title=f'Proportion correct by {subgroup}')\n"
        "    plt.show()",
        "H-4-4"))

    cells.append(md(
        "### 4.5 Your headline result",
        "H-4-5-md"))
    cells.append(code(
        "plots.plot_score_comparison(list(final_metrics), list(final_metrics.values()), reference=0.5,\n"
        "                            colours=['#2c6fbb'] * 5,\n"
        "                            title='Module H — gradient boosting, held-out chemical series',\n"
        "                            ylabel='score')\n"
        "plt.show()\n"
        "print(f'{len(df)} real BACE1 compounds; tested on {len(X_test)} from unseen series.')\n"
        "print(f'Enrichment at the top 50: {truth[ranking[:50]].mean() / max(truth.mean(), 1e-9):.2f}x')\n"
        "for name, value in final_metrics.items():\n"
        "    print(f'  {name:<20s} {value:.3f}')",
        "H-4-5"))

    cells.append(md(
        "### 4.6 The part that matters most\n\n"
        "**What this model does well.** Given a library of a million purchasable compounds, it can rank them "
        "in seconds and tell a chemist which thousand to look at. That is a real, deployed, valuable use of "
        "machine learning, and it happens every day in every pharmaceutical company.\n\n"
        "**What it cannot tell you.**\n\n"
        "1. **Binding is not efficacy.** Every compound in this dataset was tested against purified BACE1 in a "
        "dish. Nothing here says whether it dissolves, survives the liver, crosses the blood–brain barrier, "
        "avoids toxicity, or helps anybody.\n"
        "2. **The target might be wrong.** This is the BACE1 lesson. The most potent, most selective, most "
        "brain-penetrant BACE1 inhibitors ever made — verubecestat, lanabecestat, atabecestat — went into "
        "large phase-3 trials in Alzheimer's disease and **failed**. Some arms got worse than placebo. A "
        "perfect model of BACE1 inhibition would have ranked those compounds at the very top.\n"
        "3. **New chemistry is genuinely hard.** Your series-grouped score is the honest one, and it is lower "
        "than the leaky one for a reason.\n\n"
        "**The transferable point:** *a model can only be as right as the question it was asked.* Every "
        "module today optimises something — an AUROC, a gene list, an enrichment factor. None of them "
        "optimises \"does the patient get better\", and no amount of model quality substitutes for choosing "
        "the right thing to predict.\n\n"
        "---\n\n"
        "### 🧠 Final question for the group discussion\n\n"
        "Your model would have enthusiastically recommended verubecestat. **Whose job was it to notice that "
        "the target was wrong, and what evidence would have changed their mind?** Could any amount of "
        "chemistry data have told you?",
        "H-4-6"))

    cells.append(go_further(
        "H-4-further",
        "in 4.2, find the budget at which the enrichment curve stops beating random picking.",
        "in 4.3, change `COMPOUND` to one of the confidently-wrong compounds from 4.4 and read its Shapley "
        "plot. What misled the model?",
        "read one review of why the BACE1 inhibitor trials failed, and write down which of the three "
        "explanations (wrong target / too late / off-target harm) you find most convincing and why.",
    ))

    return cells, solutions


# =============================================================================
# Shared notebooks
# =============================================================================

def download_notebook_cells():
    cells = []
    cells.append(md(
        "# Download the data — **do this at home, at least two days before the session**\n\n"
        "Everything this course uses is downloaded here, once, from its original public source. Nothing is "
        "downloaded during the session, because thirty laptops pulling data over seminar Wi-Fi is a "
        "guaranteed way to lose the first half hour.\n\n"
        "**The whole thing is about 18 MB and takes a couple of minutes.** You do not need a fast connection.\n\n"
        "### What you actually get\n\n"
        "| Module | Real data downloaded | What is simulated |\n|---|---|---|\n"
        "| **A** MRI | OASIS-2: 373 real MRI sessions from 150 people | the 2D slice pictures |\n"
        "| **C** biomarkers | *(nothing — no shareable dataset exists)* | the whole cohort |\n"
        "| **D** confounding | OASIS-1: 416 real people, one scan each | nothing |\n"
        "| **E** clinical records | *(nothing — EHR data is never open)* | the whole cohort |\n"
        "| **F** genetics | GWAS Catalog: real AD risk variants and effect sizes | the genotypes |\n"
        "| **G** transcriptomics | GEO GSE1297: 31 real post-mortem brains | nothing |\n"
        "| **H** chemistry | MoleculeNet BACE-1: 1513 real compounds | nothing |\n\n"
        "Each module's notebook prints its own provenance in its first cell, and says plainly which parts are "
        "real measurements and which are not.\n\n"
        "### How this notebook works\n\n"
        "1. Choose your modules · 2. See the sizes · 3. Download · 4. Prepare · 5. Verify\n\n"
        "It only needs a plain Python install — no pandas, no scikit-learn — so you can run it before setting "
        "up the environment. Re-running is always safe: files already downloaded and verified are skipped.",
        "dl-intro"))

    cells.append(code(
        "# Standard library only, so this works on a bare Python install.\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        "repo_root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src').exists())\n"
        "sys.path.insert(0, str(repo_root / 'src'))\n\n"
        "import download\n"
        "from data_registry import MODULES, SOURCES, ACCESS_DATE, module_ids, sources_for, download_bytes\n\n"
        "print('Ready. Modules available:', ', '.join(module_ids()))\n"
        "print('Source links last verified:', ACCESS_DATE)\n"
        "print('Files will be saved under:', repo_root / 'data')",
        "dl-setup"))

    cells.append(md(
        "## 1 · Choose your modules\n\n"
        "Two modules is normal and enough — the one you plan to work through fully, and one to sample. "
        "Downloading everything is fine too; it is only 18 MB.\n\n"
        "**Edit the list in the cell below.** This plain cell always works. The checkbox widget after it does "
        "the same thing, if `ipywidgets` happens to be installed — but you can ignore it entirely.",
        "dl-choose-md"))
    cells.append(code(
        "# Put the modules you want here, or use 'ALL'.\n"
        "MODULES_TO_FETCH = 'ALL'         # e.g. ['C', 'H']  or  ['A', 'D', 'G']  or  'ALL'\n\n"
        "WIDGET_STATE = {}                # only used if you run the optional widget cell below",
        "dl-choose"))
    cells.append(code(
        "# OPTIONAL: checkboxes. Skip this cell if you prefer the list above — both do the same thing.\n"
        "try:\n"
        "    import ipywidgets as widgets\n"
        "    from IPython.display import display\n\n"
        "    preselected = module_ids() if MODULES_TO_FETCH == 'ALL' else list(MODULES_TO_FETCH)\n"
        "    boxes = {m: widgets.Checkbox(value=(m in preselected),\n"
        "                                 description=f\"{m} — {MODULES[m]['title']}\",\n"
        "                                 layout=widgets.Layout(width='520px'),\n"
        "                                 style={'description_width': 'initial'})\n"
        "             for m in module_ids()}\n"
        "    select_all = widgets.Checkbox(value=False, description='select all')\n\n"
        "    def _toggle_all(change):\n"
        "        for box in boxes.values():\n"
        "            box.value = change['new']\n\n"
        "    def _sync(_=None):\n"
        "        WIDGET_STATE.clear()\n"
        "        WIDGET_STATE.update({m: box.value for m, box in boxes.items()})\n\n"
        "    select_all.observe(_toggle_all, names='value')\n"
        "    for box in boxes.values():\n"
        "        box.observe(_sync, names='value')\n"
        "    _sync()\n"
        "    display(widgets.VBox([select_all] + list(boxes.values())))\n"
        "    print('Tick what you want, then run section 3.')\n"
        "except ImportError:\n"
        "    print('ipywidgets is not installed — that is completely fine.')\n"
        "    print('Just use the MODULES_TO_FETCH list in the cell above.')",
        "dl-widgets"))

    cells.append(md(
        "## 2 · What you are about to download\n\n"
        "Sizes are measured from the actual files, not estimated, so they cannot drift out of date. Read this "
        "table before you choose.",
        "dl-sizes-md"))
    cells.append(code(
        "print(f\"{'Module':<8}{'Download':>10}   Source\")\n"
        "print('-' * 96)\n"
        "for module in module_ids():\n"
        "    entry = MODULES[module]\n"
        "    keys = entry['sources']\n"
        "    size = download.human(download_bytes([module])) if keys else 'none'\n"
        "    first = SOURCES[keys[0]]['title'] if keys else 'generated locally (no shareable source exists)'\n"
        "    print(f\"{module:<8}{size:>10}   {first}\")\n"
        "    for key in keys[1:]:\n"
        "        print(f\"{'':<18}   {SOURCES[key]['title']}\")\n"
        "    print(f\"{'':<18}   feasibility: {entry['feasibility']}\")\n"
        "print('-' * 96)\n"
        "print(f\"Everything: {download.human(download_bytes(module_ids()))} to download, \"\n"
        "      f\"roughly 1-3 minutes on a home connection.\")\n"
        "print('After preparation the derived tables add about another 2 MB.')",
        "dl-sizes"))

    cells.append(md(
        "### Licences and citations\n\n"
        "Run this cell and read it. These are other people's data, donated by real patients and released "
        "under terms that ask for attribution in return.",
        "dl-licence-md"))
    cells.append(code(
        "for key, source in SOURCES.items():\n"
        "    print(f\"{source['title']}\")\n"
        "    print(f\"  what     : {source['what']}\")\n"
        "    print(f\"  licence  : {source['licence']}\")\n"
        "    print(f\"  cite     : {source['citation']}\")\n"
        "    print(f\"  homepage : {source['homepage']}\")\n"
        "    print()",
        "dl-licence"))

    cells.append(md(
        "## 3 · Download\n\n"
        "Re-running this is safe. A file that is already present and passes its checksum is skipped in a "
        "fraction of a second. Interrupted downloads are simply restarted; a partial file is never left "
        "behind. Transient network failures are retried three times.",
        "dl-fetch-md"))
    cells.append(code(
        "picked = [m for m, on in WIDGET_STATE.items() if on]\n"
        "if not picked:\n"
        "    picked = module_ids() if MODULES_TO_FETCH == 'ALL' else [m.upper() for m in MODULES_TO_FETCH]\n\n"
        "keys = sources_for(picked)\n"
        "print(f\"Selected modules: {', '.join(picked)}\")\n"
        "print(f\"That needs {len(keys)} file(s), {download.human(download_bytes(picked))} in total.\\n\")\n\n"
        "outcomes = {}\n"
        "for key in keys:\n"
        "    print(f\"  {SOURCES[key]['title']}\")\n"
        "    status, detail = download.fetch(key)\n"
        "    outcomes[key] = status\n"
        "    print(f\"    -> {status}: {detail}\\n\")\n\n"
        "if not keys:\n"
        "    print('None of your chosen modules needs a download — their data is generated locally.')\n"
        "failed = [key for key, status in outcomes.items() if status in ('failed', 'mismatch')]\n"
        "if failed:\n"
        "    print('Some downloads did not succeed:', ', '.join(failed))\n"
        "    print('Try again (the servers are occasionally busy), or use the offline fallback in section 4.')\n"
        "else:\n"
        "    print('All downloads complete. Continue to section 4.')",
        "dl-fetch"))

    cells.append(md(
        "## 4 · Prepare the teaching tables\n\n"
        "The raw downloads are Excel workbooks, gzipped GEO matrices and a 7 MB association catalogue. This "
        "step turns them into the small, tidy tables the notebooks read, and generates the simulated parts "
        "for modules C and E.\n\n"
        "**This step needs pandas, numpy and scikit-learn** — the only part of this notebook that does. If "
        "you have not installed the environment yet, that is fine: install it, come back, and re-run this "
        "one cell. (Or just skip it — the module notebooks will run the preparation themselves the first "
        "time you open them.)\n\n"
        "### If you have no working internet at all\n\n"
        "Ask the instructor for the `data/raw` folder on a USB stick, set `INSTRUCTOR_FOLDER` below to where "
        "you copied it, and run the cell after this one.",
        "dl-prepare-md"))
    cells.append(code(
        "try:\n"
        "    import prepare\n"
        "    for module in picked:\n"
        "        try:\n"
        "            print(' ', prepare.prepare(module, force=True))\n"
        "        except FileNotFoundError as error:\n"
        "            print(f'  {module}: skipped — {error}')\n"
        "    print('\\nDone. Continue to section 5.')\n"
        "except ImportError as error:\n"
        "    print('The teaching environment is not installed yet:', error)\n"
        "    print('\\nInstall it with:   conda env create -f environment.yml')\n"
        "    print('             or:   pip install numpy pandas matplotlib scikit-learn jupyter')\n"
        "    print('\\nThen re-run this cell. Your downloads in section 3 are already safe.')",
        "dl-prepare"))
    cells.append(code(
        "# OFFLINE FALLBACK — only needed if section 3 could not download anything.\n"
        "INSTRUCTOR_FOLDER = None      # e.g. Path('/media/usb/ad_practical_data/raw')\n\n"
        "if INSTRUCTOR_FOLDER is None:\n"
        "    print('No offline folder set — skip this cell unless the downloads failed for you.')\n"
        "else:\n"
        "    for key in sources_for(picked):\n"
        "        status, detail = download.copy_from_folder(key, INSTRUCTOR_FOLDER)\n"
        "        print(f\"  {Path(SOURCES[key]['path']).name}: {status} — {detail}\")\n"
        "    print('\\nNow re-run section 4 to prepare the tables.')",
        "dl-offline"))

    cells.append(md(
        "## 5 · Verify\n\n"
        "One row per module. **If anything is not ✅, screenshot this table and send it to the instructor "
        "before the session** — not during it.\n\n"
        "- ✅ everything present and verified\n"
        "- ⚠️ downloaded but the prepared tables are missing (run section 4)\n"
        "- ❌ raw files missing (run section 3)",
        "dl-verify-md"))
    cells.append(code(
        "total_bytes = 0\n"
        "print(f\"{'Module':<8}{'Status':<8}Detail\")\n"
        "print('-' * 84)\n"
        "for module in module_ids():\n"
        "    entry = MODULES[module]\n"
        "    raw_ok = all(download.check(key)[0] == 'ok' for key in entry['sources'])\n"
        "    derived = [repo_root / name for name in entry['derived']]\n"
        "    derived_ok = all(path.exists() for path in derived)\n"
        "    size = sum(path.stat().st_size for path in derived if path.exists())\n"
        "    size += sum((repo_root / SOURCES[key]['path']).stat().st_size\n"
        "                for key in entry['sources'] if (repo_root / SOURCES[key]['path']).exists())\n"
        "    total_bytes += size\n"
        "    if raw_ok and derived_ok:\n"
        "        mark, detail = '✅', f'ready — {download.human(size)} on disk'\n"
        "    elif raw_ok:\n"
        "        mark, detail = '⚠️', 'downloaded, but not prepared yet — run section 4'\n"
        "    elif derived_ok:\n"
        "        mark, detail = '✅', f'ready (prepared) — {download.human(size)} on disk'\n"
        "    else:\n"
        "        mark, detail = '❌', 'raw files missing — run section 3'\n"
        "    print(f'{module:<8}{mark:<8}{detail}')\n"
        "print('-' * 84)\n"
        "print(f'Total on disk: {download.human(total_bytes)}')\n"
        "print('\\nNext: run 01_setup_check.ipynb, also at home. Then you are done until the session.')",
        "dl-verify"))
    return cells


def setup_check_cells():
    return [
        md(
            "# Setup check — run this at home, after the download notebook\n\n"
            "Thirty seconds. It tells you which modules will run on your machine, so that any problem is "
            "found now rather than in the first ten minutes of the session.",
            "sc-intro"),
        code(
            "import importlib\n\n"
            "print('Core packages — every module needs these:')\n"
            "missing = []\n"
            "for name, why in [('numpy', 'numbers'), ('pandas', 'tables'), ('matplotlib', 'figures'),\n"
            "                  ('sklearn', 'the models'), ('scipy', 'statistics')]:\n"
            "    try:\n"
            "        importlib.import_module(name)\n"
            "        print(f'  {name:<14} OK   ({why})')\n"
            "    except ImportError:\n"
            "        missing.append(name)\n"
            "        print(f'  {name:<14} MISSING  <- install the environment first')\n\n"
            "print('\\nOptional extras — only some cells need these:')\n"
            "for name, why in [('torch', 'module A: the CNN (there is an automatic fallback without it)'),\n"
            "                  ('lifelines', 'module E: proper Cox survival models (fallback available)'),\n"
            "                  ('rdkit', 'module H: drawing molecules and true scaffolds'),\n"
            "                  ('ipywidgets', 'checkbox selection in the download notebook'),\n"
            "                  ('shap', 'nothing — we compute exact Shapley values ourselves')]:\n"
            "    try:\n"
            "        importlib.import_module(name)\n"
            "        print(f'  {name:<14} available   ({why})')\n"
            "    except ImportError:\n"
            "        print(f'  {name:<14} not installed   ({why})')\n\n"
            "if missing:\n"
            "    print('\\n*** Install the core packages before the session: ***')\n"
            "    print('    conda env create -f environment.yml     (or)')\n"
            "    print('    pip install numpy pandas matplotlib scikit-learn scipy jupyter')",
            "sc-imports"),
        code(
            "from pathlib import Path\n"
            "import sys\n"
            "repo_root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src').exists())\n"
            "sys.path.insert(0, str(repo_root / 'src'))\n"
            "from data_registry import MODULES, SOURCES, module_ids\n\n"
            "print('Which modules can you run right now?\\n')\n"
            "ready = []\n"
            "for module in module_ids():\n"
            "    entry = MODULES[module]\n"
            "    have_raw = all((repo_root / SOURCES[key]['path']).exists() for key in entry['sources'])\n"
            "    have_derived = all((repo_root / name).exists() for name in entry['derived'])\n"
            "    if have_derived:\n"
            "        ready.append(module)\n"
            "        state = 'ready to go'\n"
            "    elif have_raw:\n"
            "        state = 'downloaded, will prepare itself when you open the notebook'\n"
            "        ready.append(module)\n"
            "    else:\n"
            "        state = 'NOT ready — run 00_download_data.ipynb'\n"
            "    print(f\"  {module}  {entry['title']:<38} {state}\")\n\n"
            "print('\\nRunnable now:', ', '.join(ready) if ready else 'none yet')\n"
            "print('\\nYou only need two modules. If your two are listed above, you are set.')",
            "sc-data"),
        code(
            "# A 10-second end-to-end test: load a module, split, train, score, draw something.\n"
            "try:\n"
            "    import matplotlib.pyplot as plt\n"
            "    import plots\n"
            "    from data import load_data\n"
            "    from models import split_data, train_model, evaluate\n\n"
            "    candidates = [m for m in ready if m in ('C', 'E', 'H', 'D')]\n"
            "    module = candidates[0] if candidates else (ready[0] if ready else None)\n"
            "    if module is None:\n"
            "        print('No module data yet — run 00_download_data.ipynb first.')\n"
            "    else:\n"
            "        frame = load_data(module)\n"
            "        print(f'Loaded module {module}: {frame.shape[0]} rows x {frame.shape[1]} columns')\n"
            "        numbers = frame.select_dtypes('number')\n"
            "        plots.plot_missingness(frame, title=f'Module {module}: missing values')\n"
            "        plt.show()\n"
            "        print('\\nEverything works. See you at the session.')\n"
            "except Exception as error:\n"
            "    print('Something is not right:', type(error).__name__, error)\n"
            "    print('Send this message to the instructor before the session.')",
            "sc-smoke"),
    ]


def orientation_cells():
    return [
        md(
            "# Orientation — how to choose your module\n\n"
            "You will work through **one module properly** and **sample a second**. There is no wrong choice, "
            "and there is no competition: nobody's results are compared with anybody else's, because the "
            "modules are not comparable and pretending otherwise would teach the wrong lesson.\n\n"
            "## Where each module sits in Alzheimer's research\n\n"
            "```\n"
            "  UNDERSTAND THE DISEASE            FIND A DRUG\n"
            "     G transcriptomics      →      H chemistry\n"
            "     which genes differ?           which molecule to make?\n"
            "              │                          │\n"
            "              └──────────┬───────────────┘\n"
            "                         ▼\n"
            "  WHO IS AT RISK                DIAGNOSE AND STAGE\n"
            "     F genetics                   C blood biomarkers\n"
            "     E clinical records           A structural MRI\n"
            "                                  D — and is any of it real? (confounding)\n"
            "```\n\n"
            "Everything on the bottom row exists because work like the top row came first.\n\n"
            "## The menu\n\n"
            "| | Module | Data | The question | Good if you… |\n|---|---|---|---|---|\n"
            "| **A** | Structural MRI | real OASIS-2 measures + simulated slices | Can a brain scan tell us who has dementia? | want to train an SVM and a CNN on images |\n"
            "| **C** | Blood & CSF biomarkers | simulated from published cohorts | Can a blood test identify AD? | **have never coded — start here** |\n"
            "| **D** | Confounding | real OASIS-1 | Is the model learning disease, or who was recruited? | like arguing about what a result means |\n"
            "| **E** | Clinical records | simulated cohort | Which life factors predict later dementia? | want survival analysis and interpretability |\n"
            "| **F** | Genetics | real GWAS effects + simulated genotypes | How much risk is written in the genome? | want to build a polygenic score by hand |\n"
            "| **G** | Brain transcriptomics | real post-mortem brains (GEO) | Which genes differ in the AD brain? | prefer discovery to prediction |\n"
            "| **H** | Chemistry | real BACE1 compounds | Which molecules are worth making? | want drug discovery, not patients |\n\n"
            "## How to pick\n\n"
            "- **Never written code?** → **C** in full. It is the fastest to run and the most legible. Then "
            "sample **D**, which reuses the same ideas and asks the awkward questions.\n"
            "- **Comfortable with code, want to build something?** → **A** in full (SVM and CNN on images). "
            "Sample **H** to see the identical leakage problem in a different discipline.\n"
            "- **Biologist?** → **G** in full. Sample **C**.\n"
            "- **Interested in prevention or epidemiology?** → **E** in full. Sample **F**.\n"
            "- **Want the widest view of the field?** → one clinical module (**A**, **C**, **D**, **E** or "
            "**F**) plus one discovery module (**G** or **H**). That pairing shows you the whole arc, from "
            "molecules to patients, and it is the pairing the wrap-up discussion is built around.",
            "or-intro"),
        code(
            "from pathlib import Path\n"
            "import sys\n"
            "repo_root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src').exists())\n"
            "sys.path.insert(0, str(repo_root / 'src'))\n"
            "from data import provenance\n"
            "from data_registry import module_ids\n\n"
            "for module in module_ids():\n"
            "    print(provenance(module))\n"
            "    print()",
            "or-menu"),
        md(
            "## Two things to carry into whichever module you pick\n\n"
            "**1. Every dataset here is somebody's body.** Real brains were donated, real people had blood "
            "drawn and lay still in a scanner, real patients consented to their genotypes being studied. "
            "Where we could not obtain data legally, we simulated it and said so — in the first cell of every "
            "notebook, every time. Check that cell before you believe a number.\n\n"
            "**2. Nothing you build today is a diagnostic tool.** Not because the code is bad, but because "
            "'this model scores well on held-out data' and 'this model should be used on a patient' are "
            "separated by external validation, prospective testing, regulatory approval, and evidence that "
            "using it changes an outcome. Every module ends by asking what would have to be true first.",
            "or-ethics"),
    ]


def wrap_cells():
    return [
        md(
            "# Cross-modal wrap-up\n\n"
            "Everyone spent the afternoon on a different corner of the same disease. This last part is a "
            "**discussion, not a scoreboard.**\n\n"
            "> There is deliberately no shared results file and no comparison between your numbers and "
            "anybody else's. The numbers are not comparable — different cohorts, different sample sizes, "
            "different label definitions, different difficulty — and lining them up on one bar chart would "
            "teach exactly the wrong lesson. **That incomparability is itself the point.**\n\n"
            "What *is* comparable is what each modality can and cannot tell you.",
            "wr-intro"),
        md(
            "## 1 · Report back — three sentences each\n\n"
            "Whoever did each module, say:\n\n"
            "1. **What was your data, and how much of it was real?**\n"
            "2. **What was the one flaw that would have fooled you?**\n"
            "3. **What is the single figure you would show somebody?**\n\n"
            "| Module | The flaw it was built around |\n|---|---|\n"
            "| **A** MRI | Subject-level leakage — one patient, several scans, split across train and test |\n"
            "| **C** biomarkers | Label leakage through the MMSE, and missingness that tracks severity |\n"
            "| **D** confounding | Age is entangled with diagnosis; education's effect reverses when you stratify |\n"
            "| **E** clinical records | Competing risk of death, reverse causation, immortal time |\n"
            "| **F** genetics | Multiple testing, population stratification, and scores that do not transfer |\n"
            "| **G** transcriptomics | p ≫ n, and cell-composition change masquerading as gene regulation |\n"
            "| **H** chemistry | Scaffold leakage — the exact twin of module A's problem, in another discipline |\n\n"
            "**Notice the pairs.** A and H are the same mathematical problem in two fields that never cite "
            "each other. C and D are the same dataset asked two different questions. That is the most "
            "transferable thing in the whole day: the failure modes are *general*, and recognising one in a "
            "field you know nothing about is a genuinely useful skill.",
            "wr-report"),
        md(
            "## 2 · Cost, invasiveness and what each modality is actually for\n\n"
            "| Modality | Cost | What the patient goes through | Used in practice for |\n|---|---|---|---|\n"
            "| Blood biomarkers | €50–300 | A blood draw | Emerging: triage before specialist referral |\n"
            "| Genetics | ~€50, once, forever | A cheek swab | Research and trial stratification, not clinical care |\n"
            "| Clinical risk factors | Free | A conversation | Population prevention advice |\n"
            "| Structural MRI | €300–800 | 30 minutes in a scanner | Confirming a diagnosis, excluding other causes |\n"
            "| PET imaging | €2000–4000 | Injection, scan, radiation dose | Confirming amyloid before an expensive therapy |\n"
            "| Brain transcriptomics | — | Only possible after death | Understanding mechanism |\n"
            "| Compound screening | — | No patient involved | Deciding what to synthesise |\n\n"
            "### Discuss\n\n"
            "**a)** You have to screen an entire national population aged 65+. Which modality, and what "
            "happens to the people your test gets wrong?\n\n"
            "**b)** A patient in front of you has memory complaints. Which modality do you reach for, and in "
            "what order?\n\n"
            "**c)** Which of today's modules was trying to **predict** something, and which was trying to "
            "**understand** something? Does a lower AUROC mean a less valuable piece of work?",
            "wr-costs"),
        md(
            "## 3 · The four things worth remembering next week\n\n"
            "**1. The split is the experiment.** Nearly every module had a way to accidentally show the model "
            "something it should not have seen — the same patient, the same molecule, the same cognitive "
            "test that defined the label. The number a model reports is a statement about how you split the "
            "data, not only about the model.\n\n"
            "**2. A baseline is not a formality.** In several modules a single well-chosen number came close "
            "to the fanciest model. If a method cannot beat one number, it has not earned its complexity — "
            "and 'we used deep learning' is not a result.\n\n"
            "**3. Ask what the score is made of.** Module D took a respectable AUROC apart and found age "
            "underneath. Shapley values in C, E, F and H did the same thing per patient. Interpretability "
            "does not make a model correct; it makes it *arguable*, which is the precondition for finding out "
            "whether it is correct.\n\n"
            "**4. Every model here optimises the wrong thing, slightly.** AUROC, gene lists, enrichment "
            "factors — none of them is \"the patient got better\". Choosing what to predict is a scientific "
            "and ethical decision that happens before any code is written, and the BACE1 story in module H "
            "is what it looks like when that decision goes wrong at a cost of billions.\n\n"
            "---\n\n"
            "### One last question\n\n"
            "You have now seen seven ways to point machine learning at Alzheimer's disease. **If you had one "
            "research budget, which would you fund — and what would you want to see before you believed the "
            "result?**",
            "wr-close"),
    ]


# =============================================================================
# Assembly
# =============================================================================

BUILDERS = {
    "A_mri_structural": build_A,
    "C_fluid_biomarkers": build_C,
    "D_confounders": build_D,
    "E_clinical_epi": build_E,
    "F_genetics": build_F,
    "G_transcriptomics": build_G,
    "H_drug_discovery": build_H,
}


def solution_cells(cells, solutions):
    """Return a copy of a module's cells with each TODO cell replaced by the worked version."""
    import copy

    output = []
    for cell in cells:
        identifier = cell["metadata"].get("id")
        if identifier in solutions and solutions[identifier]:
            output.append(code(solutions[identifier], identifier))
        else:
            output.append(copy.deepcopy(cell))
    header = md(
        "# Worked solutions\n\n"
        "This notebook is identical to the student version except that every 🔵 `# TODO` has been filled in, "
        "**with commentary on why the answer is what it is** rather than just the code. Read the comments — "
        "the reasoning is the point, not the syntax.\n\n"
        "Everything else, including the ✏️ YOUR TURN cells, is unchanged: those have no single right answer.",
        "sol-header")
    return [header] + output


def clean_removed(modules_root, solutions_root):
    """Delete notebooks for modules that no longer exist (module B was removed)."""
    keep = set(MODULES)
    for folder in [modules_root, solutions_root]:
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            elif path.suffix == ".ipynb":
                stem = path.stem.replace("_solutions", "")
                if stem not in keep:
                    path.unlink()
                    print(f"  removed stale notebook {path}")


def main():
    notebooks = Path("notebooks")
    modules_root = notebooks / "modules"
    solutions_root = Path("solutions") / "modules"
    modules_root.mkdir(parents=True, exist_ok=True)
    solutions_root.mkdir(parents=True, exist_ok=True)
    clean_removed(modules_root, solutions_root)

    written_solutions = 0
    for folder, builder in BUILDERS.items():
        cells, solutions = builder()
        (modules_root / f"{folder}.ipynb").write_text(notebook_json(cells), encoding="utf-8")
        real = {key: value for key, value in solutions.items() if value}
        if real:
            (solutions_root / f"{folder}_solutions.ipynb").write_text(
                notebook_json(solution_cells(cells, real)), encoding="utf-8")
            written_solutions += 1
        print(f"  {folder:<22} {len(cells):>3} cells, {len(real)} worked solution(s)")

    shared = {
        "00_download_data.ipynb": download_notebook_cells(),
        "01_setup_check.ipynb": setup_check_cells(),
        "02_orientation.ipynb": orientation_cells(),
        "99_crossmodal_wrap.ipynb": wrap_cells(),
    }
    for filename, cells in shared.items():
        (notebooks / filename).write_text(notebook_json(cells), encoding="utf-8")

    print(f"\nGenerated {len(BUILDERS)} module notebooks, {written_solutions} solution notebooks, "
          f"{len(shared)} shared notebooks.")


if __name__ == "__main__":
    main()

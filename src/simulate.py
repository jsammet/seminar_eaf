"""Simulated teaching data, for the parts of the course where real data cannot be shared.

Three modules need simulation, and each says so in its own first cell:

* **C** - fluid biomarkers. No open individual-level Abeta/p-tau/NfL table exists
  that we may redistribute, so the cohort is drawn from published summary
  statistics (group means, spreads, assay batch offsets, a lower limit of
  detection). Direction and magnitude are realistic; the people are not.
* **E** - clinical records. Individual EHR data are never open. Times to
  diagnosis are drawn from a Weibull survival model whose hazard ratios are set
  to published values for age, APOE e4 dose, education and vascular burden.
* **F** - genotypes only. The variants, risk alleles, frequencies and odds
  ratios are the real GWAS Catalog record; only each participant's alleles and
  disease status are drawn, because individual genotypes are access-controlled.

Module **A**'s 2D slice images are also generated here: raw OASIS images require
a data-use agreement, so we draw a simple phantom whose ventricle size and
cortical thickness follow that visit's *real measured* nWBV and eTIV.

Everything is seeded, so two students get identical numbers.
"""
import math
import random

SEED = 2026


def _clip(value, low, high):
    return max(low, min(high, value))


# --------------------------------------------------------------------------
# Module C - fluid biomarkers
# --------------------------------------------------------------------------

# Group -> (Abeta42/40 ratio, p-tau181 pg/ml, NfL pg/ml, GFAP pg/ml) as (mean, sd).
_C_PROFILE = {
    "CN":  {"ab42_40_ratio": (0.092, 0.017), "ptau181_pg_ml": (14.0, 6.0), "nfl_pg_ml": (18.0, 8.0), "gfap_pg_ml": (115.0, 50.0)},
    "MCI": {"ab42_40_ratio": (0.079, 0.019), "ptau181_pg_ml": (19.5, 9.0), "nfl_pg_ml": (24.0, 11.0), "gfap_pg_ml": (160.0, 70.0)},
    "AD":  {"ab42_40_ratio": (0.068, 0.017), "ptau181_pg_ml": (28.0, 13.0), "nfl_pg_ml": (31.0, 15.0), "gfap_pg_ml": (215.0, 90.0)},
}

# The assay has a lower limit of detection: anything under this is reported as the limit.
PTAU_LOWER_LIMIT = 8.0

# Two collection sites ran different assay lots, so one reads systematically high.
_C_BATCH_SHIFT = {"site_1": 1.00, "site_2": 1.18, "site_3": 0.94}


def fluid_biomarkers(n=420):
    """Module C: a simulated memory-clinic biomarker cohort."""
    rng = random.Random(SEED + 3)
    fields = [
        "subject_id", "age", "sex", "education_years", "apoe4_carrier", "site",
        "diagnosis", "ab42_pg_ml", "ab40_pg_ml", "ab42_40_ratio",
        "ptau181_pg_ml", "nfl_pg_ml", "gfap_pg_ml", "mmse",
    ]
    rows = []
    for i in range(n):
        # Diagnosis first, then everything downstream of it.
        draw = rng.random()
        diagnosis = "CN" if draw < 0.40 else ("MCI" if draw < 0.75 else "AD")
        severity = {"CN": 0, "MCI": 1, "AD": 2}[diagnosis]
        age = _clip(rng.gauss(69 + 3.5 * severity, 7.5), 50, 92)
        sex = "F" if rng.random() < 0.56 else "M"
        site = rng.choice(["site_1", "site_2", "site_3"])
        apoe4 = int(rng.random() < (0.22 + 0.18 * severity))
        profile = _C_PROFILE[diagnosis]

        ratio = _clip(rng.gauss(*profile["ab42_40_ratio"]) - 0.004 * apoe4, 0.030, 0.140)
        ab40 = _clip(rng.gauss(7800, 1400), 3000, 13000)
        ab42 = ratio * ab40

        ptau = rng.gauss(*profile["ptau181_pg_ml"]) * _C_BATCH_SHIFT[site]
        ptau = max(ptau, 0.5)
        censored = ptau < PTAU_LOWER_LIMIT      # left-censoring at the detection limit
        ptau = PTAU_LOWER_LIMIT if censored else ptau

        nfl = max(rng.gauss(*profile["nfl_pg_ml"]) + 0.35 * (age - 70), 3.0)
        gfap = max(rng.gauss(*profile["gfap_pg_ml"]), 20.0)
        mmse = round(_clip(rng.gauss(29 - 3.0 * severity - 0.05 * max(age - 75, 0), 1.6), 6, 30))

        # Sicker people miss follow-up bloods more often: missingness is NOT random.
        missing_ptau = rng.random() < (0.03 + 0.06 * severity)
        missing_gfap = rng.random() < 0.05

        rows.append({
            "subject_id": f"C{i:04d}",
            "age": round(age, 1),
            "sex": sex,
            "education_years": round(_clip(rng.gauss(13.5, 3.2), 5, 22)),
            "apoe4_carrier": apoe4,
            "site": site,
            "diagnosis": diagnosis,
            "ab42_pg_ml": round(ab42, 1),
            "ab40_pg_ml": round(ab40, 1),
            "ab42_40_ratio": round(ratio, 4),
            "ptau181_pg_ml": None if missing_ptau else round(ptau, 2),
            "nfl_pg_ml": round(nfl, 2),
            "gfap_pg_ml": None if missing_gfap else round(gfap, 1),
            "mmse": mmse,
        })
    return fields, rows


# --------------------------------------------------------------------------
# Module E - clinical records / epidemiology
# --------------------------------------------------------------------------

# log hazard ratios, roughly matching published population estimates
_E_EFFECTS = {
    "age_per_year": math.log(1.10),
    "apoe4_per_allele": math.log(2.6),
    "education_per_year": math.log(0.93),
    "hypertension": math.log(1.25),
    "diabetes": math.log(1.45),
    "smoking": math.log(1.30),
    "physical_activity": math.log(0.75),
    "depression_history": math.log(1.60),
    "female": math.log(1.10),
}


def clinical_records(n=900, max_followup=12.0):
    """Module E: a simulated prospective ageing cohort with time to AD diagnosis."""
    rng = random.Random(SEED + 5)
    fields = [
        "subject_id", "age_baseline", "sex", "education_years", "apoe4_dose",
        "hypertension", "diabetes", "smoking", "physical_activity",
        "depression_history", "baseline_mmse", "systolic_bp",
        "followup_years", "diagnosis_event", "died_without_diagnosis",
    ]
    rows = []
    for i in range(n):
        age = _clip(rng.gauss(70, 7), 55, 90)
        female = int(rng.random() < 0.55)
        education = round(_clip(rng.gauss(12.5, 3.5), 4, 22))
        apoe4 = 0 if rng.random() < 0.72 else (1 if rng.random() < 0.88 else 2)
        hypertension = int(rng.random() < 0.42 + 0.004 * (age - 70))
        diabetes = int(rng.random() < 0.16)
        smoking = int(rng.random() < 0.20)
        activity = int(rng.random() < 0.45)
        depression = int(rng.random() < 0.18)

        linear = (
            _E_EFFECTS["age_per_year"] * (age - 70)
            + _E_EFFECTS["apoe4_per_allele"] * apoe4
            + _E_EFFECTS["education_per_year"] * (education - 12)
            + _E_EFFECTS["hypertension"] * hypertension
            + _E_EFFECTS["diabetes"] * diabetes
            + _E_EFFECTS["smoking"] * smoking
            + _E_EFFECTS["physical_activity"] * activity
            + _E_EFFECTS["depression_history"] * depression
            + _E_EFFECTS["female"] * female
        )
        # Weibull time to diagnosis with shape 1.4 and a slow baseline hazard.
        scale = 26.0 * math.exp(-linear / 1.4)
        time_to_event = scale * (-math.log(1 - rng.random())) ** (1 / 1.4)
        # Competing risk: death without a diagnosis, which matters in an elderly cohort.
        time_to_death = 28.0 * math.exp(-0.055 * (age - 70)) * (-math.log(1 - rng.random()))
        time_to_dropout = rng.uniform(1.0, max_followup)

        first = min(time_to_event, time_to_death, time_to_dropout)
        event = int(first == time_to_event)
        died = int(first == time_to_death)

        rows.append({
            "subject_id": f"E{i:04d}",
            "age_baseline": round(age, 1),
            "sex": "F" if female else "M",
            "education_years": education,
            "apoe4_dose": apoe4,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "smoking": smoking,
            "physical_activity": activity,
            "depression_history": depression,
            "baseline_mmse": round(_clip(rng.gauss(28.5 - 0.04 * max(age - 70, 0), 1.4), 20, 30)),
            "systolic_bp": round(_clip(rng.gauss(134 + 12 * hypertension, 15), 95, 205)),
            "followup_years": round(min(first, max_followup), 2),
            "diagnosis_event": event if first <= max_followup else 0,
            "died_without_diagnosis": died if first <= max_followup else 0,
        })
    return fields, rows


# --------------------------------------------------------------------------
# Module F - genotypes drawn from real GWAS Catalog effects
# --------------------------------------------------------------------------

def genotype_cohort(variants, n=1200):
    """Module F: simulate genotypes and disease status from *real* variant effects.

    ``variants`` is a list of dicts with keys ``rsid``, ``risk_allele_freq`` and
    ``odds_ratio``, taken straight from the GWAS Catalog download.
    """
    rng = random.Random(SEED + 6)
    ids = [variant["rsid"] for variant in variants]
    fields = ["subject_id", "age", "sex", "ancestry"] + ids + ["diagnosis"]
    rows = []
    for i in range(n):
        # Two ancestry groups with slightly different allele frequencies: this is what
        # makes a polygenic score transfer badly, and it is a real equity problem.
        ancestry = "reference" if rng.random() < 0.75 else "underrepresented"
        shift = 0.0 if ancestry == "reference" else rng.gauss(0, 0.06)
        age = _clip(rng.gauss(72, 8), 55, 95)
        female = rng.random() < 0.57

        log_odds = -3.4 + 0.085 * (age - 72) + (0.15 if female else 0.0)
        row = {
            "subject_id": f"F{i:05d}",
            "age": round(age, 1),
            "sex": "F" if female else "M",
            "ancestry": ancestry,
        }
        for variant in variants:
            frequency = _clip(variant["risk_allele_freq"] + shift, 0.01, 0.99)
            dose = sum(1 for _ in range(2) if rng.random() < frequency)
            row[variant["rsid"]] = dose
            log_odds += dose * math.log(variant["odds_ratio"])
        probability = 1 / (1 + math.exp(-log_odds))
        row["diagnosis"] = "AD" if rng.random() < probability else "CN"
        rows.append(row)
    return fields, rows


# --------------------------------------------------------------------------
# Module A - 2D slice phantoms conditioned on real OASIS measurements
# --------------------------------------------------------------------------

def brain_slice(nwbv, etiv, size=64, seed=0):
    """Draw one simulated axial slice for a visit with measured nWBV and eTIV.

    nWBV (normalised whole-brain volume) sets how much brain tissue there is;
    the ventricles and sulcal spaces expand as it falls, which is what atrophy
    looks like on a real scan. eTIV sets overall head size. Returns a list of
    lists of floats in [0, 1] so this module stays numpy-free.
    """
    rng = random.Random(seed)
    # nWBV in OASIS runs roughly 0.64 (marked atrophy) to 0.84 (young, full brain).
    tissue = _clip((nwbv - 0.62) / 0.24, 0.0, 1.0)
    head = 0.30 + 0.06 * _clip((etiv - 1200) / 800, -1.0, 1.0)
    ventricle = 0.055 + 0.075 * (1 - tissue)      # bigger when there is less brain
    cortex_gap = 0.020 + 0.045 * (1 - tissue)     # widened sulci at the surface

    centre = (size - 1) / 2
    image = []
    for y in range(size):
        row = []
        for x in range(size):
            dx = (x - centre) / size
            dy = (y - centre) / size
            radius = math.sqrt(dx * dx + (dy * 1.15) ** 2)
            if radius > head:
                value = 0.02                       # background outside the head
            elif radius > head - cortex_gap:
                value = 0.30                       # CSF in the widened sulci
            elif radius > head - cortex_gap - 0.035:
                value = 0.82                       # grey matter ribbon
            else:
                value = 0.62                       # white matter
            # Lateral ventricles: two ellipses either side of the midline.
            for side in (-1, 1):
                vx = dx - side * 0.055
                vy = dy + 0.015
                if (vx / ventricle) ** 2 + (vy / (ventricle * 1.9)) ** 2 < 1.0:
                    value = 0.12
            row.append(_clip(value + rng.gauss(0, 0.05), 0.0, 1.0))
        image.append(row)
    return image

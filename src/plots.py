"""Every figure the notebooks draw lives here, so each module looks the same.

Rules kept throughout: axis labels with units, a title that reads as a caption,
and a return value of the matplotlib axes so a student can keep customising.
Nothing here needs seaborn.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

BLUE, ORANGE, GREY = "#2c6fbb", "#e08214", "#8a8a8a"
DIVERGING = LinearSegmentedColormap.from_list("ad", ["#2c6fbb", "#f7f7f7", "#c0392b"])


def _finish(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=11)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return ax


# --- section 1: understanding the data ------------------------------------

def plot_missingness(frame, title="Missing values per column"):
    counts = frame.isna().sum().sort_values(ascending=False)
    counts = counts[counts > 0]
    fig, ax = plt.subplots(figsize=(8, max(2.2, 0.35 * max(len(counts), 1))))
    if counts.empty:
        ax.text(0.5, 0.5, "No missing values anywhere in this table.", ha="center", va="center")
        ax.axis("off")
        return ax
    percent = 100 * counts / len(frame)
    ax.barh(counts.index[::-1], percent.values[::-1], color=ORANGE)
    for y, value in enumerate(counts.values[::-1]):
        ax.text(percent.values[::-1][y] + 0.4, y, f"{value}", va="center", fontsize=9)
    ax.set_xlim(0, max(percent.max() * 1.25, 5))
    plt.tight_layout()
    return _finish(ax, title, "percent of rows missing (%)", "")


def plot_class_balance(labels, title="Who is in this dataset?"):
    counts = labels.value_counts()
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    bars = ax.bar(counts.index.astype(str), counts.values, color=[BLUE, ORANGE, GREY, "#5aa469"][: len(counts)])
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value}\n({100 * value / counts.sum():.0f}%)",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, counts.max() * 1.25)
    plt.tight_layout()
    return _finish(ax, title, "group", "number of records")


def plot_by_group(frame, column, group, unit="", title=None):
    """Overlaid histograms of one measurement, split by a grouping column."""
    fig, ax = plt.subplots(figsize=(7, 3.6))
    values = frame[[column, group]].dropna()
    categories = sorted(values[group].astype(str).unique())
    edges = np.histogram_bin_edges(values[column], bins=22)
    palette = [BLUE, ORANGE, "#5aa469", GREY, "#8e44ad"]
    for index, category in enumerate(categories):
        subset = values.loc[values[group].astype(str) == category, column]
        ax.hist(subset, bins=edges, alpha=0.55, label=f"{category} (n={len(subset)})",
                color=palette[index % len(palette)])
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title or f"{column} by {group}", f"{column} {unit}".strip(), "number of records")


def plot_scatter(x, y, colour_by=None, xlabel="x", ylabel="y", title="", legend_title=""):
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    if colour_by is None:
        ax.scatter(x, y, s=26, alpha=0.75, color=BLUE, edgecolor="white", linewidth=0.4)
    else:
        categories = sorted(np.unique(np.asarray(colour_by).astype(str)))
        palette = [BLUE, ORANGE, "#5aa469", GREY, "#8e44ad", "#c0392b"]
        for index, category in enumerate(categories):
            mask = np.asarray(colour_by).astype(str) == category
            ax.scatter(np.asarray(x)[mask], np.asarray(y)[mask], s=30, alpha=0.8,
                       color=palette[index % len(palette)], edgecolor="white", linewidth=0.4, label=category)
        ax.legend(title=legend_title, fontsize=9)
    plt.tight_layout()
    return _finish(ax, title, xlabel, ylabel)


# --- section 2: quality control -------------------------------------------

def plot_score_comparison(labels, scores, title, ylabel="balanced accuracy", reference=None, colours=None):
    """A bar per variant — used for wrong-way/right-way and knob-turning cells."""
    fig, ax = plt.subplots(figsize=(max(5, 1.5 * len(labels)), 3.6))
    colours = colours or [BLUE if index else ORANGE for index in range(len(labels))]
    bars = ax.bar(range(len(labels)), scores, color=colours)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, score, f"{score:.3f}", ha="center", va="bottom", fontsize=9)
    if reference is not None:
        ax.axhline(reference, color=GREY, linestyle="--", linewidth=1)
        ax.text(len(labels) - 0.5, reference, " chance", va="bottom", ha="right", color=GREY, fontsize=8)
    ax.set_ylim(0, max(max(scores) * 1.2, 1.0))
    plt.tight_layout()
    return _finish(ax, title, "", ylabel)


def plot_group_means(frame, value, group, title=None, unit=""):
    """Mean of one measurement per site/batch, with the spread — the batch-effect view."""
    stats = frame.groupby(group, observed=True)[value].agg(["mean", "std", "count"]).sort_index()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.errorbar(stats.index.astype(str), stats["mean"], yerr=stats["std"], fmt="o",
                color=BLUE, capsize=5, markersize=8)
    for index, (name, row) in enumerate(stats.iterrows()):
        ax.annotate(f"n={int(row['count'])}", (index, row["mean"]), textcoords="offset points",
                    xytext=(10, 0), fontsize=8, color=GREY)
    plt.tight_layout()
    return _finish(ax, title or f"{value} by {group} (mean ± SD)", group, f"{value} {unit}".strip())


# --- section 3: modelling --------------------------------------------------

def plot_model_comparison(table, metric="balanced_accuracy", title="Model comparison"):
    values = table[metric].sort_values()
    fig, ax = plt.subplots(figsize=(7, max(2.6, 0.5 * len(values))))
    colours = [ORANGE if name == "baseline" else BLUE for name in values.index]
    bars = ax.barh(values.index, values.values, color=colours)
    for bar, value in zip(bars, values.values):
        ax.text(value + 0.01, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", va="center", fontsize=9)
    ax.set_xlim(0, 1.08)
    ax.axvline(0.5, color=GREY, linestyle="--", linewidth=1)
    plt.tight_layout()
    return _finish(ax, title, metric.replace("_", " "), "")


def plot_parameter_sweep(values, train_scores, test_scores, parameter, metric="balanced accuracy", title=None):
    """The overfitting picture: training score up, held-out score down."""
    labels = [str(value) for value in values]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ax.plot(labels, train_scores, "o-", color=ORANGE, label="training data (what it memorised)")
    ax.plot(labels, test_scores, "o-", color=BLUE, label="held-out data (what it learned)")
    best = int(np.argmax(test_scores))
    ax.axvline(best, color=GREY, linestyle=":", linewidth=1)
    ax.annotate(f"best held-out\n{parameter}={labels[best]}", (best, test_scores[best]),
                textcoords="offset points", xytext=(8, -28), fontsize=8, color=GREY)
    ax.set_ylim(0.4, 1.03)
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title or f"Effect of {parameter}", parameter, metric)


def plot_learning_curve(sizes, train_scores, test_scores, title="Does more data help?"):
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(sizes, train_scores, "o-", color=ORANGE, label="training")
    ax.plot(sizes, test_scores, "o-", color=BLUE, label="held-out")
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title, "number of training records", "balanced accuracy")


# --- section 4: results ----------------------------------------------------

def plot_confusion(y_true, y_predicted, labels=("no dementia", "dementia"), title="Confusion matrix"):
    matrix = confusion_matrix(y_true, y_predicted, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.imshow(matrix, cmap="Blues")
    meanings = [["true negative", "false positive\n(false alarm)"],
                ["false negative\n(missed diagnosis)", "true positive"]]
    for row in range(2):
        for column in range(2):
            colour = "white" if matrix[row, column] > matrix.max() * 0.55 else "black"
            ax.text(column, row, f"{matrix[row, column]}\n{meanings[row][column]}",
                    ha="center", va="center", color=colour, fontsize=9)
    ax.set_xticks([0, 1], [f"predicted\n{labels[0]}", f"predicted\n{labels[1]}"], fontsize=9)
    ax.set_yticks([0, 1], [f"actually\n{labels[0]}", f"actually\n{labels[1]}"], fontsize=9)
    ax.set_title(title, fontsize=11)
    plt.tight_layout()
    return ax


def plot_roc_pr(y_true, probability, title="Held-out performance"):
    """ROC and precision-recall side by side. PR is the honest one under imbalance."""
    from sklearn.metrics import average_precision_score, roc_auc_score

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fpr, tpr, _ = roc_curve(y_true, probability)
    axes[0].plot(fpr, tpr, color=BLUE, linewidth=2, label=f"AUROC = {roc_auc_score(y_true, probability):.3f}")
    axes[0].plot([0, 1], [0, 1], "--", color=GREY, label="coin flip")
    axes[0].legend(fontsize=9, loc="lower right")
    _finish(axes[0], "ROC: catching cases vs false alarms", "false positive rate", "sensitivity (true positive rate)")

    precision, recall, _ = precision_recall_curve(y_true, probability)
    prevalence = float(np.mean(y_true))
    axes[1].plot(recall, precision, color=ORANGE, linewidth=2,
                 label=f"AUPRC = {average_precision_score(y_true, probability):.3f}")
    axes[1].axhline(prevalence, linestyle="--", color=GREY, label=f"prevalence = {prevalence:.2f}")
    axes[1].set_ylim(0, 1.02)
    axes[1].legend(fontsize=9, loc="lower left")
    _finish(axes[1], "Precision-recall: of those flagged, how many are real?", "recall (sensitivity)", "precision")
    fig.suptitle(title, fontsize=12)
    plt.tight_layout()
    return axes


def plot_threshold_sweep(y_true, probability, chosen=0.5, title="Moving the decision threshold"):
    thresholds = np.linspace(0.02, 0.98, 97)
    sensitivity, specificity, flagged = [], [], []
    y_true = np.asarray(y_true)
    for threshold in thresholds:
        predicted = (probability >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
        sensitivity.append(tp / max(tp + fn, 1))
        specificity.append(tn / max(tn + fp, 1))
        flagged.append(predicted.mean())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(thresholds, sensitivity, color=BLUE, linewidth=2, label="sensitivity — cases we catch")
    ax.plot(thresholds, specificity, color=ORANGE, linewidth=2, label="specificity — healthy people we spare")
    ax.plot(thresholds, flagged, color=GREY, linestyle=":", linewidth=2, label="fraction of the clinic flagged")
    ax.axvline(chosen, color="black", linewidth=1)
    ax.annotate(f"your threshold = {chosen:.2f}", (chosen, 0.04), rotation=90, fontsize=8,
                textcoords="offset points", xytext=(4, 0))
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=9, loc="center left")
    plt.tight_layout()
    return _finish(ax, title, "probability threshold for calling someone a case", "proportion")


def plot_importance(names, values, title="What is the model leaning on?", xlabel="importance"):
    order = np.argsort(np.abs(values))
    names = np.asarray(names)[order]
    values = np.asarray(values)[order]
    fig, ax = plt.subplots(figsize=(7, max(2.6, 0.38 * len(names))))
    colours = [BLUE if value >= 0 else "#c0392b" for value in values]
    ax.barh(names, values, color=colours)
    ax.axvline(0, color="black", linewidth=0.8)
    plt.tight_layout()
    return _finish(ax, title, xlabel, "")


def plot_subgroup_errors(frame, subgroup, correct, title=None):
    """Accuracy per subgroup — who would this model fail?"""
    stats = frame.groupby(subgroup, observed=True)[correct].agg(["mean", "count"])
    fig, ax = plt.subplots(figsize=(max(5, 1.4 * len(stats)), 3.6))
    bars = ax.bar(stats.index.astype(str), stats["mean"], color=BLUE)
    for bar, (_, row) in zip(bars, stats.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, row["mean"], f"{row['mean']:.2f}\nn={int(row['count'])}",
                ha="center", va="bottom", fontsize=9)
    ax.axhline(frame[correct].mean(), color=ORANGE, linestyle="--", label="overall")
    ax.set_ylim(0, 1.2)
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title or f"Accuracy by {subgroup}", subgroup, "proportion correct")


def plot_calibration(y_true, probability, bins=8, title="Calibration: do the probabilities mean anything?"):
    y_true = np.asarray(y_true)
    edges = np.quantile(probability, np.linspace(0, 1, bins + 1))
    edges = np.unique(edges)
    centres, observed = [], []
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (probability >= low) & (probability <= high)
        if mask.sum() >= 3:
            centres.append(probability[mask].mean())
            observed.append(y_true[mask].mean())
    fig, ax = plt.subplots(figsize=(5, 4.4))
    ax.plot([0, 1], [0, 1], "--", color=GREY, label="perfectly calibrated")
    ax.plot(centres, observed, "o-", color=BLUE, label="this model")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title, "predicted probability", "observed fraction of cases")


# --- images (module A) -----------------------------------------------------

def plot_image_grid(images, titles=None, columns=6, title="", cmap="gray"):
    images = np.asarray(images)
    rows = int(np.ceil(len(images) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(1.7 * columns, 1.9 * rows))
    axes = np.atleast_1d(axes).ravel()
    for index, ax in enumerate(axes):
        ax.axis("off")
        if index < len(images):
            ax.imshow(images[index], cmap=cmap)
            if titles is not None:
                ax.set_title(str(titles[index]), fontsize=8)
    if title:
        fig.suptitle(title, fontsize=12)
    plt.tight_layout()
    return axes


# --- discovery (module G) --------------------------------------------------

def plot_volcano(log_fold_change, p_values, names, alpha=0.05, top=12, title="Volcano plot"):
    log_fold_change = np.asarray(log_fold_change)
    neg_log_p = -np.log10(np.asarray(p_values) + 1e-300)
    significant = np.asarray(p_values) < alpha
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(log_fold_change[~significant], neg_log_p[~significant], s=10, color=GREY, alpha=0.4, label="not significant")
    ax.scatter(log_fold_change[significant], neg_log_p[significant], s=16, color="#c0392b", alpha=0.8, label=f"FDR < {alpha}")
    ax.axhline(-np.log10(alpha), linestyle="--", color=GREY, linewidth=1)
    ax.axvline(0, color="black", linewidth=0.6)
    ranked = np.argsort(-neg_log_p)[:top]
    for index in ranked:
        ax.annotate(names[index], (log_fold_change[index], neg_log_p[index]), fontsize=8,
                    textcoords="offset points", xytext=(4, 3))
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title, "log2 fold change (AD vs control)", "-log10(adjusted p)")


def plot_heatmap(matrix, row_labels, column_labels, title="Expression heatmap", cbar_label="z-score"):
    fig, ax = plt.subplots(figsize=(max(6, 0.28 * len(column_labels)), max(4, 0.28 * len(row_labels))))
    image = ax.imshow(matrix, cmap=DIVERGING, aspect="auto", vmin=-2.5, vmax=2.5)
    ax.set_yticks(range(len(row_labels)), row_labels, fontsize=8)
    ax.set_xticks(range(len(column_labels)), column_labels, rotation=90, fontsize=7)
    fig.colorbar(image, ax=ax, shrink=0.7, label=cbar_label)
    ax.set_title(title, fontsize=11)
    plt.tight_layout()
    return ax


# --- survival (module E) ---------------------------------------------------

def kaplan_meier(times, events):
    """Kaplan-Meier estimate, written out so students can see the arithmetic."""
    order = np.argsort(times)
    times, events = np.asarray(times)[order], np.asarray(events)[order]
    at_risk = len(times)
    survival, points = 1.0, [(0.0, 1.0)]
    for index, time in enumerate(times):
        if events[index] == 1:
            survival *= 1 - 1 / at_risk
            points.append((time, survival))
        at_risk -= 1
    return np.array([point[0] for point in points]), np.array([point[1] for point in points])


def plot_survival(frame, time_column, event_column, group_column, title="Time to diagnosis"):
    fig, ax = plt.subplots(figsize=(7, 4.4))
    palette = [BLUE, ORANGE, "#5aa469", GREY, "#8e44ad"]
    for index, (name, group) in enumerate(frame.groupby(group_column)):
        times, survival = kaplan_meier(group[time_column], group[event_column])
        ax.step(times, 100 * survival, where="post", color=palette[index % len(palette)],
                linewidth=2, label=f"{group_column} = {name} (n={len(group)})")
    ax.set_ylim(0, 102)
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _finish(ax, title, "years of follow-up", "percent still undiagnosed")

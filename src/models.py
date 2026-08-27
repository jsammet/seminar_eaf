"""Shared, CPU-friendly modelling API used identically by every module.

Three functions carry the whole course:

    X_train, X_test, y_train, y_test = split_data(X, y, groups=...)
    model = train_model('logistic', X_train, y_train, C=1.0)
    metrics = evaluate(model, X_test, y_test)

``train_model`` always wraps the estimator in a preprocessing pipeline that is
fitted on the training data only, so scaling and imputation cannot leak. Every
estimator accepts keyword arguments, which is what makes the "change one number
and re-run" cells in the notebooks work.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

RANDOM_SEED = 42

# name -> (plain-language description, the one knob worth turning first, values to sweep)
MODEL_CHOICES = {
    "baseline": ("Always predicts the commonest class. The score to beat.", None, None),
    "logistic": ("Logistic regression: a weighted sum of the features. Readable coefficients.", "C", [0.01, 0.1, 1.0, 10.0, 100.0]),
    "knn": ("k-nearest neighbours: copy the label of the most similar patients.", "n_neighbors", [1, 3, 5, 11, 25, 51]),
    "tree": ("A single decision tree: a flowchart of yes/no questions.", "max_depth", [1, 2, 3, 5, 8, 12, None]),
    "random_forest": ("Hundreds of trees, each on a random slice of the data, then averaged.", "max_depth", [2, 3, 5, 8, 12, None]),
    "gradient_boosting": ("Trees added one at a time, each fixing the previous ones' mistakes.", "learning_rate", [0.01, 0.05, 0.1, 0.3, 1.0]),
    "svm": ("Support vector machine: find the widest possible margin between the classes.", "C", [0.01, 0.1, 1.0, 10.0, 100.0]),
    "mlp": ("A small neural network (multi-layer perceptron).", "alpha", [1e-5, 1e-3, 1e-2, 1e-1, 1.0]),
}


def _estimator(name, **params):
    name = name.lower()
    if name == "baseline":
        return DummyClassifier(strategy="most_frequent", **params)
    if name == "logistic":
        return LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_SEED, **params)
    if name == "knn":
        return KNeighborsClassifier(**params)
    if name == "tree":
        return DecisionTreeClassifier(max_depth=params.pop("max_depth", 3), class_weight="balanced", random_state=RANDOM_SEED, **params)
    if name == "random_forest":
        params.setdefault("n_estimators", 200)
        params.setdefault("max_depth", 5)
        return RandomForestClassifier(class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1, **params)
    if name == "gradient_boosting":
        params.setdefault("n_estimators", 150)
        params.setdefault("max_depth", 3)
        return GradientBoostingClassifier(random_state=RANDOM_SEED, **params)
    if name == "svm":
        params.setdefault("kernel", "rbf")
        params.setdefault("C", 1.0)
        return SVC(class_weight="balanced", probability=True, random_state=RANDOM_SEED, **params)
    if name == "mlp":
        params.setdefault("hidden_layer_sizes", (32, 16))
        params.setdefault("max_iter", 2000)
        return MLPClassifier(random_state=RANDOM_SEED, **params)
    raise KeyError(f"Unknown model {name!r}. Choose one of: {', '.join(MODEL_CHOICES)}")


def make_preprocessor(X, impute="median", scale=True):
    """Impute and (optionally) scale numbers; impute and one-hot encode text.

    ``impute`` is one of 'median', 'mean' or 'most_frequent' — the notebooks let
    students switch it and watch the score move.
    """
    numeric = X.select_dtypes(include=np.number).columns
    categorical = X.select_dtypes(exclude=np.number).columns
    numeric_steps = [("impute", SimpleImputer(strategy=impute))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    return ColumnTransformer([
        ("num", Pipeline(numeric_steps), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])


def split_data(X, y, groups=None, test_size=0.25, seed=RANDOM_SEED):
    """Split into train and test.

    Pass ``groups`` whenever rows are not independent — repeated visits from one
    subject, or chemical analogues of one scaffold. Without it, the same person
    (or nearly the same molecule) sits on both sides and the test score is a lie.
    """
    if groups is None:
        return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train, test = next(splitter.split(X, y, groups))
    return X.iloc[train], X.iloc[test], y.iloc[train], y.iloc[test]


def train_model(name, X, y, impute="median", scale=True, **params):
    """Fit a preprocessing + estimator pipeline. Extra keywords go to the estimator."""
    return Pipeline([
        ("preprocess", make_preprocessor(X, impute=impute, scale=scale)),
        ("model", _estimator(name, **params)),
    ]).fit(X, y)


def predicted_probability(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)


def evaluate(model, X, y, threshold=0.5):
    """Balanced accuracy, AUROC, AUPRC, sensitivity and specificity at a threshold."""
    probability = predicted_probability(model, X)
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    single_class = len(np.unique(y)) < 2
    return {
        "balanced_accuracy": balanced_accuracy_score(y, predicted),
        "auroc": np.nan if single_class else roc_auc_score(y, probability),
        "auprc": np.nan if single_class else average_precision_score(y, probability),
        "sensitivity": tp / max(tp + fn, 1),
        "specificity": tn / max(tn + fp, 1),
    }


def compare_models(names, X_train, y_train, X_test, y_test, **params):
    """Fit several models on one split and return a tidy comparison table."""
    rows = []
    for name in names:
        model = train_model(name, X_train, y_train, **params.get(name, {}))
        metrics = evaluate(model, X_test, y_test)
        rows.append({"model": name, **metrics})
    return pd.DataFrame(rows).set_index("model").round(3)


def sweep_parameter(name, parameter, values, X_train, y_train, X_test, y_test, metric="balanced_accuracy", **fixed):
    """Refit one model across a range of a single hyperparameter.

    Returns (values, train_scores, test_scores) so the notebooks can draw the
    overfitting gap rather than just print a number.
    """
    train_scores, test_scores = [], []
    for value in values:
        model = train_model(name, X_train, y_train, **{parameter: value}, **fixed)
        train_scores.append(evaluate(model, X_train, y_train)[metric])
        test_scores.append(evaluate(model, X_test, y_test)[metric])
    return list(values), train_scores, test_scores


def cross_validated_score(name, X, y, groups=None, folds=5, metric="balanced_accuracy", **params):
    """Cross-validation, grouped when groups are supplied. Returns the fold scores."""
    scoring = {"balanced_accuracy": "balanced_accuracy", "auroc": "roc_auc", "auprc": "average_precision"}[metric]
    pipeline = Pipeline([("preprocess", make_preprocessor(X)), ("model", _estimator(name, **params))])
    if groups is None:
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_SEED)
        return cross_val_score(pipeline, X, y, cv=splitter, scoring=scoring)
    splitter = GroupKFold(n_splits=folds)
    return cross_val_score(pipeline, X, y, cv=splitter, groups=groups, scoring=scoring)

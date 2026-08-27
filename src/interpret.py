"""Model interpretability: exact Shapley values, computed from the definition.

The popular ``shap`` package *approximates* Shapley values, because real models
have hundreds of features. Our tabular modules have fewer than a dozen, so we
can compute the *exact* values by enumerating every coalition of features, which
means students see the actual definition instead of a library call:

    phi_i  =  sum over coalitions S that exclude feature i of
              [ |S|! (n-|S|-1)! / n! ] * ( v(S + i) - v(S) )

The value function v(S) is "what does the model predict when it may only look at
the features in S?". We build that the standard way: take the person being
explained, overwrite every feature outside S with the corresponding value from a
background person, and average the prediction over many background people.

Cost is 2^n_features x n_background predictions per person, so the number of
features is capped. Eight features and forty background rows takes a couple of
seconds on a laptop.
"""
from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd

MAX_FEATURES = 10


def _predict(model, frame):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(frame)[:, 1]
    return model.decision_function(frame)


def _coalition_values(model, target_rows, background, features):
    """Return (coalitions, values) where values[i, c] = v(coalition c) for row i."""
    coalitions = [frozenset(subset) for size in range(len(features) + 1)
                  for subset in combinations(features, size)]
    columns = list(background.columns)
    positions = {name: columns.index(name) for name in features}
    background_values = background.to_numpy()
    n_background = len(background_values)

    blocks = []
    for row_position in range(len(target_rows)):
        target = target_rows.iloc[row_position].to_numpy()
        for coalition in coalitions:
            block = background_values.copy()
            for feature in coalition:
                block[:, positions[feature]] = target[positions[feature]]
            blocks.append(block)

    stacked = pd.DataFrame(np.concatenate(blocks, axis=0), columns=columns)
    stacked = stacked.astype(background.dtypes.to_dict(), errors="ignore")
    predictions = _predict(model, stacked)
    values = predictions.reshape(len(target_rows), len(coalitions), n_background).mean(axis=2)
    return coalitions, values


def shapley_values(model, X_explain, X_background, features=None, max_background=40):
    """Exact Shapley values for every row of ``X_explain``.

    Returns a DataFrame with one row per explained record and one column per
    feature. A positive value means "this person's value for this feature pushed
    the predicted risk *up*, relative to a typical person in the background set".
    """
    features = list(features if features is not None else X_explain.columns)
    if len(features) > MAX_FEATURES:
        raise ValueError(
            f"Exact Shapley values enumerate 2^n coalitions, and {len(features)} features is too many. "
            f"Choose at most {MAX_FEATURES} features, or use the `shap` package's approximation."
        )
    background = X_background.sample(min(max_background, len(X_background)), random_state=0)
    coalitions, values = _coalition_values(model, X_explain, background, features)
    position_of = {coalition: index for index, coalition in enumerate(coalitions)}

    n_features = len(features)
    weights = {size: factorial(size) * factorial(n_features - size - 1) / factorial(n_features)
               for size in range(n_features)}

    output = np.zeros((len(X_explain), n_features))
    for feature_position, feature in enumerate(features):
        others = [name for name in features if name != feature]
        for size in range(n_features):
            weight = weights[size]
            for subset in combinations(others, size):
                without = position_of[frozenset(subset)]
                with_it = position_of[frozenset(subset + (feature,))]
                output[:, feature_position] += weight * (values[:, with_it] - values[:, without])
    return pd.DataFrame(output, columns=features, index=X_explain.index)


def baseline_prediction(model, X_background, max_background=40):
    """v(empty set): the model's average prediction over the background people."""
    background = X_background.sample(min(max_background, len(X_background)), random_state=0)
    return float(_predict(model, background).mean())


def shapley_importance(shapley_frame):
    """Global importance: the average size of each feature's contribution."""
    return shapley_frame.abs().mean().sort_values(ascending=False)


def explain_one(model, X_explain, X_background, row=0, features=None, max_background=40):
    """Shapley values for a single person, as a Series sorted from negative to positive."""
    frame = shapley_values(model, X_explain.iloc[[row]], X_background,
                           features=features, max_background=max_background)
    return frame.iloc[0].sort_values()

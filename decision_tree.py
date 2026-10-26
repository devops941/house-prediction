"""
A small from-scratch CART regression tree.

Used in place of sklearn.tree.DecisionTreeRegressor because this machine's
Application Control (WDAC) policy blocks the compiled Cython extension that
scikit-learn's tree module depends on (sklearn/neighbors/_quad_tree). This
class exposes the same fit/predict API and is a drop-in replacement for the
comparison against Linear Regression described in the project spec.

Algorithm: greedy recursive binary splitting. At each node, every feature's
candidate thresholds (midpoints between sorted unique values) are evaluated
and the split that most reduces the sum of squared errors (SSE) is chosen --
the same criterion sklearn's DecisionTreeRegressor uses by default (MSE).
"""

import numpy as np


class SimpleDecisionTreeRegressor:
    def __init__(self, max_depth=5, min_samples_split=10):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree_ = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self.tree_ = self._grow(X, y, depth=0)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return np.array([self._predict_one(row, self.tree_) for row in X])

    def _grow(self, X, y, depth):
        node_value = y.mean()
        if depth >= self.max_depth or len(y) < self.min_samples_split or np.all(y == y[0]):
            return {"leaf": True, "value": node_value}

        split = self._best_split(X, y)
        if split is None:
            return {"leaf": True, "value": node_value}

        feature, threshold, left_idx, right_idx = split
        return {
            "leaf": False,
            "feature": feature,
            "threshold": threshold,
            "left": self._grow(X[left_idx], y[left_idx], depth + 1),
            "right": self._grow(X[right_idx], y[right_idx], depth + 1),
        }

    @staticmethod
    def _sse(values):
        return np.sum((values - values.mean()) ** 2) if len(values) else 0.0

    def _best_split(self, X, y):
        n_features = X.shape[1]
        parent_sse = self._sse(y)
        best_gain, best = 0.0, None

        for feature in range(n_features):
            values = X[:, feature]
            uniques = np.unique(values)
            if len(uniques) < 2:
                continue
            thresholds = (uniques[:-1] + uniques[1:]) / 2.0

            for threshold in thresholds:
                left_idx = values <= threshold
                right_idx = ~left_idx
                if left_idx.sum() == 0 or right_idx.sum() == 0:
                    continue
                gain = parent_sse - (self._sse(y[left_idx]) + self._sse(y[right_idx]))
                if gain > best_gain:
                    best_gain = gain
                    best = (feature, threshold, left_idx, right_idx)

        return best

    def _predict_one(self, row, node):
        while not node["leaf"]:
            node = node["left"] if row[node["feature"]] <= node["threshold"] else node["right"]
        return node["value"]

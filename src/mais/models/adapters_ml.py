"""Concrete ML adapters: LightGBM, XGBoost, RandomForest.

Imported lazily by registry.py - if the underlying lib isn't installed,
the adapter is silently skipped.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .base import ModelAdapter


class LightGBMAdapter(ModelAdapter):

    def fit(self, X, y, X_val=None, y_val=None):
        import lightgbm as lgb
        params = {
            "objective":     self.params.get("objective", "regression"),
            "learning_rate": self.params.get("learning_rate", 0.03),
            "num_leaves":    self.params.get("num_leaves", 31),
            "feature_fraction": self.params.get("feature_fraction", 0.8),
            "bagging_fraction": self.params.get("bagging_fraction", 0.8),
            "min_data_in_leaf": self.params.get("min_data_in_leaf", 50),
            "lambda_l2":     self.params.get("lambda_l2", 1.0),
            "verbose":       -1,
        }
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)
        mask = y.notna()
        Xc = Xc.loc[mask]; yc = y.loc[mask]
        self._cols = list(Xc.columns)
        train_set = lgb.Dataset(Xc.values, label=yc.values)
        valid_sets = [train_set]
        if X_val is not None and y_val is not None:
            Xv = X_val.select_dtypes(include=[np.number]).fillna(0.0)[self._cols]
            mv = y_val.notna()
            valid_sets.append(lgb.Dataset(Xv.loc[mv].values, label=y_val.loc[mv].values))
        self._booster = lgb.train(
            params, train_set,
            num_boost_round=self.params.get("n_estimators", 300),
            valid_sets=valid_sets,
            callbacks=[lgb.log_evaluation(0)],
        )
        self._fitted = True
        return self

    def predict(self, X):
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)[self._cols]
        return self._booster.predict(Xc.values)


class XGBoostAdapter(ModelAdapter):

    def fit(self, X, y, X_val=None, y_val=None):
        import xgboost as xgb
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)
        mask = y.notna()
        Xc = Xc.loc[mask]; yc = y.loc[mask]
        self._cols = list(Xc.columns)
        params = {
            "objective": "reg:squarederror",
            "learning_rate": self.params.get("learning_rate", 0.03),
            "max_depth": self.params.get("max_depth", 6),
            "subsample": self.params.get("subsample", 0.8),
            "colsample_bytree": self.params.get("colsample_bytree", 0.8),
            "verbosity": 0,
        }
        self._model = xgb.XGBRegressor(
            n_estimators=self.params.get("n_estimators", 1000),
            **params,
        )
        eval_set = None
        if X_val is not None and y_val is not None:
            Xv = X_val.select_dtypes(include=[np.number]).fillna(0.0)[self._cols]
            mv = y_val.notna()
            eval_set = [(Xv.loc[mv].values, y_val.loc[mv].values)]
        self._model.fit(Xc.values, yc.values, eval_set=eval_set, verbose=False)
        self._fitted = True
        return self

    def predict(self, X):
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)[self._cols]
        return self._model.predict(Xc.values)


class RandomForestAdapter(ModelAdapter):

    def fit(self, X, y, X_val=None, y_val=None):
        from sklearn.ensemble import RandomForestRegressor
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)
        mask = y.notna()
        Xc = Xc.loc[mask]; yc = y.loc[mask]
        self._cols = list(Xc.columns)
        self._model = RandomForestRegressor(
            n_estimators=self.params.get("n_estimators", 500),
            max_depth=self.params.get("max_depth", 20),
            min_samples_leaf=self.params.get("min_samples_leaf", 5),
            n_jobs=-1,
            random_state=self.params.get("random_state", 42),
        )
        self._model.fit(Xc.values, yc.values)
        self._fitted = True
        return self

    def predict(self, X):
        Xc = X.select_dtypes(include=[np.number]).fillna(0.0)[self._cols]
        return self._model.predict(Xc.values)

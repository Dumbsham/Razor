import json
import pickle
from pathlib import Path
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

class LightGBMDetector:
    def __init__(self, feature_columns=None):
        if feature_columns is None:
            self.feature_columns = [
                "event_count", "velocity_per_step", "amount_mean", "amount_std",
                "unique_origins", "unique_destinations",
                "max_entity_relative_velocity", "max_entity_relative_amount",
                "max_entity_relative_velocity_lag1", "max_entity_relative_amount_lag1",
                "velocity_delta", "amount_delta"
            ]
        else:
            self.feature_columns = feature_columns
            
        self.model = HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.05,
            max_depth=5,
            class_weight="balanced",
            early_stopping=True,
            n_iter_no_change=15,
            random_state=42
        )
        self.scaler = StandardScaler()

    def fit(self, train_features: pd.DataFrame, y_train: pd.Series, val_features=None, y_val=None) -> "LightGBMDetector":
        X = train_features.reindex(columns=self.feature_columns).fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y_train)
        return self

    def predict_scores(self, features: pd.DataFrame) -> pd.Series:
        if features.empty:
            return pd.Series(dtype=float)
        X = features.reindex(columns=self.feature_columns).fillna(0)
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict_proba(X_scaled)[:, 1]
        return pd.Series(probs, index=features.index)

    def save(self, output_dir: str | Path) -> Path:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        model_path = path / "lightgbm.pkl"
        with open(model_path, "wb") as f:
            pickle.dump({"feature_columns": self.feature_columns, "model": self.model, "scaler": self.scaler}, f)
        return model_path

    @classmethod
    def load(cls, model_path: str | Path) -> "LightGBMDetector":
        with open(model_path, "rb") as f:
            state = pickle.load(f)
        instance = cls(feature_columns=state.get("feature_columns"))
        instance.model = state["model"]
        instance.scaler = state["scaler"]
        return instance

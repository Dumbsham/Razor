"""Explainable baseline anomaly detection using rolling z-scores."""

import json
from pathlib import Path
import pandas as pd

class BaselineZScoreModel:
    """A baseline model that scores windows based on z-scores of selected features."""
    
    def __init__(self, feature_columns: list[str] = None):
        if feature_columns is None:
            self.feature_columns = [
                "event_count", 
                "velocity_per_step", 
                "amount_mean", 
                "unique_destinations",
                "repetition_ratio"
            ]
        else:
            self.feature_columns = feature_columns
            
        self.means_ = {}
        self.stds_ = {}

    def fit(self, train_features: pd.DataFrame) -> "BaselineZScoreModel":
        """Calculate and store the mean and standard deviation from training data."""
        for col in self.feature_columns:
            if col in train_features.columns:
                self.means_[col] = float(train_features[col].mean())
                std = float(train_features[col].std(ddof=0))
                # Prevent division by zero
                self.stds_[col] = std if std > 1e-6 else 1e-6
            else:
                self.means_[col] = 0.0
                self.stds_[col] = 1.0
        return self

    def predict_scores(self, features: pd.DataFrame) -> pd.Series:
        """Score each window by the maximum z-score among monitored features.
        
        Returns a series of anomaly scores (higher is more anomalous).
        """
        if features.empty:
            return pd.Series(dtype=float)
            
        z_scores = pd.DataFrame(index=features.index)
        for col in self.feature_columns:
            if col in features.columns:
                mean = self.means_.get(col, 0.0)
                std = self.stds_.get(col, 1.0)
                # Compute absolute z-score
                z_scores[col] = (features[col] - mean).abs() / std
                
        # The anomaly score is the max z-score across all monitored features
        anomaly_score = z_scores.max(axis=1)
        return anomaly_score

    def predict(self, features: pd.DataFrame, threshold: float = 3.0) -> pd.Series:
        """Predict binary anomaly flags based on a z-score threshold."""
        scores = self.predict_scores(features)
        return scores > threshold

    def save(self, output_dir: str | Path) -> Path:
        """Save the fitted model parameters."""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        model_path = path / "baseline_zscore.json"
        
        state = {
            "feature_columns": self.feature_columns,
            "means": self.means_,
            "stds": self.stds_
        }
        model_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        return model_path

    @classmethod
    def load(cls, model_path: str | Path) -> "BaselineZScoreModel":
        """Load a fitted model from JSON."""
        path = Path(model_path)
        state = json.loads(path.read_text(encoding="utf-8"))
        model = cls(feature_columns=state.get("feature_columns"))
        model.means_ = state.get("means", {})
        model.stds_ = state.get("stds", {})
        return model

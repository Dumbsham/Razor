"""Primary anomaly detector using scikit-learn Isolation Forest."""

import pickle
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class IsolationForestModel:
    """An unsupervised anomaly detector using Isolation Forest."""
    
    def __init__(self, contamination: float = 0.01, random_state: int = 42, feature_columns: list[str] = None):
        if feature_columns is None:
            self.feature_columns = [
                "event_count", "velocity_per_step", "amount_mean", "amount_std",
                "amount_deviation", "mean_interarrival_steps", "unique_origins",
                "unique_destinations", "destination_entropy", "amount_entropy", "repetition_ratio"
            ]
        else:
            self.feature_columns = feature_columns
            
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.scaler = StandardScaler()

    def fit(self, train_features: pd.DataFrame) -> "IsolationForestModel":
        """Fit the scaler and model on training data (normal behavior)."""
        # Ensure all columns exist, fill missing if any
        X = train_features.reindex(columns=self.feature_columns).fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        return self

    def predict_scores(self, features: pd.DataFrame) -> pd.Series:
        """Compute anomaly score. 
        
        IsolationForest.score_samples returns negative anomaly score:
        lower values -> more anomalous.
        We invert it so higher values indicate higher anomaly severity.
        """
        if features.empty:
            return pd.Series(dtype=float)
            
        X = features.reindex(columns=self.feature_columns).fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Raw scores from IF are typically negative. We negate to make positive = anomalous.
        scores = -self.model.score_samples(X_scaled)
        return pd.Series(scores, index=features.index)

    def predict(self, features: pd.DataFrame, threshold: float = None) -> pd.Series:
        """Predict binary anomaly flags.
        
        If threshold is None, use the model's default internal decision_function.
        Otherwise, use the custom threshold on our inverted scores.
        """
        if threshold is None:
            X = features.reindex(columns=self.feature_columns).fillna(0)
            X_scaled = self.scaler.transform(X)
            # IF returns -1 for outliers and 1 for inliers. We want True for anomalies.
            preds = self.model.predict(X_scaled)
            return pd.Series(preds == -1, index=features.index)
        else:
            scores = self.predict_scores(features)
            return scores > threshold

    def save(self, output_dir: str | Path) -> Path:
        """Save the fitted model and scaler using pickle."""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        model_path = path / "isolation_forest.pkl"
        
        with open(model_path, "wb") as f:
            pickle.dump({
                "feature_columns": self.feature_columns,
                "model": self.model,
                "scaler": self.scaler
            }, f)
            
        return model_path

    @classmethod
    def load(cls, model_path: str | Path) -> "IsolationForestModel":
        """Load a fitted model from pickle."""
        path = Path(model_path)
        with open(path, "rb") as f:
            state = pickle.load(f)
            
        instance = cls(feature_columns=state.get("feature_columns"))
        instance.model = state["model"]
        instance.scaler = state["scaler"]
        return instance

import pandas as pd

def explain_alert(window_features: pd.Series, train_means: dict, train_stds: dict) -> list[dict]:
    """Provide top contributing reasons for a flagged anomaly window without exposing raw numbers."""
    contributions = []
    # Identify which features are most standard deviations away from normal
    for col, mean in train_means.items():
        std = train_stds.get(col, 1.0)
        # Avoid division by zero
        if std == 0:
            std = 1.0
        # Ensure we can access the column, skip if missing
        if col not in window_features:
            continue
            
        z = (window_features[col] - mean) / std
        if z > 2.0:
            contributions.append({"feature": col, "deviation": z})
            
    # Sort by standard deviation deviation
    sorted_reasons = sorted(contributions, key=lambda x: x["deviation"], reverse=True)[:3]
    
    # Translate features to natural language
    translation = {
        "event_count": "Sudden volume spike",
        "velocity_per_step": "High velocity burst",
        "amount_mean": "Abnormally high transaction amounts",
        "amount_deviation": "High variation in transaction amounts",
        "unique_origins": "High volume of origin accounts",
        "unique_destinations": "High volume of destination accounts",
        "destination_entropy": "Unusual destination distribution",
        "amount_entropy": "Unusual amount distribution",
        "repetition_ratio": "Highly repetitive behavior",
        "mean_interarrival_steps": "Long gaps between transactions",
        "max_entity_relative_velocity": "Entity transaction velocity spike",
        "max_entity_relative_amount": "Entity transaction amount spike"
    }
    
    return [
        {
            "signal": translation.get(r["feature"], r["feature"]),
            "contribution_level": "High" if r["deviation"] > 4.0 else "Medium"
        }
        for r in sorted_reasons
    ]

#!/bin/bash
set -e
echo "Running full pipeline..."

# Day 1: Ingestion
echo "Running ingestion..."
PYTHONPATH=. python scripts/run_ingestion.py

# Day 2: Synthetic spikes
echo "Generating synthetic spikes..."
PYTHONPATH=. python scripts/generate_synthetic_spikes.py

# Day 3: Features
echo "Building features..."
PYTHONPATH=. python scripts/build_features.py
PYTHONPATH=. python scripts/plot_features.py

# Day 4 & 5: Models
echo "Running models..."
PYTHONPATH=. python scripts/run_models.py

# Day 6: Validation Metrics Plot
echo "Plotting validation metrics..."
PYTHONPATH=. python scripts/plot_validation_metrics.py

# Day 7: Test Evaluation
echo "Running test evaluation..."
PYTHONPATH=. python scripts/run_test_evaluation.py

echo "Pipeline completed successfully!"
PYTHONPATH=. python scripts/freeze_demo_scenario.py

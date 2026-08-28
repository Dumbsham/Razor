# Beginner's Guide: Understanding the PaySim Anomaly Detection Project

Welcome! This guide explains exactly how this project works from start to finish, what happens behind the scenes, and what you see on the screen. 

## What is this project?
This project is an **Anomaly (Fraud) Detection System** built on transaction data (like PaySim). Since real fraud is rare and constantly changing, the system looks at a stream of transactions and tries to flag abnormal behavior (like a sudden burst of transactions or unusual amounts) in near real-time.

---

## 1. How the Project Works (The Data Pipeline)

### Step 1: Getting the Data (Ingestion)
*(Relevant file: `src/ingestion.py`)*
Raw transaction logs (who sent money to whom, when, and how much) are loaded into the system.

### Step 2: Creating "Features" (The Rolling Window)
*(Relevant files: `src/features.py`, `scripts/build_features.py`)*
Instead of looking at one transaction in isolation, the system looks at the **recent history** (a rolling window).
For example, at Time Step 100, the system looks at the last 6 steps (Time Steps 94 to 99) and calculates summaries, called **Features**:
*   How many transactions happened? (`event_count`)
*   What was the average amount? (`amount_mean`)
*   How many unique accounts received money? (`unique_destinations`)

By summarizing the data this way, the machine learning models can easily spot sudden changes in behavior.

### Step 3: Injecting Synthetic "Spikes" (For Testing)
*(Relevant file: `scripts/generate_synthetic_spikes.py`)*
Because real fraud is extremely rare, we need a way to test if our AI actually works. The project injects "fake" fraud—called **Synthetic Spikes**—into the data. 
*   Example: Suddenly generating 100 rapid transactions in a single time step (a "velocity attack"). 
This gives the models something to practice on and allows us to measure if they successfully catch the attacks.

### Step 4: The Machine Learning Models
*(Relevant files: `src/models/baseline_zscore.py`, `src/models/isolation_forest.py`, `scripts/run_models.py`)*
Once the features are calculated, they are fed into machine learning models. This project has a few models:
1.  **Baseline Z-Score**: A simple statistical rule. It checks if the current features (like the transaction count) are wildly higher than the historical average.
2.  **Isolation Forest**: A more advanced AI algorithm. It "isolates" anomalies by looking for data points that are very different from the rest of the dataset.

The model looks at a window of data and outputs an **Anomaly Score**. If the score crosses a certain **Threshold**, the system flags it as a Fraud Alert.

### Step 5: Explainability
*(Relevant file: `src/explain.py`)*
When the AI flags an alert, a human investigator needs to know *why*. The explainability module looks at the math and translates it into human-readable reasons, like:
*   *"Abnormally high transaction amounts"*
*   *"Sudden volume spike"*

---

## 2. What is Showing on the Screen? (The Dashboard)
*(Relevant files: `app/streamlit_app.py`, `app/api.py`)*
All of the complex math and AI happening in the background is surfaced to the user via a clean, web-based dashboard built using **Streamlit**.

When you run the dashboard, you see two main tabs:

### 🔴 Tab 1: Live Alerts Stream (The Replay)
This tab acts like a video player for the transaction stream.
*   **The Slider**: You can drag a slider to change the "Current Time Step". This simulates time moving forward in the real world.
*   **The Chart**: A line graph shows the AI's anomaly score moving up and down over time.
*   **Active Alerts (The Cards)**: When the anomaly score crosses the danger threshold, a Red Alert Card pops up. It tells you:
    *   The exact time the suspicious activity happened.
    *   The Anomaly Score.
    *   **The Primary Risk Factors**: The human-readable explanation of *why* the AI got triggered (e.g., "High velocity burst").

### 📊 Tab 2: Impact & Metrics (The Report Card)
*(Relevant files: `src/evaluate.py`, `scripts/run_test_evaluation.py`)*
This tab is for the business managers to understand how well the AI is performing overall.
*   **Performance Metrics**: Numbers like Precision (how often the AI is right when it cries wolf) and Recall (how much of the total fraud the AI actually caught).
*   **Total Expected Cost**: A business calculation that puts a rupee value on the AI's performance (balancing the cost of investigating false alarms vs. the cost of missing actual fraud).
*   **Charts**: Visual curves showing the tradeoffs between catching more fraud and spending more money on investigations.

---

## 3. How to Present This Project to a Judge

When presenting to a hackathon judge or stakeholder, focus on **business value**, **practicality**, and **scalability**, rather than getting lost in the technical weeds. Here is a suggested script/flow:

### 1. The Hook (The Problem)
*   *"Traditional fraud detection focuses on single transactions. But fraudsters are smart—they blend in using hundreds of tiny transactions over hours."*
*   *"Our system doesn't just look at one transaction; it monitors the **behavioral stream** over time to catch these coordinated attacks (like velocity bursts)."*

### 2. The Demo (Show, Don't Tell)
*   **Open the Streamlit Dashboard (Tab 1).**
*   Move the slider to simulate time passing. Show how the background anomaly score fluctuates quietly during normal hours.
*   Slide to a known "Spike" period and watch the red alert pop up.
*   **Highlight Explainability:** Point to the "Primary Risk Factors". Say: *"We don't just give investigators a black-box AI score. We tell them exactly what triggered the alarm, drastically reducing investigation time."*

### 3. The Business Value (Tab 2)
*   Switch to the **Impact & Metrics** tab.
*   *"We know false positives are the bane of fraud teams. They waste time and frustrate real customers."*
*   Show the **Total Expected Cost** metric.
*   *"We didn't just optimize for AI metrics like F1 score; we optimized our thresholds to minimize actual **rupee cost** to the business, balancing the cost of friction against the cost of lost funds."*

### 4. Technical Rigor (Briefly Mention)
*   *"We validated this using rigorous, chronological data splits so our model wouldn't 'cheat' by looking at future data. We also injected synthetic spikes to guarantee it works on modern, coordinated attacks."*

---

## Summary of the Flow
1. **Raw Data** comes in (`src/ingestion.py`).
2. It's converted into **Rolling Features** (`src/features.py`).
3. **Synthetic Spikes** are injected to test the system (`scripts/generate_synthetic_spikes.py`).
4. The **AI Model** scores the features (`src/models/isolation_forest.py`).
5. If the score is high, the **Explainability** module figures out why (`src/explain.py`).
6. The **Streamlit Dashboard** shows the alerts and explanations to the user (`app/streamlit_app.py`)!

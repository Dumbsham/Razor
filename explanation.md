# Beginner's Guide: Understanding the PaySim Anomaly Detection Project

Welcome! This guide explains exactly how this project works from start to finish, what happens behind the scenes, and what you see on the screen. 

## What is this project?
This project is an **Anomaly (Fraud) Detection System** built on transaction data (like PaySim). Since real fraud is rare and constantly changing, the system looks at a stream of transactions and tries to flag abnormal behavior (like a sudden burst of transactions or unusual amounts) in near real-time.

---

## 1. How the Project Works (The Data Pipeline)

### Step 1: Getting the Data (Ingestion)
*(You can skip this if you're already familiar with it!)*
Raw transaction logs (who sent money to whom, when, and how much) are loaded into the system.

### Step 2: Creating "Features" (The Rolling Window)
Instead of looking at one transaction in isolation, the system looks at the **recent history** (a rolling window).
For example, at Time Step 100, the system looks at the last 6 steps (Time Steps 94 to 99) and calculates summaries, called **Features**:
*   How many transactions happened? (`event_count`)
*   What was the average amount? (`amount_mean`)
*   How many unique accounts received money? (`unique_destinations`)

By summarizing the data this way, the machine learning models can easily spot sudden changes in behavior.

### Step 3: Injecting Synthetic "Spikes" (For Testing)
Because real fraud is extremely rare, we need a way to test if our AI actually works. The project injects "fake" fraud—called **Synthetic Spikes**—into the data. 
*   Example: Suddenly generating 100 rapid transactions in a single time step (a "velocity attack"). 
This gives the models something to practice on and allows us to measure if they successfully catch the attacks.

### Step 4: The Machine Learning Models
Once the features are calculated, they are fed into machine learning models. This project has a few models:
1.  **Baseline Z-Score**: A simple statistical rule. It checks if the current features (like the transaction count) are wildly higher than the historical average.
2.  **Isolation Forest**: A more advanced AI algorithm. It "isolates" anomalies by looking for data points that are very different from the rest of the dataset.

The model looks at a window of data and outputs an **Anomaly Score**. If the score crosses a certain **Threshold**, the system flags it as a Fraud Alert.

### Step 5: Explainability
When the AI flags an alert, a human investigator needs to know *why*. The explainability module looks at the math and translates it into human-readable reasons, like:
*   *"Abnormally high transaction amounts"*
*   *"Sudden volume spike"*

---

## 2. What is Showing on the Screen? (The Dashboard)

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
This tab is for the business managers to understand how well the AI is performing overall.
*   **Performance Metrics**: Numbers like Precision (how often the AI is right when it cries wolf) and Recall (how much of the total fraud the AI actually caught).
*   **Total Expected Cost**: A business calculation that puts a rupee value on the AI's performance (balancing the cost of investigating false alarms vs. the cost of missing actual fraud).
*   **Charts**: Visual curves showing the tradeoffs between catching more fraud and spending more money on investigations.

---

## Summary of the Flow
1. **Raw Data** comes in.
2. It's converted into **Rolling Features**.
3. **Synthetic Spikes** are injected to test the system.
4. The **AI Model** scores the features.
5. If the score is high, the **Explainability** module figures out why.
6. The **Streamlit Dashboard** shows the alerts and explanations to the user!

# Run & Deploy Guide

This guide covers how to set up the Fraud-Spike Detector project on your local machine and how to deploy it to production.

---
~
## 1. Local Setup & Running

### Prerequisites
- **Python 3.11+**
- **uv** (Package manager for Python): Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js 18+ & npm** (If using the Next.js frontend)

### Step 1: Install Dependencies
At the root of the project, use `uv` to install the Python dependencies and create a virtual environment:
```bash
uv sync --all-groups
```

### Step 2: Run the Data Pipeline
Ensure that `Paysim.csv` is present in the root directory. Then, generate features, train the models, and evaluate the metrics by running the master script:
```bash
# This runs ingestion, spike generation, feature extraction, and evaluation
bash scripts/run_all.sh
```

### Step 3: Start the Interfaces

You can interact with the project via the built-in Streamlit dashboard or the Next.js + FastAPI setup.

**Option A: Streamlit Dashboard (Recommended for quick testing)**
```bash
uv run streamlit run app/streamlit_app.py
```
*The dashboard will be available at `http://localhost:8501`*

**Option B: FastAPI Backend + Next.js Frontend**
1. **Start the API Server:**
   ```bash
   uv run uvicorn app.api:app --reload
   ```
   *The API will be available at `http://localhost:8000` (Docs at `/docs`)*

2. **Start the Next.js Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *The frontend will be available at `http://localhost:3000`*

---

## 2. Deployment Guide

### A. Deploying the Streamlit App (Easiest Method)
The fastest way to deploy the Streamlit dashboard is via **Streamlit Community Cloud**.

1. Generate a `requirements.txt` file (Streamlit Cloud does not natively use `uv.lock` by default):
   ```bash
   uv export --format requirements-txt > requirements.txt
   ```
2. Commit and push your code to a public or private GitHub repository.
3. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
4. Click **New app**, select your repository, and set the **Main file path** to `app/streamlit_app.py`.
5. Click **Deploy**.

### B. Deploying the FastAPI Backend (Render / Heroku / GCP)
If you are deploying the API for the Next.js app to consume:

1. **Create a `Dockerfile`** at the root of your project:
   ```dockerfile
   FROM python:3.11-slim
   
   # Install uv
   RUN pip install uv
   
   WORKDIR /app
   COPY . /app
   
   # Install dependencies
   RUN uv sync --no-dev
   
   # Expose the API port
   EXPOSE 8000
   
   # Command to run the API
   CMD ["uv", "run", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. Push this to **Render** (via Docker Web Service), **Google Cloud Run**, or **AWS ECS**.

### C. Deploying the Next.js Frontend (Vercel)
If you are using the custom Next.js UI:

1. Create a free account on [Vercel](https://vercel.com/).
2. Click **Add New... > Project** and import your GitHub repository.
3. Set the **Root Directory** to `frontend`.
4. Ensure the **Build Command** is `npm run build` and **Install Command** is `npm install`.
5. Add an Environment Variable for your backend API URL:
   - `NEXT_PUBLIC_API_URL` = `<URL_OF_YOUR_DEPLOYED_FASTAPI_BACKEND>`
6. Click **Deploy**.

> **Note on Data:** For production, ensure your pre-processed window features (`data/processed/test/window_features_v1.csv`), the frozen model (`isolation_forest.pkl`), and `optimal_threshold.json` are committed or uploaded to your deployment server so the API and Dashboard can load the data without needing to re-run the pipeline.

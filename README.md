# Agentic AI Data Preprocessing & Quality Analyst

A privacy-first, deterministic-backed **Agentic AI Data Preprocessing and Quality Analysis Platform** built with **FastAPI**, **Pandas**, **Scikit-Learn**, **React (Vite)**, and a local **Small Language Model (`Qwen2.5 1.5B` via Ollama)** running 100% on CPU.

---

## Why This Architecture?

Most AI data-cleaning tools ask an LLM to compute statistics or execute arbitrary Python/SQL code on raw datasets—leading to hallucinated numbers, data privacy leaks, and unsafe code execution.

This platform solves that using a **Deterministic-First, Constrained-SLM Architecture**:
1. **100% Deterministic Math & Execution**: `Pandas`, `NumPy`, `SciPy`, and `Scikit-Learn` compute all dataset profiles, 16-point quality scans, statistical outlier bounds, and data transformations.
2. **Privacy-Preserving Local AI Planning**: Only a compact JSON metadata digest (never raw sensitive records) is sent to local `Qwen2.5 1.5B` via Ollama (`http://127.0.0.1:11434`).
3. **Strict Schema Validation & Self-Correction**: Model outputs are validated against strict **Pydantic** JSON schemas. If the model hallucinates a column name or operation, a self-correction retry loop repairs the response or falls back to a deterministic rule planner.
4. **Zero Arbitrary Code Execution**: No `eval()`, `exec()`, or shell commands. Only allowlisted Python functions approved by the user are executed.

---

## Multi-Agent Pipeline Architecture

| Logical Agent | Backend Module | Responsibility |
| :--- | :--- | :--- |
| **1. Dataset Profiling Agent** | `app/services/profiler.py` | Computes row/column dimensions, memory footprint, missingness, exact duplicates, numeric distributions, top categories, and semantic column classifications (`numeric`, `categorical`, `boolean`, `datetime`, `identifier`, `text`). |
| **2. Quality Analysis Agent** | `app/services/quality_analyzer.py` | Runs 16 deterministic checks separating **confirmed issues** from **potential anomalies**: missing values, exact/fuzzy duplicates, duplicate IDs, 1.5x IQR & Modified Z-Score (MAD) outliers, numbers stored as strings, mixed dates, zero-variance columns, skewness, multicollinearity, target class imbalance, and ML data leakage. |
| **3. AI Planning Agent** | `app/services/recommendation_planner.py` | Queries local `qwen2.5:1.5b` via Ollama with user goals and target columns, enforces Pydantic JSON schemas, and provides offline deterministic fallback. |
| **4. Preprocessing Execution Agent** | `app/services/transformation_engine.py` | Executes 15 allowlisted operations with dry-run effect previews, identifier protection, and leak-free Train/Test split fitting. |
| **5. Validation Agent** | `app/services/validation_engine.py` | Verifies post-transformation invariants (non-empty dataset, zero `Inf`/`-Inf` corruption, imputation/deduplication completeness) before committing snapshots. |
| **6. Reporting & Audit Agent** | `app/services/audit_logger.py` & `export_service.py` | Maintains disk-backed version history with single-click Undo/Restore, Before-vs-After comparisons, multi-format dataset exports (`CSV`, `XLSX`, `JSON`, `Parquet`), and downloadable `HTML`, `Markdown`, and `JSON` audit reports. |

---

## Key Features

- **Multi-Format Ingestion**: Supports `.csv` (with multi-encoding fallback), `.xlsx`, `.xls`, `.json`, and `.parquet` with upload size and row/column memory caps.
- **Automatic Header Standardization**: Normalizes messy headers (`Annual Salary ($)` -> `annual_salary`), resolves duplicate column names (`customer_id`, `customer_id_2`), and preserves an original-to-standardized mapping report.
- **Interactive Outlier Visualizer**: Renders 5-number summary boxplots (`Min`, `Q25`, `Median`, `Q75`, `Max`) and highlights extreme values detected by both **IQR** and **Modified Z-Score**.
- **Leak-Free ML Pipeline Studio**: Partitions data into `Train` and `Test` sets *before* fitting imputers, one-hot encoders, or scalers (`StandardScaler`, `MinMaxScaler`, `RobustScaler`) strictly on training rows.
- **Immutable Audit Trail & Time-Travel Undo**: Every approved operation saves a recoverable checkpoint (`v0`, `v1`, `v2`...) with single-click Undo and version restore.

---

## Project Structure

```text
agentic-data-analyst/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routers (datasets, profiling, quality, recommendations, transformations, exports)
│   │   ├── core/                # .env configuration loader, security limits & exception handlers
│   │   ├── schemas/             # Strict Pydantic v2 data contracts
│   │   ├── services/            # 6 modular deterministic & AI agent services
│   │   └── main.py              # FastAPI application entrypoint & security middleware
│   ├── tests/                   # Automated Pytest suite (Phases 1–7)
│   ├── .env.example             # Safe environment configuration template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Modular React UI components (Royal Blue, Pure White & Tomato Red theme)
│   │   ├── services/api.js      # Frontend API client
│   │   ├── App.jsx              # Main application workspace
│   │   └── index.css            # Design system & responsive styles
│   ├── package.json
│   └── vite.config.js
└── start_app.ps1                # One-click Windows PowerShell launcher
```

---

## Quick Start (Windows / CPU-Only)

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Ollama** (optional, for AI planning — system works deterministically even if Ollama is offline):
  ```powershell
  ollama pull qwen2.5:1.5b
  ```

### 1. Clone & Configure Environment
```powershell
git clone [https://github.com/](https://github.com/)Rubeshwaran15/agentic-data-analyst.git
cd agentic-data-analyst
Copy-Item "backend/.env.example" -Destination "backend/.env"
```

### 2. Backend Setup & Unit Tests
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --prefer-binary -r requirements.txt
python -m pytest -v
```

### 3. Frontend Setup
```powershell
cd ../frontend
npm install
```

### 4. Launch the Full Stack
From the project root (`agentic-data-analyst`), run:
```powershell
.\start_app.ps1
```
- **React Frontend UI**: `http://127.0.0.1:5173`
- **FastAPI Backend & Swagger Docs**: `http://127.0.0.1:8000/api/docs`

---

## Security & Reliability Guarantees

- **No Arbitrary Code Execution**: LLM outputs are never passed to `eval()`, `exec()`, or subprocesses.
- **Data Privacy**: Raw rows are never transmitted to external APIs; local Ollama receives only compact column-level statistics.
- **Original Data Immutability**: Uploaded files are stored read-only in `storage/originals/` and never overwritten.
- **Environment Isolation**: Secrets and local paths are managed via `.env` and excluded via `.gitignore`.
- **Security Headers**: Responses enforce `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and localhost-restricted CORS.

---

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic v2, Uvicorn, HTTPX
- **Data Science & ML**: Pandas, NumPy, SciPy, Scikit-Learn, PyArrow, OpenPyXL
- **Agentic AI**: Ollama Local Runtime, `Qwen2.5:1.5B` (Structured JSON Output)
- **Frontend**: React 18, Vite, Lucide Icons, Custom CSS Design System
- **Testing**: Pytest
# 🚀 Avito Real Estate Data Pipeline

End to end data engineering project that transforms raw real estate listings from **Avito.ma** into analytics ready datasets and machine learning features.

## 🔗 Project Evolution

This repository documents the earlier version of my Avito real estate data engineering work. It covers the core flow from Selenium extraction through PostgreSQL staging, cleaning, dimensional modeling, BI, and an ML feature store.

The evolved implementation is maintained separately in [real-estate-pipeline](https://github.com/badre2152/real-estate-pipeline). That repository extends the same project direction with a more mature structure, broader automation, documentation, and testing.

Both repositories are intentionally kept to show the technical evolution of the project rather than presenting them as unrelated duplicate projects.
---
## ⚠️ Disclaimer

This project is for educational purposes only.  
No personal data is collected or stored.  
Scraping is performed on publicly available listings with respectful rate limiting.
and all the data will not be shared and will be deleted within 2 weeks


## 📄 License
This project is licensed under the MIT License.
---

## 🎯 Project Overview

This project simulates a **production-grade data pipeline**:

* Extracts real estate listings via web scraping
* Processes and cleans raw data
* Loads structured data into a PostgreSQL Data Warehouse
* Serves analytics (BI) and Machine Learning use cases

---

## 🧱 Architecture

![Architecture](docs/architecture.png)

**Flow:**

```
Selenium Scraper
      ↓
Bronze Layer (JSON)
      ↓
PostgreSQL Staging
      ↓
Cleaning & Feature Engineering
      ↓
Data Warehouse (Star Schema)
      ↓
Power BI Dashboard
      ↓
ML Feature Store (OBT)
```

---

## 🛠️ Tech Stack

* **Python** → ETL & scraping
* **Selenium** → Data extraction
* **PostgreSQL** → Data warehouse
* **SQL** → Transformations & analytics
* **Streamlit / Power BI** → Data visualization

---

## 📊 Business Use Cases

* Track real estate price trends across cities
* Compare price per m² by location
* Identify high-value investment zones
* Build ML models for price prediction

---

## 🗂️ Project Structure

```
data_pipeline/
├── data/
│   ├── bronze/        # Raw JSON data
│   ├── silver/        # Cleaned CSV data
│   └── gold/          # Final outputs (BI/ML)
├── logs/
│   └── pipeline.log
├── src/
│   ├── extract/
│   ├── staging/
│   ├── clean/
│   ├── warehouse/
│   ├── utils/
│   └── main.py
├── docs/
├── requirements.txt
└── .env
```

---

## 🏗️ Data Warehouse Design

### Schemas

| Schema    | Purpose                   |
| --------- | ------------------------- |
| staging   | Raw temporary data        |
| clean     | Cleaned + enriched data   |
| bi_schema | Star schema for analytics |
| ml_schema | Feature store (ML)        |

### ⭐ Star Schema (BI)

```
fact_annonce
   ├── dim_localisation
   ├── dim_caracteristiques
   └── dim_temps
```

### 🤖 Feature Store (ML)

```
feature_store
→ prix (target)
→ surface_m2
→ nb_chambres
→ prix_par_m2
→ age_bien
→ categorie_prix
```

---

## 🔄 Pipeline Workflow

```
run_scraper()        → bronze/*.json
run_staging()        → staging.raw_annonces
run_clean()          → clean.annonces
run_bi_schema()      → bi_schema tables
run_ml_schema()      → ml_schema.feature_store
_cleanup_staging()   → cleanup
```

---

## ⚙️ Engineering Highlights

* Idempotent data loading (`ON CONFLICT DO NOTHING`)
* Retry mechanism (3 attempts)
* Modular pipeline design
* Centralized logging system
* Data validation & type handling

---

## ⚙️ Setup & Installation

### 1. Clone repository

```bash
git clone https://github.com/badre2152/real-estate-data-pipeline.git
cd real-estate-data-pipeline
```

### 2. Setup environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

Create a local `.env` file from the tracked template:

```bash
cp .env.example .env
```

Then replace `change_me_database_password` with your PostgreSQL password. The template uses the local defaults expected by the code:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=avito_db
DB_USER=postgres
DB_PASSWORD=change_me_database_password
```

---

## 🚀 Run the Pipeline

This earlier version runs locally and expects PostgreSQL to be available using the values from your `.env` file.

Create the database once if it does not already exist:

```bash
createdb avito_db
```

Then run the pipeline:

```bash
python src/main.py
```

The pipeline creates its PostgreSQL schemas and tables as needed.

---

## 📊 Dashboard Preview

![Dashboard](docs/dashboard.png)

---

## 🔌 Power BI Integration

1. Connect to PostgreSQL
2. Import `bi_schema` tables
3. Use relationships for analysis

---

## 🛡️ Data Ethics & Compliance

* No personal data collected
* Only public listings used
* Respectful scraping (rate limiting)
* Full pipeline logging

---

## 🧠 Why This Project Stands Out

* Implements **Medallion Architecture (Bronze/Silver/Gold)**
* Separates **BI and ML workloads**
* Uses **Star Schema** for analytics
* Includes **Feature Store for ML**
* Designed like a real-world data platform

---

## 👤 Author

**BRAHIM BADRE**, Data Engineering & Analytics

---

## ⭐ Support

If you found this project useful, consider giving it a star ⭐



![Python](https://img.shields.io/badge/python-3.10-blue)




![License](https://img.shields.io/badge/license-MIT-green)

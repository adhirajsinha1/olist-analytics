# Olist E-commerce Analytics

> 🚧 Work in progress: this README gets finished on Day 7 with findings, charts and a dashboard link.

End-to-end analysis of **~100k real orders** from Olist, a Brazilian e-commerce marketplace (2016–2018).
The project covers revenue growth, customer retention, delivery performance and seller quality, and ends with business recommendations.

## Business questions
1. How is revenue growing, and what drives it (categories, regions, seasonality)?
2. Do customers come back? Which customer segments matter most?
3. How reliable is delivery, and how does lateness affect customer satisfaction?
4. Which sellers perform well or badly?
5. How do customers pay, and does that relate to order value?

## Tech stack
Python (pandas) · SQL (DuckDB) · Jupyter · Plotly / Matplotlib · Streamlit · Git & GitHub

## Pipeline
```
Kaggle CSVs → src/load_data.py → DuckDB (raw schema)
            → SQL cleaning & star schema → analysis notebooks → Streamlit dashboard
```

## Project structure
```
data/raw/        source CSVs (not committed, see "How to run")
src/             Python scripts (data loading, pipeline)
sql/             SQL transformations
notebooks/       analysis notebooks
reports/         written findings (data quality report, insights)
```

## How to run
1. Download the [Olist dataset from Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and unzip the CSVs into `data/raw/`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python src/load_data.py`
5. Open the notebooks in `notebooks/` in order

## Progress
- [x] Day 1: data loading and data quality profiling ([report](reports/data_quality_report.md))
- [ ] Day 2: cleaning and star schema
- [ ] Day 3: revenue and payments analysis
- [ ] Day 4: cohort retention and RFM segmentation
- [ ] Day 5: delivery and seller performance
- [ ] Day 6: dashboard
- [ ] Day 7: final insights and recommendations

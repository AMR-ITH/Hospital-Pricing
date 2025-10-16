# Hospital Pricing Dashboard — User Guide & Documentation

## Overview
This Streamlit dashboard lets users explore and compare hospital procedure pricing data across institutions, payers, and plans. It is built on standardized hospital price transparency files and includes basic data cleaning and validation.

## Data files included
- `hospital_procedure_prices_detailed.csv` — procedure-level with payer and plan; includes estimated, min, and max prices. This is the dataset used by the dashboard.
- `hospital_procedure_prices_basic.csv` — procedure-level without payer/plan; includes standard charge ranges.
- `hospital_drug_prices.csv` — medication-level standard charges with dosage/measurement.

---

## Features & Components

### 1) Filters / Inputs
- Hospital selector: choose a single hospital. (Payer and plan options cascade from this selection.)
- Payer selector: multiselect; shows only payers available for the chosen hospital.
- Plan selector: multiselect; shows only plans available for the chosen hospital and selected payer(s).
- Price range slider: filters by `estimated_amount`.
- Search: keyword filter on procedure `description`.
- Date filter (optional): filter by `last_updated_on` if present.

Tip: Leaving Payer or Plan empty means “all” for the current hospital selection.

### 2) Overview visuals
- Distribution plot: histogram of `estimated_amount` for the current selection.
- Box plot by payer: compares `estimated_amount` distributions across payers.

### 3) Detailed Price Analysis
- Average price by plan (grouped by payer): average `estimated_amount` per plan, colored by its payer.
- Top 10 by price spread: procedures with the largest gap between min and max standard charges, i.e., `price_spread = standard_charge|min … standard_charge|max`.
- Scatter (min vs max): each point is a row/procedure; dashed line y = x is the “equal line.” Points above the line have `max > min`; points below suggest data issues.

### 4) Procedure-level insights
- Top 10 most expensive procedures: based on `estimated_amount` within the current filters.
- Most common procedures: highest counts by `description` in the filtered data.

### 5) Payer-level summary
- Average amount by payer: bar chart of mean `estimated_amount` per payer.
- Distribution by payer: donut or bar chart showing “Top N payers + Other” to avoid clutter from very small categories.
---

## Data model / schema (canonical fields)

| Field                  | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `hospital_name`        | Hospital or institution name                                                |
| `last_updated_on`      | Date when the pricing file was last updated                                 |
| `hospital_address`     | Address or location metadata (if available)                                 |
| `description`          | Procedure name/description                                                  |
| `payer_name`           | Insurance payer (e.g., Medicaid, PPO)                                       |
| `plan_name`            | Specific insurance plan under the payer                                     |
| `estimated_amount`     | Estimated patient/insurer amount (if provided)                              |
| `standard_charge|min`  | Minimum listed standard charge                                              |
| `standard_charge|max`  | Maximum listed standard charge                                              |
| Derived fields         | `spread = max − min`, `ratio = max/min`, `est_minus_avg` (if average exists)|

Notes:
- Amount columns are coerced to numeric and validated.
- Rows where `max < min` are flagged as potential data issues.

---

## Example workflow
1. Select a Hospital (e.g., “Mount Sinai Behavioral Health Center”).
2. Choose Payer(s) and Plan(s) relevant to that hospital.
3. Optionally narrow the price range and search for procedure keywords.
4. Review charts:
   - Histogram of `estimated_amount`
   - Box plot by payer
   - Average price by plan (grouped by payer)
   - Top procedures by price spread (max − min)
   - Min vs Max scatter with equal line
5. Inspect the data table, sort/search as needed, and download the filtered CSV.

---

## Methodology (brief)
- Normalization & cleaning: map disparate hospital columns to a canonical schema; coerce amounts to numeric; standardize text (trim, collapse whitespace); remove filler tokens like “Or Supplies” when appropriate.
- Validation & anomaly detection: enforce/flag `min ≤ max`; highlight rows with `max < min`; review extreme outliers.
- Derived metrics: compute `spread` (max − min), `ratio` (max/min), and summary percentiles (e.g., P50, P95, P99) for robust comparisons.
- Reconciliation: deduplicate by `hospital_name + description + payer_name + plan_name`, preferring the most recent `last_updated_on`.

---

## Running the app (local)
```bash
pip install -r requirements.txt
streamlit run app_streamlit.py
```
Place `hospital_procedure_prices_detailed.csv` next to the app (or use the uploader if enabled).

---

## Notes on interpretation
- Large spreads (max − min) point to higher pricing variability; investigate whether this reflects payer negotiations, bundles, or data issues.
- Points below the y = x line on the scatter indicate `max < min` and should be treated as data anomalies.

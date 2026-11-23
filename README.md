# MCDM-Based Business Decision Support System Using Goal Programming

An Enterprise-Grade Multi-Criteria Decision Support System (MCDM-DSS) for retail assortment optimization powered by **Mixed-Integer Weighted Goal Programming (MI-WGP)**.

---

## 🌟 Key Features

1. **Dual-Dataset Support:**
   * **50-SKU Enterprise Retail Dataset:** Multi-category inventory, supplier performance, and customer transactions.
   * **6-Product Textbook Benchmark:** Pedagogical model for tracing deviations and binary variables step-by-step.
2. **Multi-Scenario Robustness Analytics:**
   * Side-by-side comparison across **Optimistic (Expansion)**, **Normal (Baseline)**, and **Pessimistic (Constrained)** economic scenarios.
3. **Priority Weight Sensitivity Analysis:**
   * Dynamic sweep of goal priority weights ($w_k$) from 0.1 to 0.9 with interactive trade-off curves.
4. **Solver Performance & Execution Metrics:**
   * High-resolution wall-clock solve times (typically $15-50\text{ ms}$), variable counts (58 total, 50 binary, 8 continuous), constraint matrices, and density stats.
5. **Baseline vs. Optimized Benchmark:**
   * Direct empirical comparison against unoptimized catalog and demand heuristics (achieving **+$23.8\%$ higher profit density**).
6. **Automated Product Classification & Directives:**
   * Tiers SKUs into *Core Winners*, *Strategic Contributors*, *Tactical Swing SKUs*, and *Deprioritized SKUs* with actionable guidance.
7. **Multi-Format Enterprise Reporting:**
   * **Excel (.xlsx):** Formatted multi-tab workbook with executive KPIs, portfolio breakdown, recommendations, and scenario matrices.
   * **PDF (.pdf):** Formatted executive summary report.
8. **Interactive Streamlit BI Dashboard:**
   * Modern navy blue, white, and light blue responsive interface with Plotly charts.

---

## 📁 Project Directory Structure

```text
BI/
├── data/
│   ├── textbook_products.csv        # 6-Product pedagogical benchmark dataset
│   ├── retail_products.csv          # 50-Product multi-category retail dataset
│   ├── customer_information.csv     # 100 Customer profiles & segment spending
│   ├── sales_transactions.csv       # 500 Sales transaction records
│   ├── inventory_information.csv    # 50 Inventory stock & storage capacity records
│   └── supplier_information.csv     # 20 Supplier rating & lead time records
├── models/
│   ├── goal_programming_retail.py   # 50-Product MILP solver, scenarios, sensitivity & recs
│   ├── goal_programming_textbook.py # Preserved 6-product textbook solver
│   ├── export_reports.py            # Styled Excel (.xlsx) and PDF (.pdf) generators
│   └── test_system.py               # 9-part comprehensive validation test suite
├── dashboard/
│   └── app.py                       # 7-page enterprise Streamlit dashboard
├── requirements.txt                 # Project dependencies
└── README.md                        # Documentation & user guide
```

---

## 🚀 How to Run the Dashboard

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Application:**
   ```bash
   streamlit run dashboard/app.py
   ```
   *Or with full python interpreter:*
   ```bash
   python -m streamlit run dashboard/app.py
   ```

3. **Run Validation Suite:**
   ```bash
   python models/test_system.py
   ```

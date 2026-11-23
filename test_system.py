"""
MCDM Retail Assortment Decision Support System
Upgraded Comprehensive Test & Validation Suite (10 Requirements)
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.goal_programming_retail import (
    load_and_preprocess_data,
    solve_retail_goal_programming,
    run_scenario_analysis,
    run_sensitivity_analysis,
    generate_product_recommendations,
    compare_baseline_vs_optimized
)
from models.goal_programming_textbook import solve_textbook_goal_programming
from models.export_reports import generate_excel_report, generate_pdf_report

def test_1_textbook_model():
    print("[TEST 1/9] Testing Textbook Model (6 Products)...")
    res, df = solve_textbook_goal_programming()
    assert res["success"] is True, "Textbook model failed!"
    assert len(df) == 6, "Textbook dataset must have 6 rows!"
    assert res["metrics"]["Total_Selection"]["actual"] == 3, "Expected 3 products selected in textbook model!"
    assert res["metrics"]["Total_Storage"]["actual"] <= 2.0, "Storage exceeded in textbook model!"
    print(" -> PASSED: Textbook model verified.")

def test_2_retail_data_loading():
    print("[TEST 2/9] Testing Retail Data Loading & Integrity (50 Products)...")
    df = load_and_preprocess_data()
    assert len(df) == 50, f"Expected 50 products, got {len(df)}"
    assert df["Product_ID"].duplicated().sum() == 0, "Duplicate Product_IDs detected!"
    assert df.isnull().sum().sum() == 0, "Missing values found!"
    assert np.allclose(df["Profit"], (df["Selling_Price"] - df["Purchase_Cost"]).round(2)), "Profit mismatch!"
    print(" -> PASSED: Retail dataset integrity verified.")
    return df

def test_3_retail_optimization_baseline(df):
    print("[TEST 3/9] Testing Retail Optimization Baseline...")
    res, res_df = solve_retail_goal_programming(df)
    assert res["success"] is True, f"Optimization failed: {res.get('message')}"
    
    # Binary variable check
    selected = res_df["Selected"].to_numpy()
    assert np.all((selected == 0) | (selected == 1)), "Non-binary selection found!"
    assert res["total_selected"] == 20, f"Expected 20 products selected, got {res['total_selected']}"
    
    # Category bounds check
    for cat, info in res["category_summary"].items():
        assert info["valid"] is True, f"Category requirement violated for {cat}: {info}"
        
    # Storage hard ceiling check
    assert res["total_storage"] <= 16.0, f"Storage limit violated: {res['total_storage']} > 16.0"
    
    # Goal deviation arithmetic
    for g_name, g in res["goals"].items():
        assert np.isclose(g["actual"] - g["d_plus"] + g["d_minus"], g["target"]), f"Deviation math violated for {g_name}!"
    print(" -> PASSED: Baseline optimization, bounds, and deviation arithmetic verified.")
    return res, res_df

def test_4_solver_performance_metrics(res):
    print("[TEST 4/9] Testing Solver Performance & Execution Time Metrics...")
    perf = res.get("performance", {})
    assert "execution_time_ms" in perf, "execution_time_ms missing!"
    assert perf["execution_time_ms"] > 0, "Execution time must be positive!"
    assert perf["total_variables"] == 58, f"Expected 58 variables, got {perf.get('total_variables')}"
    assert perf["binary_variables"] == 50, f"Expected 50 binary variables, got {perf.get('binary_variables')}"
    assert perf["continuous_deviations"] == 8, f"Expected 8 deviations, got {perf.get('continuous_deviations')}"
    assert perf["matrix_density_pct"] > 0, "Matrix density must be positive!"
    print(f" -> PASSED: Execution time: {perf['execution_time_ms']:.2f} ms | Variables: {perf['total_variables']} | Density: {perf['matrix_density_pct']}%.")

def test_5_sensitivity_analysis(df):
    print("[TEST 5/9] Testing Goal Priority Sensitivity Analysis...")
    sens_df = run_sensitivity_analysis(df, primary_goal="Profit", steps=5)
    assert len(sens_df) == 5, f"Expected 5 sensitivity steps, got {len(sens_df)}"
    assert "Total_Profit" in sens_df.columns, "Total_Profit column missing from sensitivity!"
    assert "Total_Storage" in sens_df.columns, "Total_Storage column missing from sensitivity!"
    # Ensure profit remains within plausible range
    assert sens_df["Total_Profit"].min() >= 1000.0, "Unexpected low profit in sweep!"
    print(f" -> PASSED: Sensitivity sweep verified across {len(sens_df)} weight levels.")

def test_6_scenario_analysis(df):
    print("[TEST 6/9] Testing Multi-Scenario Analysis (Optimistic, Normal, Pessimistic)...")
    scen_results, comp_df, tracker = run_scenario_analysis(df)
    assert len(scen_results) == 3, "Expected 3 scenarios!"
    assert "Optimistic Scenario" in scen_results
    assert "Normal Scenario" in scen_results
    assert "Pessimistic Scenario" in scen_results

    opt_profit = scen_results["Optimistic Scenario"]["results"]["total_profit"]
    norm_profit = scen_results["Normal Scenario"]["results"]["total_profit"]
    pess_profit = scen_results["Pessimistic Scenario"]["results"]["total_profit"]

    # Verify macroeconomic ranking
    assert opt_profit >= norm_profit >= pess_profit, f"Scenario profit hierarchy violated: {opt_profit} >= {norm_profit} >= {pess_profit}"
    assert len(tracker) == 50, "Scenario tracker must hold all 50 products!"
    print(f" -> PASSED: Scenarios verified (Pessimistic: ${pess_profit} <= Normal: ${norm_profit} <= Optimistic: ${opt_profit}).")
    return comp_df, tracker

def test_7_product_recommendations(df, res, tracker):
    print("[TEST 7/9] Testing Product-Level Classification & Recommendation Engine...")
    rec_df = generate_product_recommendations(df, res, tracker)
    assert len(rec_df) == 50, "Recommendations must cover all 50 products!"
    assert "Strategic_Role" in rec_df.columns
    assert "Priority_Tier" in rec_df.columns
    assert "Recommended_Action" in rec_df.columns

    tiers = rec_df["Priority_Tier"].unique()
    assert "Tier 1: Core Winner" in tiers, "Core Winner tier missing!"
    assert "Tier 4: Deprioritize" in tiers, "Deprioritize tier missing!"
    print(f" -> PASSED: Product classification verified: {dict(rec_df['Priority_Tier'].value_counts())}.")
    return rec_df

def test_8_baseline_vs_optimized_comparison(df, res):
    print("[TEST 8/9] Testing Baseline vs. Optimized Assortment Comparison...")
    base_comp = compare_baseline_vs_optimized(df, res)
    assert len(base_comp) == 3, "Expected 3 comparison strategies!"
    
    # Check profit density
    opt_density = base_comp.loc[base_comp["Strategy"].str.contains("Goal Programming"), "Profit Density ($/cu ft)"].values[0]
    unopt_density = base_comp.loc[base_comp["Strategy"].str.contains("Full Catalog"), "Profit Density ($/cu ft)"].values[0]
    assert opt_density > unopt_density, f"Optimized density (${opt_density}) must exceed unoptimized (${unopt_density})!"
    print(f" -> PASSED: Profit density outperformance confirmed (${opt_density}/cu ft vs ${unopt_density}/cu ft).")
    return base_comp

def test_9_excel_and_pdf_export(res, res_df, comp_df, rec_df, base_df):
    print("[TEST 9/9] Testing Multi-Tab Excel and Executive PDF Report Export Engine...")
    excel_bytes = generate_excel_report(res, res_df, comp_df, rec_df, base_df)
    pdf_bytes = generate_pdf_report(res, res_df, comp_df, base_df)

    assert len(excel_bytes) > 2000, f"Excel file too small: {len(excel_bytes)} bytes"
    assert len(pdf_bytes) > 1000, f"PDF file too small: {len(pdf_bytes)} bytes"
    print(f" -> PASSED: Excel ({len(excel_bytes):,} bytes) and PDF ({len(pdf_bytes):,} bytes) successfully generated.")

if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING MCDM ENTERPRISE GOAL PROGRAMMING COMPREHENSIVE SUITE")
    print("=" * 65)
    test_1_textbook_model()
    df = test_2_retail_data_loading()
    res, res_df = test_3_retail_optimization_baseline(df)
    test_4_solver_performance_metrics(res)
    test_5_sensitivity_analysis(df)
    comp_df, tracker = test_6_scenario_analysis(df)
    rec_df = test_7_product_recommendations(df, res, tracker)
    base_df = test_8_baseline_vs_optimized_comparison(df, res)
    test_9_excel_and_pdf_export(res, res_df, comp_df, rec_df, base_df)
    print("=" * 65)
    print("ALL 9 COMPREHENSIVE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

"""
MCDM-Based Business Decision Support System Using Goal Programming
Model 1: Textbook Example (6 Products)
Using scipy.optimize.milp for Binary Integer Goal Programming
"""

import os
import pandas as pd
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

def solve_textbook_goal_programming(
    dataset_path="data/textbook_products.csv",
    target_profit=550.0,
    target_attractiveness=14.0,
    target_storage=2.0,
    target_selection=3,
    weights=None
):
    """
    Solves the binary product selection problem using Weighted Goal Programming (WGP).
    
    Decision Variables:
      X_i in {0, 1} for i in [0..5] (6 products)
      d1+, d1- : Positive and negative deviation for Profit Target
      d2+, d2- : Positive and negative deviation for Attractiveness Target
      d3+, d3- : Positive and negative deviation for Storage Capacity Target
      d4+, d4- : Positive and negative deviation for Product Count Target
    """
    if weights is None:
        # Default priority weights for the 4 goals
        # w1: profit underachievement penalty
        # w2: attractiveness underachievement penalty
        # w3: storage capacity exceeding penalty
        # w4: product count mismatch penalty
        weights = {
            "w_profit": 0.35,
            "w_attractiveness": 0.25,
            "w_storage": 0.25,
            "w_count": 0.15
        }

    # 1. Load Dataset
    df = pd.read_csv(dataset_path)
    n_products = len(df)
    
    # In the textbook dataset, we use Customer_Rating as the measure of Attractiveness
    df["Attractiveness"] = df["Customer_Rating"]

    # 2. Extract Coefficients
    profits = df["Unit_Profit"].to_numpy()
    attractiveness = df["Attractiveness"].to_numpy()
    storage = df["Storage_Space_cuft"].to_numpy()
    selection = np.ones(n_products) # Each product contributes 1 to count

    # Vector of variables layout:
    # Index 0..5:  X0, X1, X2, X3, X4, X5 (Binary, 0 or 1)
    # Index 6..7:  d1+, d1- (Profit deviations)
    # Index 8..9:  d2+, d2- (Attractiveness deviations)
    # Index 10..11: d3+, d3- (Storage deviations)
    # Index 12..13: d4+, d4- (Product count deviations)
    total_vars = n_products + 8

    # 3. Objective Function (Weighted normalized deviations)
    # We normalize each deviation by dividing by its respective target:
    # Z = w1 * (d1- / T1) + w2 * (d2- / T2) + w3 * (d3+ / T3) + w4 * ((d4+ + d4-) / T4)
    c = np.zeros(total_vars)
    c[6] = 0.0                                          # d1+ (exceeding profit is GOOD, no penalty)
    c[7] = weights["w_profit"] / target_profit          # d1- (under-achieving profit is penalized)
    c[8] = 0.0                                          # d2+ (exceeding attractiveness is GOOD, no penalty)
    c[9] = weights["w_attractiveness"] / target_attractiveness # d2- (falling short of attractiveness is penalized)
    c[10] = weights["w_storage"] / target_storage       # d3+ (exceeding storage capacity is penalized)
    c[11] = 0.0                                         # d3- (using less storage is acceptable, no penalty)
    c[12] = weights["w_count"] / target_selection       # d4+ (exceeding target selection count is penalized)
    c[13] = weights["w_count"] / target_selection       # d4- (under-selecting products is penalized)

    # 4. Goal Constraints Matrix: A_eq @ x = b_eq
    # Row 0 (Profit):         sum(Profit_i * X_i) - d1+ + d1- = T_profit
    # Row 1 (Attractiveness): sum(Attr_i * X_i)   - d2+ + d2- = T_attractiveness
    # Row 2 (Storage):        sum(Storage_i * X_i) - d3+ + d3- = T_storage
    # Row 3 (Selection Limit): sum(1 * X_i)        - d4+ + d4- = T_selection
    A = np.zeros((4, total_vars))
    
    # Row 0: Profit
    A[0, 0:n_products] = profits
    A[0, 6] = -1.0 # - d1+
    A[0, 7] =  1.0 # + d1-

    # Row 1: Attractiveness
    A[1, 0:n_products] = attractiveness
    A[1, 8] = -1.0 # - d2+
    A[1, 9] =  1.0 # + d2-

    # Row 2: Storage
    A[2, 0:n_products] = storage
    A[2, 10] = -1.0 # - d3+
    A[2, 11] =  1.0 # + d3-

    # Row 3: Product count
    A[3, 0:n_products] = selection
    A[3, 12] = -1.0 # - d4+
    A[3, 13] =  1.0 # + d4-

    b_targets = np.array([
        target_profit,
        target_attractiveness,
        target_storage,
        target_selection
    ])

    constraints = LinearConstraint(A, b_targets, b_targets)

    # 5. Variable Bounds and Integrality
    # X_i in {0, 1} -> lower=0, upper=1, integrality=1
    # Deviations in [0, inf) -> lower=0, upper=inf, integrality=0 (continuous)
    lb = np.zeros(total_vars)
    ub = np.array([1.0]*n_products + [np.inf]*8)
    bounds = Bounds(lb, ub)
    
    # integrality = 1 for binary products, 0 for continuous deviation variables
    integrality = np.array([1]*n_products + [0]*8)

    # 6. Solve using SciPy MILP
    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)

    if not res.success:
        raise RuntimeError(f"Optimization failed: {res.status} - {res.message}")

    # 7. Extract and Parse Results
    x_sol = res.x
    selected_binary = np.round(x_sol[0:n_products]).astype(int)
    
    df["Selected"] = selected_binary
    selected_df = df[df["Selected"] == 1].copy()

    # Calculate actual achievements
    actual_profit = np.sum(profits * selected_binary)
    actual_attractiveness = np.sum(attractiveness * selected_binary)
    actual_storage = np.sum(storage * selected_binary)
    actual_count = int(np.sum(selected_binary))

    # Deviations from solution vector
    d1_plus, d1_minus = max(0.0, actual_profit - target_profit), max(0.0, target_profit - actual_profit)
    d2_plus, d2_minus = max(0.0, actual_attractiveness - target_attractiveness), max(0.0, target_attractiveness - actual_attractiveness)
    d3_plus, d3_minus = max(0.0, actual_storage - target_storage), max(0.0, target_storage - actual_storage)
    d4_plus, d4_minus = max(0.0, actual_count - target_selection), max(0.0, target_selection - actual_count)

    # Goal achievement percentage
    # For Profit & Attractiveness: min(100%, (Actual / Target) * 100%)
    # For Storage & Count: Target / Actual if over-target, or 100% if satisfied
    achieve_profit = (actual_profit / target_profit) * 100.0
    achieve_attr = (actual_attractiveness / target_attractiveness) * 100.0
    achieve_storage = (target_storage / actual_storage * 100.0) if actual_storage > target_storage else 100.0
    achieve_count = (1.0 - abs(actual_count - target_selection) / target_selection) * 100.0

    results = {
        "success": res.success,
        "objective_value": res.fun,
        "selected_products": selected_df[[
            "Product_ID", "Product_Name", "Unit_Profit", "Storage_Space_cuft", "Customer_Rating"
        ]].to_dict(orient="records"),
        "metrics": {
            "Total_Profit": {"actual": actual_profit, "target": target_profit, "d_plus": d1_plus, "d_minus": d1_minus, "achievement_pct": achieve_profit},
            "Total_Attractiveness": {"actual": round(actual_attractiveness, 2), "target": target_attractiveness, "d_plus": round(d2_plus, 2), "d_minus": round(d2_minus, 2), "achievement_pct": round(achieve_attr, 2)},
            "Total_Storage": {"actual": round(actual_storage, 2), "target": target_storage, "d_plus": round(d3_plus, 2), "d_minus": round(d3_minus, 2), "achievement_pct": round(achieve_storage, 2)},
            "Total_Selection": {"actual": actual_count, "target": target_selection, "d_plus": d4_plus, "d_minus": d4_minus, "achievement_pct": round(achieve_count, 2)}
        }
    }

    return results, df

if __name__ == "__main__":
    results, df = solve_textbook_goal_programming()
    print("=" * 60)
    print("MCDM GOAL PROGRAMMING RESULTS (TEXTBOOK EXAMPLE)")
    print("=" * 60)
    print(f"Objective Function Value (Z): {results['objective_value']:.4f}\n")
    print("Selected Products:")
    for p in results["selected_products"]:
        print(f" - [{p['Product_ID']}] {p['Product_Name']} | Profit: ${p['Unit_Profit']} | Storage: {p['Storage_Space_cuft']} cuft | Rating: {p['Customer_Rating']}")
    
    print("\nGoal Performance Breakdown:")
    for goal_name, m in results["metrics"].items():
        print(f" * {goal_name}:")
        print(f"     Actual: {m['actual']} | Target: {m['target']}")
        print(f"     d+ (Over): {m['d_plus']} | d- (Under): {m['d_minus']}")
        print(f"     Achievement: {m['achievement_pct']:.1f}%")
    print("=" * 60)

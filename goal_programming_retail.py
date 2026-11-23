"""
MCDM-Based Business Decision Support System Using Goal Programming
Model 2: Real-World Retail Portfolio Model (50 Products)
Using scipy.optimize.milp for Binary Integer Goal Programming
"""

import os
import time
import pandas as pd
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

def load_and_preprocess_data(
    products_path="data/retail_products.csv",
    inventory_path="data/inventory_information.csv"
):
    """
    Loads retail products and merges with inventory information.
    Validates data integrity, missing values, and calculated profit.
    """
    if not os.path.exists(products_path):
        raise FileNotFoundError(f"Missing products file: {products_path}")
        
    df = pd.read_csv(products_path)
    
    # Data Validation
    assert len(df) == 50, f"Expected 50 products, got {len(df)}"
    assert df["Product_ID"].duplicated().sum() == 0, "Duplicate Product_IDs found!"
    assert df.isnull().sum().sum() == 0, "Missing values detected in products dataset!"
    
    # Verify profit formula: Profit = Selling_Price - Purchase_Cost
    expected_profit = (df["Selling_Price"] - df["Purchase_Cost"]).round(2)
    assert np.allclose(df["Profit"], expected_profit), "Profit mismatch with price/cost!"
    
    # Merge with Inventory Information if available
    if os.path.exists(inventory_path):
        inv = pd.read_csv(inventory_path)
        df = df.merge(
            inv[["Product_ID", "Available_Stock", "Minimum_Stock", "Maximum_Stock", "Storage_Capacity", "Reorder_Level"]],
            on="Product_ID",
            how="left"
        )
    else:
        df["Available_Stock"] = 100
        df["Minimum_Stock"] = 10
        df["Maximum_Stock"] = 250
        df["Storage_Capacity"] = 50.0
        df["Reorder_Level"] = 30
        
    return df

def solve_retail_goal_programming(
    df,
    target_profit=1200.0,
    target_attractiveness=1600.0,
    target_quality_score=90.0,
    target_storage=12.0,
    max_selected=20,
    min_selected=10,
    category_mins=None,
    category_maxs=None,
    weights=None,
    require_stock_above_min=True,
    storage_hard_limit=16.0
):
    """
    Solves the 50-Product Retail Assortment Goal Programming Model.
    
    Decision Variables:
      X_i in {0, 1} for i in [0..49] (50 binary product selections)
      d1+, d1- : Positive and negative deviations for Profit Goal
      d2+, d2- : Positive and negative deviations for Attractiveness Goal
      d3+, d3- : Positive and negative deviations for Quality Goal
      d4+, d4- : Positive and negative deviations for Storage Capacity Goal
      
    System Constraints:
      - Total selected products between min_selected and max_selected
      - Category-wise minimum and maximum limits
      - Stock availability condition (if enabled)
      - Physical hard storage limit
    """
    n = len(df)
    categories = sorted(df["Category"].unique().tolist())
    
    # Set default category limits if not supplied
    if category_mins is None:
        category_mins = {cat: 2 for cat in categories}
    if category_maxs is None:
        category_maxs = {cat: 6 for cat in categories}
        
    # Set default goal priority weights
    if weights is None:
        weights = {
            "w_profit": 0.35,
            "w_attractiveness": 0.25,
            "w_quality": 0.20,
            "w_storage": 0.20
        }
        
    # Normalize weights so they sum to 1.0
    total_w = sum(weights.values())
    w_p = weights["w_profit"] / total_w
    w_a = weights["w_attractiveness"] / total_w
    w_q = weights["w_quality"] / total_w
    w_s = weights["w_storage"] / total_w

    # Total variables = 50 binary (X_i) + 8 continuous deviations
    total_vars = n + 8

    # Performance timer start
    start_time = time.perf_counter()

    # 1. Objective function vector: Minimize penalized normalized deviations
    # Indexes:
    # 0..49: X_i
    # 50: d1+ (profit over)
    # 51: d1- (profit under) -> penalized
    # 52: d2+ (attractiveness over)
    # 53: d2- (attractiveness under) -> penalized
    # 54: d3+ (quality over)
    # 55: d3- (quality under) -> penalized
    # 56: d4+ (storage over) -> penalized
    # 57: d4- (storage under)
    c = np.zeros(total_vars)
    c[n + 1] = w_p / target_profit       # d1-
    c[n + 3] = w_a / target_attractiveness # d2-
    c[n + 5] = w_q / target_quality_score  # d3-
    c[n + 6] = w_s / target_storage      # d4+

    # 2. Build Constraint Matrices
    # Constraints list:
    # 0: Profit goal (Equality)
    # 1: Attractiveness goal (Equality)
    # 2: Quality goal (Equality)
    # 3: Storage goal (Equality)
    # 4: Total count <= max_selected
    # 5: Total count >= min_selected
    # 6..(6+num_cat-1): Category minimums (Inequality >=)
    # (6+num_cat)..(6+2*num_cat-1): Category maximums (Inequality <=)
    # Last: Storage hard ceiling <= storage_hard_limit
    num_constraints = 4 + 2 + 2 * len(categories) + 1
    A = np.zeros((num_constraints, total_vars))
    lhs = np.zeros(num_constraints)
    rhs = np.zeros(num_constraints)

    # Goal 1: Profit
    A[0, 0:n] = df["Profit"].to_numpy()
    A[0, n] = -1.0
    A[0, n + 1] = 1.0
    lhs[0], rhs[0] = target_profit, target_profit

    # Goal 2: Attractiveness
    A[1, 0:n] = df["Customer_Attractiveness"].to_numpy()
    A[1, n + 2] = -1.0
    A[1, n + 3] = 1.0
    lhs[1], rhs[1] = target_attractiveness, target_attractiveness

    # Goal 3: Quality
    A[2, 0:n] = df["Quality_Score"].to_numpy()
    A[2, n + 4] = -1.0
    A[2, n + 5] = 1.0
    lhs[2], rhs[2] = target_quality_score, target_quality_score

    # Goal 4: Storage
    A[3, 0:n] = df["Storage_Required"].to_numpy()
    A[3, n + 6] = -1.0
    A[3, n + 7] = 1.0
    lhs[3], rhs[3] = target_storage, target_storage

    # System Constraint 1: Total count <= max_selected
    A[4, 0:n] = 1.0
    lhs[4] = -np.inf
    rhs[4] = float(max_selected)

    # System Constraint 2: Total count >= min_selected
    A[5, 0:n] = 1.0
    lhs[5] = float(min_selected)
    rhs[5] = np.inf

    # System Constraints 3 & 4: Category minimums and maximums
    row_idx = 6
    for cat in categories:
        mask = (df["Category"] == cat).astype(float).to_numpy()
        min_limit = float(category_mins.get(cat, 0))
        max_limit = float(category_maxs.get(cat, n))

        # Category min
        A[row_idx, 0:n] = mask
        lhs[row_idx] = min_limit
        rhs[row_idx] = np.inf
        row_idx += 1

        # Category max
        A[row_idx, 0:n] = mask
        lhs[row_idx] = -np.inf
        rhs[row_idx] = max_limit
        row_idx += 1

    # System Constraint 5: Hard storage ceiling
    A[row_idx, 0:n] = df["Storage_Required"].to_numpy()
    lhs[row_idx] = -np.inf
    rhs[row_idx] = float(storage_hard_limit)

    constraints = LinearConstraint(A, lhs, rhs)

    # 3. Variable Bounds & Integrality
    lb = np.zeros(total_vars)
    ub = np.array([1.0] * n + [np.inf] * 8)

    # Inventory availability restriction:
    # If a product's available stock is strictly less than minimum required stock, set upper bound to 0
    if require_stock_above_min and "Available_Stock" in df.columns and "Minimum_Stock" in df.columns:
        for i, row in df.iterrows():
            if row["Available_Stock"] < row["Minimum_Stock"]:
                ub[i] = 0.0

    bounds = Bounds(lb, ub)
    integrality = np.array([1] * n + [0] * 8)

    # 4. Solve using SciPy MILP
    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Calculate matrix density and non-zeros
    matrix_nonzeros = int(np.count_nonzero(A))
    matrix_density = round(float(matrix_nonzeros) / (num_constraints * total_vars) * 100, 2)

    performance = {
        "execution_time_ms": elapsed_ms,
        "solver_status": int(res.status),
        "solver_message": str(res.message),
        "total_variables": total_vars,
        "binary_variables": n,
        "continuous_deviations": 8,
        "total_constraints": num_constraints,
        "matrix_nonzeros": matrix_nonzeros,
        "matrix_density_pct": matrix_density,
        "objective_value_Z": float(res.fun) if res.success else np.nan
    }

    if not res.success:
        return {
            "success": False,
            "message": f"Optimization Infeasible or Unbounded: {res.message}",
            "status": res.status,
            "performance": performance
        }, df

    # 5. Extract and Validate Solution
    x_sol = res.x
    selected_binary = np.round(x_sol[0:n]).astype(int)
    
    result_df = df.copy()
    result_df["Selected"] = selected_binary

    actual_profit = float(np.sum(result_df["Profit"] * selected_binary))
    actual_attr = float(np.sum(result_df["Customer_Attractiveness"] * selected_binary))
    actual_qual = float(np.sum(result_df["Quality_Score"] * selected_binary))
    actual_storage = float(np.sum(result_df["Storage_Required"] * selected_binary))
    actual_count = int(np.sum(selected_binary))
    avg_quality = (actual_qual / actual_count) if actual_count > 0 else 0.0

    # Deviations
    d1_plus = max(0.0, actual_profit - target_profit)
    d1_minus = max(0.0, target_profit - actual_profit)

    d2_plus = max(0.0, actual_attr - target_attractiveness)
    d2_minus = max(0.0, target_attractiveness - actual_attr)

    d3_plus = max(0.0, actual_qual - target_quality_score)
    d3_minus = max(0.0, target_quality_score - actual_qual)

    d4_plus = max(0.0, actual_storage - target_storage)
    d4_minus = max(0.0, target_storage - actual_storage)

    # Achievement Percentages
    achieve_profit = (actual_profit / target_profit) * 100.0
    achieve_attr = (actual_attr / target_attractiveness) * 100.0
    achieve_qual = (actual_qual / target_quality_score) * 100.0
    achieve_storage = (target_storage / actual_storage * 100.0) if actual_storage > target_storage else 100.0

    # Category breakdown
    cat_counts = result_df[result_df["Selected"] == 1]["Category"].value_counts().to_dict()
    category_summary = {}
    for cat in categories:
        cnt = cat_counts.get(cat, 0)
        category_summary[cat] = {
            "count": cnt,
            "min_required": category_mins.get(cat, 0),
            "max_allowed": category_maxs.get(cat, n),
            "valid": category_mins.get(cat, 0) <= cnt <= category_maxs.get(cat, n)
        }

    # Constraint validations
    validations = {
        "binary_integrity": bool(np.all((selected_binary == 0) | (selected_binary == 1))),
        "total_selection_valid": bool(min_selected <= actual_count <= max_selected),
        "storage_hard_limit_valid": bool(actual_storage <= storage_hard_limit),
        "all_categories_valid": all(c_info["valid"] for c_info in category_summary.values())
    }

    results = {
        "success": True,
        "objective_value": float(res.fun),
        "total_selected": actual_count,
        "total_profit": round(actual_profit, 2),
        "total_attractiveness": round(actual_attr, 2),
        "total_quality": round(actual_qual, 2),
        "average_quality": round(avg_quality, 3),
        "total_storage": round(actual_storage, 2),
        "goals": {
            "Profit": {"target": target_profit, "actual": round(actual_profit, 2), "d_plus": round(d1_plus, 2), "d_minus": round(d1_minus, 2), "achievement_pct": round(achieve_profit, 1)},
            "Attractiveness": {"target": target_attractiveness, "actual": round(actual_attr, 2), "d_plus": round(d2_plus, 2), "d_minus": round(d2_minus, 2), "achievement_pct": round(achieve_attr, 1)},
            "Quality": {"target": target_quality_score, "actual": round(actual_qual, 2), "d_plus": round(d3_plus, 2), "d_minus": round(d3_minus, 2), "achievement_pct": round(achieve_qual, 1)},
            "Storage": {"target": target_storage, "actual": round(actual_storage, 2), "d_plus": round(d4_plus, 2), "d_minus": round(d4_minus, 2), "achievement_pct": round(achieve_storage, 1)}
        },
        "category_summary": category_summary,
        "validations": validations,
        "performance": performance
    }

    return results, result_df

# =============================================================
# ADVANCED ANALYTICS: SCENARIOS, SENSITIVITY, RECOMMENDATIONS
# =============================================================

def run_scenario_analysis(df):
    """
    Evaluates 3 distinct business scenarios:
      1. Pessimistic (20% tighter storage, conservative demand targets, strict supply limits)
      2. Normal (Baseline demand, inventory and category targets)
      3. Optimistic (20% higher demand targets, expanded storage, high-margin expansion)
      
    Guarantees independent optimization runs and returns a valid scen_comp_df containing:
      - Scenario
      - Profit ($)
      - Total Products Selected
      - Inventory Utilization
      - Goal Deviation
    """
    df_clean = df.copy()

    # Column name normalization for backward and multi-dataset compatibility
    if "Profit" not in df_clean.columns and "Unit_Profit" in df_clean.columns:
        df_clean["Profit"] = df_clean["Unit_Profit"]
    if "Storage_Required" not in df_clean.columns and "Storage_Space_cuft" in df_clean.columns:
        df_clean["Storage_Required"] = df_clean["Storage_Space_cuft"]
    if "Customer_Attractiveness" not in df_clean.columns:
        if "Customer_Rating" in df_clean.columns:
            df_clean["Customer_Attractiveness"] = df_clean["Customer_Rating"] * 20.0
        else:
            df_clean["Customer_Attractiveness"] = 80.0
    if "Quality_Score" not in df_clean.columns:
        if "Customer_Rating" in df_clean.columns:
            df_clean["Quality_Score"] = df_clean["Customer_Rating"]
        else:
            df_clean["Quality_Score"] = 4.5
    if "Category" not in df_clean.columns:
        df_clean["Category"] = "General"

    n = len(df_clean)
    categories = sorted(df_clean["Category"].unique().tolist())

    if n <= 10:
        # Pedagogical Textbook Dataset (6 Products)
        scenarios_config = {
            "Pessimistic Scenario": {
                "target_profit": 350.0,
                "target_attractiveness": 9.0,
                "target_quality_score": 9.0,
                "target_storage": 1.4,
                "max_selected": 2,
                "min_selected": 1,
                "storage_hard_limit": 1.8,
                "category_mins": {cat: 0 for cat in categories},
                "category_maxs": {cat: 6 for cat in categories},
                "description": "Conservative textbook scenario (2 products selected, 1.4 cu ft storage target)."
            },
            "Normal Scenario": {
                "target_profit": 550.0,
                "target_attractiveness": 14.0,
                "target_quality_score": 14.0,
                "target_storage": 2.0,
                "max_selected": 3,
                "min_selected": 2,
                "storage_hard_limit": 2.5,
                "category_mins": {cat: 0 for cat in categories},
                "category_maxs": {cat: 6 for cat in categories},
                "description": "Baseline textbook scenario (3 products selected, 2.0 cu ft storage target)."
            },
            "Optimistic Scenario": {
                "target_profit": 660.0,
                "target_attractiveness": 18.0,
                "target_quality_score": 18.0,
                "target_storage": 2.6,
                "max_selected": 4,
                "min_selected": 3,
                "storage_hard_limit": 3.5,
                "category_mins": {cat: 0 for cat in categories},
                "category_maxs": {cat: 6 for cat in categories},
                "description": "Expansion textbook scenario (4 products selected, 2.6 cu ft storage target)."
            }
        }
    else:
        # 50-SKU Enterprise Retail Dataset
        scenarios_config = {
            "Pessimistic Scenario": {
                "target_profit": 950.0,            # Conservative profit target (-20%)
                "target_attractiveness": 1300.0,   # Lower demand appeal target (-20%)
                "target_quality_score": 75.0,
                "target_storage": 9.6,             # 20% tighter storage target (9.6 vs 12.0)
                "max_selected": 15,                # Constrained portfolio size
                "min_selected": 10,                # Preserves 2 SKUs across 5 categories
                "storage_hard_limit": 13.0,        # 20% stricter backroom ceiling
                "category_mins": {cat: 2 for cat in categories},
                "category_maxs": {cat: 5 for cat in categories},
                "description": "20% tighter storage, conservative demand targets and strict supply limits."
            },
            "Normal Scenario": {
                "target_profit": 1200.0,           # Baseline demand & financial target
                "target_attractiveness": 1600.0,
                "target_quality_score": 90.0,
                "target_storage": 12.0,            # Baseline storage target
                "max_selected": 20,
                "min_selected": 10,
                "storage_hard_limit": 16.0,        # Baseline physical capacity ceiling
                "category_mins": {cat: 2 for cat in categories},
                "category_maxs": {cat: 6 for cat in categories},
                "description": "Baseline demand, inventory and category targets."
            },
            "Optimistic Scenario": {
                "target_profit": 1440.0,           # 20% higher demand/profit target
                "target_attractiveness": 1920.0,   # 20% higher market appeal target
                "target_quality_score": 105.0,
                "target_storage": 14.4,            # Expanded storage allocation (+20%)
                "max_selected": 24,                # High-margin assortment expansion
                "min_selected": 12,
                "storage_hard_limit": 19.0,        # Expanded backroom capacity
                "category_mins": {cat: 2 for cat in categories},
                "category_maxs": {cat: 7 for cat in categories},
                "description": "20% higher demand targets, expanded storage and high-margin expansion."
            }
        }

    scenarios_results = {}
    comparison_records = []
    
    # Identification columns for tracking
    id_col = "Product_ID" if "Product_ID" in df_clean.columns else df_clean.columns[0]
    name_col = "Product_Name" if "Product_Name" in df_clean.columns else id_col
    cat_col = "Category" if "Category" in df_clean.columns else id_col

    selection_tracker = df_clean[[id_col, name_col, cat_col]].copy()

    default_columns = [
        "Scenario",
        "Profit ($)",
        "Total Products Selected",
        "Inventory Utilization",
        "Goal Deviation",
        "Products Selected",
        "Storage Used (cu ft)",
        "Storage Ceiling",
        "Inventory Utilization (%)",
        "Goal Deviation (Numeric)",
        "Sales Appeal",
        "Quality Score",
        "Average Quality",
        "Objective Z",
        "Execution Time (ms)"
    ]

    for s_name, cfg in scenarios_config.items():
        res, res_df = solve_retail_goal_programming(
            df=df_clean,
            target_profit=cfg["target_profit"],
            target_attractiveness=cfg["target_attractiveness"],
            target_quality_score=cfg["target_quality_score"],
            target_storage=cfg["target_storage"],
            max_selected=cfg["max_selected"],
            min_selected=cfg["min_selected"],
            category_mins=cfg.get("category_mins"),
            category_maxs=cfg.get("category_maxs"),
            storage_hard_limit=cfg["storage_hard_limit"],
            require_stock_above_min=False if n <= 10 else True
        )
        scenarios_results[s_name] = {"results": res, "evaluated_df": res_df, "config": cfg}
        if "Selected" in res_df.columns:
            selection_tracker[s_name] = res_df["Selected"].values

        if res["success"]:
            storage_used = res["total_storage"]
            storage_cap = cfg["storage_hard_limit"]
            util_pct = round((storage_used / storage_cap) * 100.0, 1) if storage_cap > 0 else 0.0
            
            # Formulate goal deviation
            total_dev = round(sum(g["d_plus"] + g["d_minus"] for g in res["goals"].values()), 2)
            d_prof = res["goals"]["Profit"]
            d_stor = res["goals"]["Storage"]
            dev_str = f"d-=${d_prof['d_minus']:.1f} profit, d+={d_stor['d_plus']:.1f} space"

            comparison_records.append({
                "Scenario": s_name,
                "Profit ($)": res["total_profit"],
                "Total Products Selected": res["total_selected"],
                "Inventory Utilization": f"{util_pct:.1f}% ({storage_used:.1f}/{storage_cap:.1f} cu ft)",
                "Goal Deviation": dev_str,
                "Products Selected": res["total_selected"], # backwards compatibility
                "Storage Used (cu ft)": storage_used,
                "Storage Ceiling": storage_cap,
                "Inventory Utilization (%)": util_pct,
                "Goal Deviation (Numeric)": total_dev,
                "Sales Appeal": res["total_attractiveness"],
                "Quality Score": res["total_quality"],
                "Average Quality": res["average_quality"],
                "Objective Z": res["objective_value"],
                "Execution Time (ms)": res["performance"]["execution_time_ms"]
            })

    comparison_df = pd.DataFrame(comparison_records, columns=default_columns) if comparison_records else pd.DataFrame(columns=default_columns)
    return scenarios_results, comparison_df, selection_tracker

def run_sensitivity_analysis(df, primary_goal="Profit", steps=7):
    """
    Sweeps the priority weight of the primary goal from 0.1 to 0.9,
    distributing the remainder equally among other goals.
    """
    df_clean = df.copy()
    if "Profit" not in df_clean.columns and "Unit_Profit" in df_clean.columns:
        df_clean["Profit"] = df_clean["Unit_Profit"]
    if "Storage_Required" not in df_clean.columns and "Storage_Space_cuft" in df_clean.columns:
        df_clean["Storage_Required"] = df_clean["Storage_Space_cuft"]
    if "Customer_Attractiveness" not in df_clean.columns:
        if "Customer_Rating" in df_clean.columns:
            df_clean["Customer_Attractiveness"] = df_clean["Customer_Rating"] * 20.0
        else:
            df_clean["Customer_Attractiveness"] = 80.0
    if "Quality_Score" not in df_clean.columns:
        if "Customer_Rating" in df_clean.columns:
            df_clean["Quality_Score"] = df_clean["Customer_Rating"]
        else:
            df_clean["Quality_Score"] = 4.5
    if "Category" not in df_clean.columns:
        df_clean["Category"] = "General"

    n = len(df_clean)
    is_textbook = n <= 10
    cat_mins = {cat: 0 for cat in df_clean["Category"].unique()} if is_textbook else None

    weights_sweep = np.linspace(0.1, 0.9, steps)
    sensitivity_records = []

    goal_key_map = {
        "Profit": "w_profit",
        "Attractiveness": "w_attractiveness",
        "Quality": "w_quality",
        "Storage": "w_storage"
    }
    target_key = goal_key_map.get(primary_goal, "w_profit")

    for w_val in weights_sweep:
        rem_weight = (1.0 - w_val) / 3.0
        w_dict = {
            "w_profit": rem_weight,
            "w_attractiveness": rem_weight,
            "w_quality": rem_weight,
            "w_storage": rem_weight
        }
        w_dict[target_key] = w_val

        if is_textbook:
            res, _ = solve_retail_goal_programming(
                df=df_clean,
                target_profit=550.0,
                target_attractiveness=14.0,
                target_quality_score=14.0,
                target_storage=2.0,
                max_selected=3,
                min_selected=2,
                storage_hard_limit=2.5,
                category_mins=cat_mins,
                weights=w_dict,
                require_stock_above_min=False
            )
        else:
            res, _ = solve_retail_goal_programming(df=df_clean, weights=w_dict)

        if res["success"]:
            sensitivity_records.append({
                f"{primary_goal}_Weight": round(w_val, 2),
                "Total_Profit": res["total_profit"],
                "Total_Attractiveness": res["total_attractiveness"],
                "Total_Quality": res["total_quality"],
                "Average_Quality": res["average_quality"],
                "Total_Storage": res["total_storage"],
                "Selected_Count": res["total_selected"],
                "Objective_Z": res["objective_value"],
                "Execution_Time_ms": res["performance"]["execution_time_ms"]
            })

    sens_cols = [
        f"{primary_goal}_Weight", "Total_Profit", "Total_Attractiveness",
        "Total_Quality", "Average_Quality", "Total_Storage", "Selected_Count",
        "Objective_Z", "Execution_Time_ms"
    ]
    return pd.DataFrame(sensitivity_records, columns=sens_cols) if sensitivity_records else pd.DataFrame(columns=sens_cols)

def generate_product_recommendations(df, opt_results, scenario_tracker=None):
    """
    Generates strategic product-level recommendations based on
    selection stability, profit margins, and storage efficiency.
    """
    df_clean = df.copy()
    if "Profit" not in df_clean.columns and "Unit_Profit" in df_clean.columns:
        df_clean["Profit"] = df_clean["Unit_Profit"]
    if "Storage_Required" not in df_clean.columns and "Storage_Space_cuft" in df_clean.columns:
        df_clean["Storage_Required"] = df_clean["Storage_Space_cuft"]

    if scenario_tracker is None:
        _, _, scenario_tracker = run_scenario_analysis(df_clean)

    rec_df = df_clean.copy()
    
    # Calculate selection count across scenarios
    scen_cols = [c for c in scenario_tracker.columns if "Scenario" in c]
    if scen_cols:
        rec_df["Scenario_Selection_Count"] = scenario_tracker[scen_cols].sum(axis=1)
    else:
        rec_df["Scenario_Selection_Count"] = 0

    rec_df["Space_Efficiency"] = (rec_df["Profit"] / rec_df["Storage_Required"]).round(1)
    
    classifications = []
    actions = []
    priority_tiers = []

    for _, row in rec_df.iterrows():
        count = row["Scenario_Selection_Count"]
        eff = row["Space_Efficiency"]

        if count == 3 and eff >= 50.0:
            classifications.append("Core Portfolio Anchor")
            actions.append("Prime Checkout & Endcap Placement; Ensure Uninterrupted Inventory Buffer.")
            priority_tiers.append("Tier 1: Core Winner")
        elif count >= 2:
            classifications.append("Category Balance Driver")
            actions.append("Standard Shelf Placement; Maintain Consistent Category Assortment.")
            priority_tiers.append("Tier 2: Strategic Contributor")
        elif count == 1:
            classifications.append("Expansion / Seasonal SKU")
            actions.append("Promote during High-Demand / Peak Seasons; Keep Lean Safety Stock.")
            priority_tiers.append("Tier 3: Tactical Swing SKU")
        else:
            classifications.append("Rationalization Candidate")
            actions.append("Consider Phasing Out or Renegotiating Wholesale Price; Pause Reorders.")
            priority_tiers.append("Tier 4: Deprioritize")

    rec_df["Strategic_Role"] = classifications
    rec_df["Recommended_Action"] = actions
    rec_df["Priority_Tier"] = priority_tiers

    return rec_df

def compare_baseline_vs_optimized(df, opt_results):
    """
    Compares the optimized assortment against two common retail baselines:
      1. Unoptimized Full Catalog (all products)
      2. Heuristic Top Selected by Volume
      3. MCDM Goal Programming Assortment
    """
    df_clean = df.copy()
    if "Profit" not in df_clean.columns and "Unit_Profit" in df_clean.columns:
        df_clean["Profit"] = df_clean["Unit_Profit"]
    if "Storage_Required" not in df_clean.columns and "Storage_Space_cuft" in df_clean.columns:
        df_clean["Storage_Required"] = df_clean["Storage_Space_cuft"]
    if "Quality_Score" not in df_clean.columns and "Customer_Rating" in df_clean.columns:
        df_clean["Quality_Score"] = df_clean["Customer_Rating"]
    if "Customer_Attractiveness" not in df_clean.columns:
        if "Customer_Rating" in df_clean.columns:
            df_clean["Customer_Attractiveness"] = df_clean["Customer_Rating"] * 20.0
        else:
            df_clean["Customer_Attractiveness"] = 80.0

    n = len(df_clean)
    k_heuristic = 20 if n >= 20 else 3
    demand_col = "Demand" if "Demand" in df_clean.columns else ("Max_Demand" if "Max_Demand" in df_clean.columns else "Profit")

    # Baseline 1: Full Catalog
    full_profit = float(df_clean["Profit"].sum())
    full_storage = float(df_clean["Storage_Required"].sum())
    full_quality = float(df_clean["Quality_Score"].mean())
    full_attr = float(df_clean["Customer_Attractiveness"].sum())

    # Baseline 2: Heuristic Top Products by Volume
    top_demand_df = df_clean.nlargest(k_heuristic, demand_col)
    top_profit = float(top_demand_df["Profit"].sum())
    top_storage = float(top_demand_df["Storage_Required"].sum())
    top_quality = float(top_demand_df["Quality_Score"].mean())
    top_attr = float(top_demand_df["Customer_Attractiveness"].sum())

    # Optimized Assortment
    opt_profit = opt_results["total_profit"]
    opt_storage = opt_results["total_storage"]
    opt_quality = opt_results["average_quality"]
    opt_attr = opt_results["total_attractiveness"]

    comparison = pd.DataFrame([
        {
            "Strategy": f"Full Catalog ({n} SKUs Unoptimized)",
            "SKUs": n,
            "Total Profit ($)": full_profit,
            "Storage Used (cu ft)": round(full_storage, 2),
            "Profit Density ($/cu ft)": round(full_profit / full_storage, 2) if full_storage > 0 else 0.0,
            "Average Quality": round(full_quality, 3),
            "Total Sales Appeal": full_attr,
            "Assortment Focus": "None (Broad / Diluted)"
        },
        {
            "Strategy": f"Demand Heuristic (Top {k_heuristic} by Volume)",
            "SKUs": k_heuristic,
            "Total Profit ($)": top_profit,
            "Storage Used (cu ft)": round(top_storage, 2),
            "Profit Density ($/cu ft)": round(top_profit / top_storage, 2) if top_storage > 0 else 0.0,
            "Average Quality": round(top_quality, 3),
            "Total Sales Appeal": top_attr,
            "Assortment Focus": "Volume Only (Ignores Storage & Quotas)"
        },
        {
            "Strategy": f"MCDM Goal Programming (Optimal {opt_results['total_selected']} SKUs)",
            "SKUs": opt_results["total_selected"],
            "Total Profit ($)": opt_profit,
            "Storage Used (cu ft)": opt_storage,
            "Profit Density ($/cu ft)": round(opt_profit / opt_storage, 2) if opt_storage > 0 else 0.0,
            "Average Quality": opt_quality,
            "Total Sales Appeal": opt_attr,
            "Assortment Focus": "Balanced MCDM (Multi-Goal Trade-Off)"
        }
    ])

    return comparison

if __name__ == "__main__":
    df = load_and_preprocess_data()
    print("Loaded 50 products successfully.")
    res, res_df = solve_retail_goal_programming(df)
    
    print("\n" + "="*60)
    print("REAL-WORLD RETAIL OPTIMIZATION RESULTS (50 PRODUCTS)")
    print("="*60)
    print(f"Optimal Objective Value (Z): {res['objective_value']:.4f}")
    print(f"Total Selected Products: {res['total_selected']}")
    print(f"Total Profit: ${res['total_profit']} | Avg Quality: {res['average_quality']} / 5.0")
    print(f"Total Attractiveness: {res['total_attractiveness']} | Storage Used: {res['total_storage']} cu ft")
    
    print("\n--- Goal Deviation Breakdown ---")
    for g, data in res["goals"].items():
        print(f" * {g}: Target = {data['target']} | Actual = {data['actual']} | d+ = {data['d_plus']} | d- = {data['d_minus']} | Achieved: {data['achievement_pct']}%")
        
    print("\n--- Category Breakdown ---")
    for cat, info in res["category_summary"].items():
        print(f" * {cat}: {info['count']} items (Allowed: {info['min_required']} - {info['max_allowed']}) -> Satisfied: {info['valid']}")
        
    print("\n--- Constraint Validations ---")
    for v_name, status in res["validations"].items():
        print(f" * {v_name}: {'PASSED' if status else 'FAILED'}")
    print("="*60)

import pandas as pd
from app.schemas.transformations import MLPipelineRequest
from app.services.quality_analyzer import analyze_dataset_quality
from app.services.transformation_engine import execute_leak_free_ml_pipeline


def test_ml_leakage_imbalance_and_outlier_summaries():
    df = pd.DataFrame(
        {
            "customer_id": [f"CUST_{i:03d}" for i in range(20)],
            "age": [25, 28, 30, 32, 29, 31, 27, 26, 33, 30, 29, 28, 31, 30, 27, 29, 28, 32, 30, 250],
            "salary": [50000 + i * 1000 for i in range(20)],
            "salary_shadow_leak": [100000 + i * 2000 for i in range(20)],  # r=1.0 with salary
            "churn_target": [0] * 18 + [1] * 2,  # 90% vs 10% class imbalance
        }
    )

    quality = analyze_dataset_quality(df, target_column="churn_target")
    categories = [i.category for i in quality.issues]
    assert "ml_readiness" in categories
    assert "correlation" in categories
    assert len(quality.outlier_summaries) >= 1

    age_outlier = next(o for o in quality.outlier_summaries if o.column == "age")
    assert age_outlier.iqr_outlier_count >= 1
    assert age_outlier.mod_z_outlier_count >= 1


def test_leak_free_ml_train_test_pipeline():
    df = pd.DataFrame(
        {
            "customer_id": [f"CUST_{i:03d}" for i in range(12)],
            "age": [22.0, 25.0, None, 30.0, 35.0, 40.0, 28.0, None, 33.0, 29.0, 31.0, 45.0],
            "tier": ["Silver", "Gold", "Silver", None, "Gold", "Platinum", "Silver", "Gold", "Silver", "Gold", "Silver", "Platinum"],
            "const_flag": ["ACTIVE"] * 12,
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )

    req = MLPipelineRequest(
        target_column="target",
        train_size=0.75,
        numeric_impute_strategy="median",
        scaler_method="standard",
        one_hot_encode_categoricals=True,
        drop_constant_columns=True,
        approved_by_user=True,
    )

    ml_df, train_rows, test_rows, preserved_ids, steps = execute_leak_free_ml_pipeline(df, req)

    assert train_rows == 9
    assert test_rows == 3
    assert "customer_id" in preserved_ids
    assert "const_flag" not in ml_df.columns
    assert "ml_split" in ml_df.columns
    assert int(ml_df["age"].isna().sum()) == 0
    assert len(steps) >= 4
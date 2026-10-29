import pandas as pd
from app.services.column_normalizer import standardize_column_names
from app.services.profiler import classify_semantic_type


def test_column_name_standardization_examples():
    raw_df = pd.DataFrame(
        columns=[
            "Customer Name",
            "CUSTOMER AGE",
            "Annual Income ($)",
            "Order-Date",
            "API Response Time",
            "Customer ID",
            "Customer-ID",
            "   ",
        ]
    )

    std_df, report = standardize_column_names(raw_df)

    expected = [
        "customer_name",
        "customer_age",
        "annual_income",
        "order_date",
        "api_response_time",
        "customer_id",
        "customer_id_2",
        "unnamed_col_8",
    ]
    assert list(std_df.columns) == expected
    assert report.total_columns == 8
    assert report.duplicate_names_resolved == 1
    assert report.empty_names_filled == 1


def test_semantic_column_classifications():
    df = pd.DataFrame(
        {
            "customer_id": [f"CUST_{i:04d}" for i in range(30)],
            "age": [25, 30, 35, 40, 22] * 6,
            "is_active": [True, False] * 15,
            "signup_date": ["2025-01-15", "2025-02-20"] * 15,
            "city": ["Chennai", "Mumbai", "Delhi"] * 10,
            "customer_feedback": [
                "The product delivery was super fast and packaging was excellent overall."
            ]
            * 30,
        }
    )

    assert classify_semantic_type(df["customer_id"], "customer_id") == "identifier"
    assert classify_semantic_type(df["age"], "age") == "numeric"
    assert classify_semantic_type(df["is_active"], "is_active") == "boolean"
    assert classify_semantic_type(df["signup_date"], "signup_date") == "datetime"
    assert classify_semantic_type(df["city"], "city") == "categorical"
    assert classify_semantic_type(df["customer_feedback"], "customer_feedback") == "text"
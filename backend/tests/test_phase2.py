import pandas as pd
from app.services.quality_analyzer import analyze_dataset_quality


def test_quality_analyzer_comprehensive():
    df = pd.DataFrame(
        {
            "customer_id": ["CUST_01", "CUST_02", "CUST_02", "CUST_04"],  # Duplicate ID
            "age": [25, None, 35, 200],  # Missing value & Outlier
            "income": ["$50,000", "$60,000", "$70,000", "$80,000"],  # String numbers
            "city": ["  New York", "London", "Paris", "Tokyo"],  # Whitespace
            "constant_col": [1, 1, 1, 1],  # Zero variance
        }
    )

    report = analyze_dataset_quality(df)
    assert report.total_issues_found >= 4
    assert report.risk_score > 0
    categories = [issue.category for issue in report.issues]
    assert "missing_values" in categories
    assert "duplicates" in categories
    assert "variance" in categories
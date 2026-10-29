import pandas as pd
from app.schemas.dataset import ColumnMappingItem, ColumnStandardizationReport
from app.services.export_service import (
    export_audit_report_bytes,
    export_cleaned_dataset_bytes,
)
from app.services.session_store import session_store


def test_dataset_and_audit_report_exports():
    df = pd.DataFrame(
        {
            "customer_id": ["CUST_01", "CUST_02"],
            "age": [29, 34],
            "city": ["Chennai", "Mumbai"],
        }
    )
    report = ColumnStandardizationReport(
        total_columns=3,
        modified_count=1,
        duplicate_names_resolved=0,
        empty_names_filled=0,
        mappings=[
            ColumnMappingItem(index=0, original_name="Customer ID", standardized_name="customer_id", was_modified=True),
            ColumnMappingItem(index=1, original_name="age", standardized_name="age", was_modified=False),
            ColumnMappingItem(index=2, original_name="city", standardized_name="city", was_modified=False),
        ],
        original_to_standardized={"Customer ID": "customer_id", "age": "age", "city": "city"},
    )
    session = session_store.create_session(
        filename="customers.csv",
        file_format=".csv",
        raw_bytes=b"Customer ID,age,city\nCUST_01,29,Chennai\n",
        standardized_df=df,
        standardization_report=report,
    )

    for fmt in ("csv", "xlsx", "json", "parquet"):
        b_data, media, fname = export_cleaned_dataset_bytes(session.dataset_id, fmt)
        assert len(b_data) > 0
        assert fname.endswith(f".{fmt}")

    for r_fmt in ("html", "md", "json"):
        r_bytes, _, r_name = export_audit_report_bytes(session.dataset_id, r_fmt)
        assert len(r_bytes) > 0
        assert r_name.endswith(f".{r_fmt}")
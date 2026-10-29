import pandas as pd
from app.schemas.dataset import ColumnMappingItem, ColumnStandardizationReport
from app.schemas.transformations import TransformationRequest
from app.services.audit_logger import build_before_after_comparison, get_audit_history
from app.services.session_store import session_store
from app.services.transformation_engine import preview_transformation_effect
from app.services.validation_engine import validate_transformation_result


def test_validation_audit_undo_and_restore():
    raw_df = pd.DataFrame(
        {
            "customer_id": ["C1", "C2", "C2", "C3"],
            "age": [25.0, None, None, 35.0],
        }
    )
    dummy_report = ColumnStandardizationReport(
        total_columns=2,
        modified_count=0,
        duplicate_names_resolved=0,
        empty_names_filled=0,
        mappings=[
            ColumnMappingItem(index=0, original_name="customer_id", standardized_name="customer_id", was_modified=False),
            ColumnMappingItem(index=1, original_name="age", standardized_name="age", was_modified=False),
        ],
        original_to_standardized={"customer_id": "customer_id", "age": "age"},
    )

    session = session_store.create_session(
        filename="test.csv",
        file_format=".csv",
        raw_bytes=b"customer_id,age\nC1,25\n",
        standardized_df=raw_df,
        standardization_report=dummy_report,
    )
    ds_id = session.dataset_id

    # Step 1: Remove exact duplicates (v1)
    req1 = TransformationRequest(operation="remove_exact_duplicates", columns=[], approved_by_user=True)
    df1, eff1 = preview_transformation_effect(session_store.load_dataframe(ds_id), req1)
    val1 = validate_transformation_result(raw_df, df1, req1)
    assert val1.is_valid is True

    v1 = session_store.save_new_snapshot(
        ds_id, df1, req1.operation, req1.columns, req1.parameters,
        eff1.rows_before, eff1.cols_before, eff1.missing_before, eff1.missing_after,
        val1.is_valid, eff1.execution_notes
    )
    assert v1 == 1

    # Step 2: Impute missing age with median (v2)
    req2 = TransformationRequest(operation="impute_numeric_median", columns=["age"], approved_by_user=True)
    df2, eff2 = preview_transformation_effect(session_store.load_dataframe(ds_id), req2)
    val2 = validate_transformation_result(df1, df2, req2)
    assert val2.is_valid is True

    v2 = session_store.save_new_snapshot(
        ds_id, df2, req2.operation, req2.columns, req2.parameters,
        eff2.rows_before, eff2.cols_before, eff2.missing_before, eff2.missing_after,
        val2.is_valid, eff2.execution_notes
    )
    assert v2 == 2

    # Check comparison between v0 and v2
    comp = build_before_after_comparison(ds_id)
    assert comp.rows_baseline == 4
    assert comp.rows_current == 3
    assert comp.missing_baseline == 2
    assert comp.missing_current == 0

    # Undo back to v1
    undo_ver = session_store.undo_last_snapshot(ds_id)
    assert undo_ver == 1
    assert int(session_store.load_dataframe(ds_id)["age"].isna().sum()) == 1

    # Restore back to v0
    restored_ver = session_store.restore_snapshot_version(ds_id, 0)
    assert restored_ver == 0
    history = get_audit_history(ds_id)
    assert history.current_version == 0
    assert history.can_undo is False
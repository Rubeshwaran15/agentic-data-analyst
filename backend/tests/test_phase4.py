import pandas as pd
import pytest
from app.core.exceptions import DatasetError
from app.schemas.transformations import TransformationRequest
from app.services.transformation_engine import preview_transformation_effect


def test_impute_median_and_remove_duplicates():
    df = pd.DataFrame(
        {
            "customer_id": ["C1", "C2", "C2", "C3", "C4"],
            "age": [20.0, None, None, 30.0, 40.0],
            "city": ["  chennai ", "mumbai", "mumbai", "delhi", "chennai"],
        }
    )

    # 1. Remove exact duplicates
    req_dup = TransformationRequest(
        operation="remove_exact_duplicates",
        columns=[],
        approved_by_user=True,
    )
    df_no_dup, effect_dup = preview_transformation_effect(df, req_dup)
    assert len(df_no_dup) == 4
    assert effect_dup.rows_delta == -1

    # 2. Impute numeric median on age
    req_imp = TransformationRequest(
        operation="impute_numeric_median",
        columns=["age"],
        approved_by_user=True,
    )
    df_imputed, effect_imp = preview_transformation_effect(df_no_dup, req_imp)
    assert df_imputed["age"].isna().sum() == 0
    assert df_imputed.loc[1, "age"] == 30.0
    assert effect_imp.missing_delta == -1


def test_identifier_protection_blocks_scaling():
    df = pd.DataFrame(
        {
            "customer_id": [1001, 1002, 1003, 1004, 1005],
            "salary": [50000, 60000, 75000, 80000, 90000],
        }
    )
    req = TransformationRequest(
        operation="apply_scaler",
        columns=["customer_id"],
        parameters={"method": "standard"},
        approved_by_user=True,
    )
    with pytest.raises(DatasetError):
        preview_transformation_effect(df, req)
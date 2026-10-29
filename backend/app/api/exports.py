from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.services.export_service import (
    build_comprehensive_audit_payload,
    export_audit_report_bytes,
    export_cleaned_dataset_bytes,
)

router = APIRouter(prefix="/api/exports", tags=["Data & Report Exports"])

SAMPLE_MESSY_CSV = """Customer ID,Customer-ID,Full Name,Customer Age,Annual Salary ($),City ,Membership Tier,Join-Date,System Flag
CUST_1001,1001,  alice johnson ,28,"$65,000",  chennai ,Silver,2025-01-10,ACTIVE
CUST_1002,1002,bob smith,, "$78,500",MUMBAI  ,Gold,2025-01-12,ACTIVE
CUST_1002,1002,bob smith,, "$78,500",MUMBAI  ,Gold,2025-01-12,ACTIVE
CUST_1003,1003,CHARLIE DAVIS,35,"$92,000",  bengaluru,Platinum,2025-01-15,ACTIVE
CUST_1004,1004,diana prince,31,"$81,200",chennai,Silver,2025-01-18,ACTIVE
CUST_1005,1005,evan wright,, "$54,000",  delhi ,Bronze,2025-01-20,ACTIVE
CUST_1006,1006,fiona gallagher,26,"$61,000",mumbai,,2025-01-22,ACTIVE
CUST_1007,1007,george miller,42,"$115,000",Hyderabad,Gold,2025-01-25,ACTIVE
CUST_1008,1008,hannah abbott,195,"$69,000",  chennai ,Silver,2025-01-28,ACTIVE
CUST_1009,1009,ian malcolm,39,"$105,000",bengaluru,,2025-02-01,ACTIVE
CUST_1010,1010,julia roberts,33,"$88,000",delhi,Gold,2025-02-04,ACTIVE
"""


@router.get("/sample-csv")
async def download_sample_messy_csv() -> Response:
    return Response(
        content=SAMPLE_MESSY_CSV.encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_messy_test_dataset.csv"'},
    )


@router.get("/{dataset_id}/dataset")
async def download_cleaned_dataset(
    dataset_id: str,
    format: str = Query(default="csv", description="csv, xlsx, json, or parquet"),
) -> Response:
    file_bytes, media_type, filename = export_cleaned_dataset_bytes(dataset_id, format)
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{dataset_id}/report")
async def download_audit_report(
    dataset_id: str,
    format: str = Query(default="html", description="html, md, or json"),
) -> Response:
    file_bytes, media_type, filename = export_audit_report_bytes(dataset_id, format)
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{dataset_id}/summary")
async def get_audit_report_summary(dataset_id: str) -> dict:
    return build_comprehensive_audit_payload(dataset_id)
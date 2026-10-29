import io
from pathlib import Path
import pandas as pd
from app.core.config import settings
from app.core.exceptions import DatasetError


def validate_file_metadata(filename: str, file_size_bytes: int) -> str:
    if not filename:
        raise DatasetError("Uploaded file must have a valid filename.", status_code=400)

    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise DatasetError(
            f"Unsupported file format '{ext}'. Allowed formats: {allowed_list}",
            status_code=400,
            details={"extension": ext, "allowed": sorted(settings.ALLOWED_EXTENSIONS)},
        )

    if file_size_bytes <= 0:
        raise DatasetError("The uploaded file is empty (0 bytes).", status_code=400)

    if file_size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        size_mb = round(file_size_bytes / (1024 * 1024), 2)
        raise DatasetError(
            f"File size ({size_mb} MB) exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
            status_code=413,
            details={"file_size_mb": size_mb, "limit_mb": settings.MAX_UPLOAD_SIZE_MB},
        )

    return ext


def parse_tabular_bytes(raw_bytes: bytes, extension: str) -> pd.DataFrame:
    """
    Safely parses CSV, XLSX, XLS, JSON, or Parquet bytes into a Pandas DataFrame
    with clear error messages and memory safeguards.
    """
    buffer = io.BytesIO(raw_bytes)

    try:
        if extension == ".csv":
            df = _read_csv_with_fallback(raw_bytes)
        elif extension == ".xlsx":
            df = pd.read_excel(buffer, engine="openpyxl")
        elif extension == ".xls":
            df = pd.read_excel(buffer, engine="xlrd")
        elif extension == ".json":
            df = _read_json_with_fallback(raw_bytes)
        elif extension == ".parquet":
            df = pd.read_parquet(buffer, engine="pyarrow")
        else:
            raise DatasetError(f"Unsupported file extension: {extension}", status_code=400)
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError(
            f"Failed to parse {extension.upper()} file. Ensure the file is not corrupted or password-protected.",
            status_code=422,
            details={"parser_error": str(exc)},
        ) from exc

    if df is None or df.empty or len(df.columns) == 0:
        raise DatasetError(
            "The uploaded dataset contains no rows or columns.",
            status_code=422,
        )

    if len(df) > settings.MAX_ROWS_LIMIT:
        raise DatasetError(
            f"Dataset has {len(df):,} rows, exceeding the maximum allowed {settings.MAX_ROWS_LIMIT:,} rows for local 16 GB RAM processing.",
            status_code=413,
        )

    if len(df.columns) > settings.MAX_COLS_LIMIT:
        raise DatasetError(
            f"Dataset has {len(df.columns):,} columns, exceeding the maximum allowed {settings.MAX_COLS_LIMIT:,} columns.",
            status_code=413,
        )

    return df


def _read_csv_with_fallback(raw_bytes: bytes) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    last_err: Exception | None = None

    for enc in encodings:
        try:
            text_stream = io.BytesIO(raw_bytes)
            return pd.read_csv(text_stream, encoding=enc, low_memory=False)
        except UnicodeDecodeError as err:
            last_err = err
            continue

    raise DatasetError(
        "Unable to decode CSV file with standard text encodings (UTF-8, Windows-1252, Latin-1).",
        status_code=422,
        details={"encoding_error": str(last_err)},
    )


def _read_json_with_fallback(raw_bytes: bytes) -> pd.DataFrame:
    # Try standard records/columns JSON first, then JSON lines (NDJSON)
    try:
        return pd.read_json(io.BytesIO(raw_bytes))
    except ValueError:
        return pd.read_json(io.BytesIO(raw_bytes), lines=True)
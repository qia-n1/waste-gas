from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.data_fusion import (
    append_source_records,
    get_status,
    parse_upload_file,
    rebuild_aggregate_from_history_csv,
    save_history_snapshot,
    run_aggregate_and_push_once,
)


router = APIRouter(tags=["data-fusion"])


@router.post("/sensor-data")
async def ingest_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    records = []
    if "records" in payload and isinstance(payload["records"], list):
        records = [item for item in payload["records"] if isinstance(item, dict)]
    elif "data" in payload and isinstance(payload["data"], dict):
        records = [payload["data"]]
    elif "record" in payload and isinstance(payload["record"], dict):
        records = [payload["record"]]
    else:
        records = [payload]

    if not records:
        raise HTTPException(status_code=400, detail="No valid records in payload")

    count, source_file = append_source_records(source_format="json", records=records)
    return {
        "status": "ok",
        "source_format": "json",
        "source_file": source_file.name,
        "written": count,
    }


@router.post("/sensor-data2")
async def ingest_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    filename = file.filename or ""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"json", "jsonl", "txt"}:
        source_format = "json"
    elif suffix == "csv":
        source_format = "csv"
    elif suffix in {"xlsx", "xlsm", "xltx", "xltm"}:
        source_format = "xlsx"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{suffix}" if suffix else "Unsupported file type")

    try:
        records = parse_upload_file(content=content, filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=400, detail="No records parsed from file")

    count, source_file = append_source_records(source_format=source_format, records=records)
    response: Dict[str, Any] = {
        "status": "ok",
        "source_format": source_format,
        "source_file": source_file.name,
        "filename": file.filename,
        "written": count,
    }

    return response


@router.post("/api/data-fusion/upload-history-csv")
async def ingest_device_history_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv is supported for this endpoint")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        records = parse_upload_file(content=content, filename=file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=400, detail="No records parsed from CSV")

    written, history_path = save_history_snapshot(records=records)
    aggregation = await rebuild_aggregate_from_history_csv(history_file=history_path.name)

    return {
        "status": "ok",
        "device_id": "device_history",
        "history_file": history_path.name,
        "filename": file.filename,
        "written": written,
        "aggregation": aggregation,
    }


@router.post("/api/data-fusion/aggregate/run-once")
async def run_once() -> Dict[str, Any]:
    return await run_aggregate_and_push_once()


@router.get("/api/data-fusion/status")
async def status() -> Dict[str, Any]:
    return get_status()

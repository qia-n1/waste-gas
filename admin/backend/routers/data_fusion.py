from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.data_fusion import (
    append_device_records,
    get_status,
    parse_upload_file,
    rebuild_aggregate_from_history_csv,
    save_history_snapshot,
    run_aggregate_and_push_once,
)


router = APIRouter(prefix="/api/data-fusion", tags=["data-fusion"])


@router.post("/ingest/{device_id}")
async def ingest_json(device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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

    count = append_device_records(device_id=device_id, records=records)
    return {"status": "ok", "device_id": device_id, "written": count}


@router.post("/upload/{device_id}")
async def ingest_file(device_id: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        records = parse_upload_file(content=content, filename=file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=400, detail="No records parsed from file")

    count = append_device_records(device_id=device_id, records=records)
    response: Dict[str, Any] = {
        "status": "ok",
        "device_id": device_id,
        "filename": file.filename,
        "written": count,
    }

    return response


@router.post("/upload-history-csv")
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


@router.post("/aggregate/run-once")
async def run_once() -> Dict[str, Any]:
    return await run_aggregate_and_push_once()


@router.get("/status")
async def status() -> Dict[str, Any]:
    return get_status()

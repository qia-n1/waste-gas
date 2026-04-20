from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Tuple

import httpx
from openpyxl import Workbook


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_API_BASE = os.getenv("ADMIN_API_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DATA_DIR = Path(
    os.getenv("ADMIN_INGEST_DATA_DIR", str(ROOT_DIR / "admin" / "backend" / "data_fusion"))
)


@dataclass
class ProbeResult:
    name: str
    response_ok: bool
    response_body: Dict[str, Any]
    file_ok: bool
    details: str


def _build_json_payload(marker: str) -> Dict[str, Any]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "timestamp": timestamp,
        "ambient_temp": 21.5,
        "ambient_humidity": 63.5,
        "ambient_pressure": 101.3,
        "rto_out_conc": marker,
        "rto_out_temp": 62.0,
    }


def _write_csv_file(path: Path, marker: str) -> None:
    path.write_text(
        "timestamp,ambient_temp,ambient_humidity,ambient_pressure,rto_out_conc,rto_out_temp\n"
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},21.5,63.5,101.3,{marker},62.0\n",
        encoding="utf-8",
    )


def _write_json_file(path: Path, marker: str) -> None:
    data = _build_json_payload(marker)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_xlsx_file(path: Path, marker: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(["timestamp", "ambient_temp", "ambient_humidity", "ambient_pressure", "rto_out_conc", "rto_out_temp"])
    ws.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 21.5, 63.5, 101.3, marker, 62.0])
    wb.save(path)


def _read_csv_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def _assert_file_contains(path: Path, marker: str) -> Tuple[bool, str]:
    text = _read_csv_text(path)
    if not text:
        return False, f"missing or empty file: {path.name}"
    if marker not in text:
        return False, f"marker {marker!r} not found in {path.name}"
    return True, f"found marker in {path.name}"


def _post_json(api_base: str, marker: str) -> ProbeResult:
    payload = _build_json_payload(marker)
    with httpx.Client(timeout=15.0) as client:
        response = client.post(f"{api_base}/sensor-data", json=payload)
    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    source_file = DEFAULT_DATA_DIR / "json.csv"
    file_ok, details = _assert_file_contains(source_file, marker)
    response_ok = response.status_code == 200 and body.get("source_file") == "json.csv" and body.get("source_format") == "json"
    return ProbeResult("sensor-data/json", response_ok, body, file_ok, details)


def _post_upload(api_base: str, marker: str, suffix: str, writer) -> ProbeResult:
    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        writer(tmp_path, marker)
        with tmp_path.open("rb") as handle:
            files = {"file": (tmp_path.name, handle)}
            with httpx.Client(timeout=15.0) as client:
                response = client.post(f"{api_base}/sensor-data2", files=files)
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        expected_file = {
            ".csv": "csv.csv",
            ".json": "json.csv",
            ".jsonl": "json.csv",
            ".txt": "json.csv",
            ".xlsx": "xlsx.csv",
        }[suffix]
        file_ok, details = _assert_file_contains(DEFAULT_DATA_DIR / expected_file, marker)
        response_ok = response.status_code == 200 and body.get("source_file") == expected_file
        return ProbeResult(f"sensor-data2/{suffix.lstrip('.')}", response_ok, body, file_ok, details)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def run(api_base: str) -> int:
    markers = {
        "json": f"9001.1",
        "csv": f"9002.2",
        "xlsx": f"9003.3",
    }

    probes = [
        _post_json(api_base, markers["json"]),
        _post_upload(api_base, markers["csv"], ".csv", _write_csv_file),
        _post_upload(api_base, markers["xlsx"], ".xlsx", _write_xlsx_file),
        _post_upload(api_base, markers["json"], ".json", _write_json_file),
    ]

    failed = False
    for probe in probes:
        print(f"[{probe.name}] response_ok={probe.response_ok} file_ok={probe.file_ok}")
        print(json.dumps(probe.response_body, ensure_ascii=False, indent=2))
        print(probe.details)
        if not probe.response_ok or not probe.file_ok:
            failed = True

    return 1 if failed else 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify admin data fusion ingestion endpoints.")
    parser.add_argument("--base-url", default=DEFAULT_API_BASE, help="Admin API base URL")
    args = parser.parse_args(argv)
    return run(args.base_url.rstrip("/"))


if __name__ == "__main__":
    raise SystemExit(main())
"""研究数据的可靠存储和来源记录。"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """分块计算文件摘要，避免大文件一次性读入内存。"""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_parquet_atomic(frame: pd.DataFrame, path: str | Path) -> Path:
    """原子写入 Parquet。

    先写临时文件，全部成功后再替换目标。若写入过程中断，不会留下一个名称正常但内容
    不完整的研究数据文件。
    """

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def write_manifest(
    source_path: str | Path,
    output_path: str | Path,
    frame: pd.DataFrame,
    *,
    extra: dict[str, Any] | None = None,
) -> Path:
    """为一次导入创建可审计的 JSON 清单。"""

    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_path": str(source),
        "source_sha256": sha256_file(source),
        "output_path": str(output),
        "row_count": int(len(frame)),
        "columns": list(frame.columns),
        "minimum_trade_date": str(frame["trade_date"].min().date()) if len(frame) else None,
        "maximum_trade_date": str(frame["trade_date"].max().date()) if len(frame) else None,
        "extra": extra or {},
    }
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path

"""CSV、Excel 和 Parquet 文件连接器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from cn_futures_factor.data.connectors.base import DataConnector
from cn_futures_factor.data.normalization import standardize_contract_daily
from cn_futures_factor.exceptions import DataValidationError


class LocalFileConnector(DataConnector):
    """读取单个本地文件并按配置标准化。

    当前刻意只处理单个文件。批量导出数据应先逐文件导入并保存 manifest，再在更高层
    合并，这样可以准确定位问题来自哪一次下载。
    """

    SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".parquet"}

    def __init__(
        self,
        path: str | Path,
        mapping_config: dict[str, Any],
        *,
        source_name: str = "local_file",
        sheet_name: str | int = 0,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.mapping_config = mapping_config
        self.source_name = source_name
        self.sheet_name = sheet_name

    def _read_raw(self) -> pd.DataFrame:
        if not self.path.exists():
            raise DataValidationError(f"数据文件不存在：{self.path}")
        suffix = self.path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            raise DataValidationError(
                f"不支持的文件格式 {suffix}；支持 {sorted(self.SUPPORTED_SUFFIXES)}"
            )

        if suffix == ".csv":
            encoding = self.mapping_config.get("csv_encoding", "utf-8-sig")
            try:
                return pd.read_csv(self.path, encoding=encoding)
            except UnicodeDecodeError as exc:
                raise DataValidationError(
                    f"CSV 编码不是 {encoding}。请在字段映射配置中修改 csv_encoding。"
                ) from exc
        if suffix in {".xlsx", ".xlsm"}:
            return pd.read_excel(self.path, sheet_name=self.sheet_name)
        return pd.read_parquet(self.path)

    def load(self) -> pd.DataFrame:
        raw = self._read_raw()
        return standardize_contract_daily(
            raw,
            self.mapping_config,
            source_name=self.source_name,
        )

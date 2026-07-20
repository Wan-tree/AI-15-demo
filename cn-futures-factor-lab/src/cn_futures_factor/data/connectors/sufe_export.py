"""上财实验数据资源平台人工导出文件适配器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cn_futures_factor.data.connectors.local_files import LocalFileConnector


class SufeExportConnector(LocalFileConnector):
    """为上财授权环境导出文件添加清晰的数据来源标识。

    这里不实现网页登录、Cookie 保存或网页抓取。平台中的 Wind、Choice、CSMAR、
    RESSET 等资源各有自己的许可与导出方式，正确边界是在授权环境内人工导出，再由
    本连接器进行本地处理。
    """

    def __init__(
        self,
        path: str | Path,
        mapping_config: dict[str, Any],
        *,
        sheet_name: str | int = 0,
    ) -> None:
        super().__init__(
            path,
            mapping_config,
            source_name="sufe_authorized_export",
            sheet_name=sheet_name,
        )

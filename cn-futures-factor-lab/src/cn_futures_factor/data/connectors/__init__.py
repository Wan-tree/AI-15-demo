"""外部数据源连接器。

所有连接器最终都输出相同的标准合约日行情表。以后增加官方 API 或 SQL 数据源时，
只需在此目录新增实现，不改动因子和回测代码。
"""

from cn_futures_factor.data.connectors.local_files import LocalFileConnector
from cn_futures_factor.data.connectors.sufe_export import SufeExportConnector

__all__ = ["LocalFileConnector", "SufeExportConnector"]

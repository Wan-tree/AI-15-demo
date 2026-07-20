"""统一日志配置。"""

from __future__ import annotations

import logging


def configure_logging(verbose: bool = False) -> None:
    """配置简洁、适合终端阅读的日志格式。

    本函数允许重复调用。测试或 Notebook 已经安装处理器时，``force=True`` 可以保证
    本项目仍使用一致的日志格式。
    """

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

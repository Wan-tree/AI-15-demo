"""YAML 配置读取工具。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cn_futures_factor.exceptions import ConfigurationError
from cn_futures_factor.paths import resolve_project_path


def load_yaml(path: str | Path) -> dict[str, Any]:
    """读取 YAML，并确保顶层结构是字典。

    配置文件错误时立即失败，比在研究运行到一半后才出现难以理解的 ``KeyError``
    更可靠。
    """

    resolved = resolve_project_path(path)
    if not resolved.exists():
        raise ConfigurationError(f"配置文件不存在：{resolved}")

    try:
        with resolved.open("r", encoding="utf-8") as handle:
            content = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"配置文件不是合法 YAML：{resolved}\n{exc}") from exc

    if not isinstance(content, dict):
        raise ConfigurationError(f"配置文件顶层必须是键值结构：{resolved}")
    return content


def load_default_configs() -> dict[str, dict[str, Any]]:
    """一次性读取演示流水线需要的所有默认配置。"""

    return {
        "base": load_yaml("configs/base.yaml"),
        "factors": load_yaml("configs/factors.yaml"),
        "backtest": load_yaml("configs/backtest.yaml"),
        "universe": load_yaml("configs/universe.yaml"),
    }

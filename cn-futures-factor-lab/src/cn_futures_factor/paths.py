"""项目路径解析与目录创建。

所有路径都相对于项目根目录解析。这样从 VS Code、Notebook、终端或测试中运行时，
不会因为当前工作目录不同而把文件写到意外的位置。
"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """返回项目根目录。

    安装为 editable 包后，本文件位于 ``<root>/src/cn_futures_factor``，因此向上两级
    就是项目根目录。这个结果不依赖用户从哪个目录启动 Python。
    """

    return Path(__file__).resolve().parents[2]


def resolve_project_path(value: str | Path) -> Path:
    """把配置中的相对路径转换为相对于项目根目录的绝对路径。"""

    path = Path(value).expanduser()
    return path if path.is_absolute() else project_root() / path


def ensure_project_directories() -> dict[str, Path]:
    """创建运行必需的目录，并返回名称到绝对路径的映射。"""

    directories = {
        "raw": project_root() / "data/raw",
        "interim": project_root() / "data/interim",
        "processed": project_root() / "data/processed",
        "manifests": project_root() / "data/manifests",
        "artifacts": project_root() / "artifacts",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories

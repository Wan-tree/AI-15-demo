"""项目命令行入口。

这里只负责解析参数和展示结果，核心业务逻辑全部放在独立模块中，因此可以被测试、
Notebook 或未来的 Web 界面直接调用。
"""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import sys
from pathlib import Path

from cn_futures_factor import __version__
from cn_futures_factor.config import load_default_configs, load_yaml
from cn_futures_factor.data.connectors.sufe_export import SufeExportConnector
from cn_futures_factor.data.storage import write_manifest, write_parquet_atomic
from cn_futures_factor.data.validation import validate_contract_daily
from cn_futures_factor.exceptions import FuturesFactorError
from cn_futures_factor.logging import configure_logging
from cn_futures_factor.paths import ensure_project_directories, project_root, resolve_project_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cn-futures",
        description="中国商品期货因子研究框架",
    )
    parser.add_argument("--verbose", action="store_true", help="显示详细日志")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="检查 Python、依赖、配置和项目目录")
    demo = subparsers.add_parser("demo", help="运行真实数据或合成数据的完整演示")
    demo.add_argument(
        "--source",
        choices=("real", "synthetic"),
        default=None,
        help="覆盖配置中的数据源；当前默认 real，synthetic 仅用于测试和离线演示",
    )
    demo.add_argument(
        "--input",
        default=None,
        help="真实数据标准化 Parquet；不指定时读取 configs/base.yaml",
    )

    ingest = subparsers.add_parser("ingest", help="导入上财授权环境导出的本地文件")
    ingest.add_argument("--input", required=True, help="CSV、XLSX、XLSM 或 Parquet 文件")
    ingest.add_argument(
        "--mapping",
        default="configs/field_mappings.yaml",
        help="字段映射 YAML，默认 configs/field_mappings.yaml",
    )
    ingest.add_argument(
        "--output",
        default="data/interim/sufe_contract_daily.parquet",
        help="标准化数据输出位置",
    )
    ingest.add_argument("--sheet", default="0", help="Excel 工作表名称或从 0 开始的序号")
    ingest.add_argument(
        "--allow-inactive-ohlc",
        action="store_true",
        help="允许未活跃合约 OHLC 为零并记录警告；结算价仍必须有效",
    )
    return parser


def _installed_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "未安装"


def _run_doctor() -> None:
    directories = ensure_project_directories()
    configs = load_default_configs()
    print("中国商品期货因子研究框架：环境检查通过")
    print(f"- 项目版本：{__version__}")
    print(f"- Python：{platform.python_version()}")
    print(f"- 解释器：{sys.executable}")
    print(f"- 项目根目录：{project_root()}")
    for package in ("numpy", "pandas", "pyarrow", "matplotlib", "PyYAML"):
        print(f"- {package}：{_installed_version(package)}")
    print(f"- 已读取配置：{', '.join(configs)}")
    print(f"- 已确认目录：{', '.join(str(path) for path in directories.values())}")


def _parse_sheet(value: str) -> str | int:
    """纯数字参数按工作表序号处理，其余作为工作表名称。"""

    return int(value) if value.isdigit() else value


def _run_ingest(args: argparse.Namespace) -> None:
    source_path = resolve_project_path(args.input)
    output_path = resolve_project_path(args.output)
    mapping = load_yaml(args.mapping)
    connector = SufeExportConnector(source_path, mapping, sheet_name=_parse_sheet(args.sheet))
    frame = connector.load()
    report = validate_contract_daily(
        frame,
        allow_inactive_ohlc=bool(args.allow_inactive_ohlc),
    )
    write_parquet_atomic(frame, output_path)
    manifest_path = write_manifest(
        source_path,
        output_path,
        frame,
        extra={
            "mapping": str(Path(args.mapping)),
            "allow_inactive_ohlc": bool(args.allow_inactive_ohlc),
            "validation": report.summary(),
        },
    )
    print(report.summary())
    print(f"标准化数据：{output_path}")
    print(f"来源清单：{manifest_path}")


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    try:
        if args.command == "doctor":
            _run_doctor()
        elif args.command == "demo":
            # 延迟导入演示流水线，避免 doctor 命令仅做环境检查时就初始化 Matplotlib。
            from cn_futures_factor.pipelines.demo import run_demo

            result = run_demo(data_source=args.source, input_path=args.input)
            print("演示运行成功。")
            print(f"数据源：{result.data_source} ({result.source_path})")
            print(f"报告：{result.report_path}")
            print(f"净值图：{result.chart_path}")
            print(f"总收益：{result.metrics['total_return']:.2%}")
            print(f"最大回撤：{result.metrics['max_drawdown']:.2%}")
        elif args.command == "ingest":
            _run_ingest(args)
        else:
            parser.error(f"未知命令：{args.command}")
    except FuturesFactorError as exc:
        parser.exit(2, f"错误：{exc}\n")

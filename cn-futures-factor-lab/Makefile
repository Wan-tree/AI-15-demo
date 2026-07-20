.PHONY: install doctor demo test lint format clean-demo

install:
	python -m pip install -e ".[dev]"

doctor:
	python -m cn_futures_factor doctor

demo:
	python -m cn_futures_factor demo

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

# 只删除可重新生成的 demo 产物，不接触任何真实数据目录。
clean-demo:
	rm -f data/raw/demo_contract_daily.csv
	rm -f data/processed/demo_contract_daily.parquet
	rm -f data/processed/demo_main_panel.parquet
	rm -f data/processed/demo_features.parquet
	rm -f artifacts/demo/daily_returns.csv
	rm -f artifacts/demo/positions.csv
	rm -f artifacts/demo/equity_curve.png
	rm -f artifacts/demo/report.md


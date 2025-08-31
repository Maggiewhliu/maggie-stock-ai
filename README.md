# Maggie's Stock AI (Slim B)
- 純函數演算法（Max Pain / Gamma Exposure / BS & IV 反解）
- yfinance 提供者（不需 API key）
- Redis(可選) + 檔案快取；SWR + 單飛鎖
- CLI / Telegram Bot / GitHub Actions

## 快速開始
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 離線驗算法
python -m src.cli maxpain --from-csv data/sample_options.csv

# 線上
python -m src.cli maxpain TSLA
python -m src.cli gex TSLA

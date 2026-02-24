# 中國信託信用卡 CSV 格式

## 狀態

✅ 有實際 CSV 樣本，已實作

## CSV 樣本

```csv
交易日,商店,消費金額
2024-01-10,台北101美食街,280
2024-01-12,中油加油站,1200
2024-01-15,誠品書店,450
2024-01-18,屈臣氏,320
```

## 欄位說明

| index | 欄位名稱 | 格式       | 說明          |
| ----- | -------- | ---------- | ------------- |
| 0     | 交易日   | YYYY-MM-DD | 完整日期      |
| 1     | 商店     | string     | 商店/交易名稱 |
| 2     | 消費金額 | 數字       | 正數=消費     |

## 特殊處理

- **編碼**：UTF-8（無 BOM）
- **格式簡單**：無動態標題，固定 skip_rows=1

## BankCsvConfig

```python
BankCsvConfig(
    code="CTBC",
    name="中國信託",
    date_column=0,
    date_format="%Y-%m-%d",
    description_column=1,
    amount_column=2,
    skip_rows=1,
    encoding="utf-8",
)
```

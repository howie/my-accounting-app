# 富邦銀行信用卡 CSV 格式

## 狀態

⚠️ 需要實際 CSV 樣本確認。以下為估計設定，請以實際銀行匯出檔案驗證後更新。

## 預估 CSV 格式樣板

```csv
交易日期,交易說明,交易金額
2024-01-10,全家便利商店,85
2024-01-12,統一超商,50
```

## 欄位說明（待確認）

| index | 欄位名稱 | 格式       | 說明          |
| ----- | -------- | ---------- | ------------- |
| 0     | 交易日期 | YYYY-MM-DD | 完整日期      |
| 1     | 交易說明 | string     | 商店/交易名稱 |
| 2     | 交易金額 | 數字       | 正數=消費     |

## BankCsvConfig（待更新）

```python
BankCsvConfig(
    code="FUBON",
    name="富邦銀行",
    date_column=0,
    date_format="%Y-%m-%d",
    description_column=1,
    amount_column=2,
    skip_rows=1,
    encoding="utf-8",
)
```

## 取得實際樣本

請至富邦銀行網銀 → 信用卡 → 帳單查詢 → 匯出 CSV，並更新本文件。

# 台新銀行活期存款對帳單 CSV 格式

## 狀態

⚠️ 需要實際 CSV 樣本確認。以下為估計設定，請以實際銀行匯出檔案驗證後更新。

## 預估 CSV 格式樣板

```csv
交易日期,交易說明,提款,存款,餘額
2024/01/10,ATM提款,3000,,47000
2024/01/12,轉帳收入,,10000,57000
2024/01/15,水電費繳費,2500,,54500
```

## 欄位說明（待確認）

| index | 欄位名稱 | 格式       | 說明                |
| ----- | -------- | ---------- | ------------------- |
| 0     | 交易日期 | YYYY/MM/DD | 完整日期            |
| 1     | 交易說明 | string     | 交易描述            |
| 2     | 提款     | 數字或空白 | 出帳金額（EXPENSE） |
| 3     | 存款     | 數字或空白 | 入帳金額（INCOME）  |
| 4     | 餘額     | 數字       | 不使用              |

## 特殊處理

- **編碼**：Big5（繁體中文銀行常見）

## BankStatementConfig（待更新）

```python
BankStatementConfig(
    code="TAISHIN",
    name="台新銀行",
    bank_account_name="台新銀行.活期存款",
    date_column=0,
    date_format="%Y/%m/%d",
    description_column=1,
    debit_column=2,
    credit_column=3,
    amount_column=None,
    balance_column=4,
    skip_rows=1,
    encoding="big5",
)
```

## 取得實際樣本

請至台新銀行網銀 → 帳戶查詢 → 存款明細查詢 → 匯出 CSV，並更新本文件。

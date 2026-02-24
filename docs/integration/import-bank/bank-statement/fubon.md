# 富邦銀行活期存款對帳單 CSV 格式

## 狀態

⚠️ 需要實際 CSV 樣本確認。以下為估計設定，請以實際銀行匯出檔案驗證後更新。

## 預估 CSV 格式樣板

```csv
交易日期,交易說明,提款金額,存款金額,餘額
2024-01-10,跨行轉出,5000,,95000
2024-01-12,薪資轉入,,80000,175000
2024-01-15,信用卡繳費,15000,,160000
```

## 欄位說明（待確認）

| index | 欄位名稱 | 格式       | 說明                       |
| ----- | -------- | ---------- | -------------------------- |
| 0     | 交易日期 | YYYY-MM-DD | 完整日期（注意破折號分隔） |
| 1     | 交易說明 | string     | 交易描述                   |
| 2     | 提款金額 | 數字或空白 | 出帳金額（EXPENSE）        |
| 3     | 存款金額 | 數字或空白 | 入帳金額（INCOME）         |
| 4     | 餘額     | 數字       | 不使用                     |

## BankStatementConfig（待更新）

```python
BankStatementConfig(
    code="FUBON",
    name="富邦銀行",
    bank_account_name="富邦銀行.活期存款",
    date_column=0,
    date_format="%Y-%m-%d",
    description_column=1,
    debit_column=2,
    credit_column=3,
    amount_column=None,
    balance_column=4,
    skip_rows=1,
    encoding="utf-8",
)
```

## 取得實際樣本

請至富邦銀行網銀 → 帳戶管理 → 存款明細 → 匯出 CSV，並更新本文件。

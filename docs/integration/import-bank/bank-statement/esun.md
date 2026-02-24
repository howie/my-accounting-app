# 玉山銀行活期存款對帳單 CSV 格式

## 狀態

⚠️ 需要實際 CSV 樣本確認。以下為估計設定，請以實際銀行匯出檔案驗證後更新。

## 預估 CSV 格式樣板

```csv
日期,說明,支出,收入,餘額
2024/01/10,便利商店繳費,500,,25000
2024/01/12,薪資,,60000,85000
2024/01/15,網路繳費,1200,,83800
```

## 欄位說明（待確認）

| index | 欄位名稱 | 格式       | 說明                |
| ----- | -------- | ---------- | ------------------- |
| 0     | 日期     | YYYY/MM/DD | 完整日期            |
| 1     | 說明     | string     | 交易描述            |
| 2     | 支出     | 數字或空白 | 出帳金額（EXPENSE） |
| 3     | 收入     | 數字或空白 | 入帳金額（INCOME）  |
| 4     | 餘額     | 數字       | 不使用              |

## BankStatementConfig（待更新）

```python
BankStatementConfig(
    code="ESUN",
    name="玉山銀行",
    bank_account_name="玉山銀行.活期存款",
    date_column=0,
    date_format="%Y/%m/%d",
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

請至玉山銀行網銀 → 帳戶服務 → 存款明細 → 匯出 CSV，並更新本文件。

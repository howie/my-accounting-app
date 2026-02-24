# 中國信託活期存款對帳單 CSV 格式

## 狀態

⚠️ 需要實際 CSV 樣本確認。以下為估計設定，請以實際銀行匯出檔案驗證後更新。

## 預估 CSV 格式樣板

```csv
交易日期,摘要,提款,存款,餘額
2024/01/10,跨行ATM提款,1000,,88000
2024/01/12,匯款轉入,,5000,93000
2024/01/15,網路轉帳,3000,,90000
```

## 欄位說明（待確認）

| index | 欄位名稱 | 格式       | 說明                |
| ----- | -------- | ---------- | ------------------- |
| 0     | 交易日期 | YYYY/MM/DD | 完整日期            |
| 1     | 摘要     | string     | 交易描述            |
| 2     | 提款     | 數字或空白 | 出帳金額（EXPENSE） |
| 3     | 存款     | 數字或空白 | 入帳金額（INCOME）  |
| 4     | 餘額     | 數字       | 不使用（可作驗證）  |

## BankStatementConfig（待更新）

```python
BankStatementConfig(
    code="CTBC",
    name="中國信託",
    bank_account_name="中國信託.活期存款",
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

請至中國信託網銀 → 帳戶服務 → 交易明細查詢 → 匯出 CSV，並更新本文件。

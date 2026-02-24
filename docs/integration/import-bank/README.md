# 銀行 CSV 匯入格式文件

本目錄說明各銀行 CSV 匯入格式，作為 adapter 實作的規格參考。

## 兩種匯入類型

### 1. 信用卡帳單 (`CREDIT_CARD`)

- 帳戶類型：LIABILITY（負債）
- 交易方向：單向（支出）
- `from` = 信用卡（LIABILITY），`to` = 支出科目（EXPENSE）

### 2. 銀行活期存款對帳單 (`BANK_STATEMENT`)

- 帳戶類型：ASSET（資產）
- 交易方向：雙向（出帳 + 入帳）
- 出帳：`from` = 銀行帳戶（ASSET），`to` = 支出科目（EXPENSE）
- 入帳：`from` = 收入科目（INCOME），`to` = 銀行帳戶（ASSET）

## 目錄結構

```
credit-card/
├── cathay.md    # 國泰世華信用卡（有實際樣本）
├── ctbc.md      # 中國信託信用卡（有實際樣本）
├── esun.md      # 玉山銀行信用卡（待樣本）
├── taishin.md   # 台新銀行信用卡（待樣本）
└── fubon.md     # 富邦銀行信用卡（待樣本）

bank-statement/
├── cathay.md    # 國泰世華活期存款（待樣本）
├── ctbc.md      # 中國信託活期存款（待樣本）
├── esun.md      # 玉山銀行活期存款（待樣本）
├── taishin.md   # 台新銀行活期存款（待樣本）
└── fubon.md     # 富邦銀行活期存款（待樣本）
```

## 如何新增銀行

1. 在對應目錄新增 `<bank>.md` 格式文件
2. 在 `backend/src/services/bank_configs.py` 新增 config entry
3. 提供實際 CSV 樣本至 `backend/tests/fixtures/csv/`
4. 新增對應的 parser 測試

## 金額欄位模式

| 模式                           | 說明                             | 適用場景             |
| ------------------------------ | -------------------------------- | -------------------- |
| `debit_column + credit_column` | 提款欄 + 存款欄（兩個獨立欄位）  | 多數台灣銀行活期帳戶 |
| `amount_column`（帶正負號）    | 單一金額欄，負數=支出，正數=收入 | 部分銀行格式         |

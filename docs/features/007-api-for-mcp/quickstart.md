# Quickstart: MCP API 對話式記帳

**Feature**: 007-api-for-mcp
**Date**: 2026-01-12
**Status**: Complete

## 概述

本指南說明如何設定 MCP API，讓 AI 助手（Claude、ChatGPT）能夠透過對話幫你記帳。

## 前置需求

- LedgerOne 帳本系統已運行
- 至少一個帳本已建立
- 基本科目已設定（現金、餐飲等）

## 步驟 1：產生 API Token

1. 登入 LedgerOne 網頁介面
2. 前往 **設定** → **API Tokens**
3. 點擊 **建立新 Token**
4. 輸入名稱（例如：「Claude Desktop」）
5. 複製產生的 token（只會顯示一次！）

```
ldo_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

## 步驟 2：設定 AI 助手

### Claude Desktop

編輯 Claude Desktop 設定檔：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ledgerone": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer ldo_abc123..."
      }
    }
  }
}
```

### ChatGPT (Custom GPT)

在 Custom GPT 的 Actions 設定中：

1. 新增 Action
2. Server URL: `http://your-server:8000/mcp`
3. Authentication: Bearer Token
4. Token: `ldo_abc123...`

## 步驟 3：開始對話記帳

連接成功後，你可以這樣對 AI 說：

### 記錄支出

```
「午餐吃了 150 元」
「今天搭捷運花了 65 元」
「買咖啡 85 元，從現金支出」
```

### 查詢餘額

```
「我的現金還剩多少？」
「列出所有資產科目」
「這個月的餐飲花費」
```

### 查詢交易

```
「今天記了哪些帳？」
「上週的支出明細」
「找出所有交通相關的交易」
```

## 常見問題

### Q: 找不到科目怎麼辦？

AI 會自動建議相似的科目名稱。例如說「早餐」，系統會建議「餐飲」、「外食」等。

### Q: 如何指定帳本？

如果你有多個帳本，AI 會詢問要使用哪一個。你也可以直接說：

```
「在家庭帳本記一筆支出」
```

### Q: 日期怎麼指定？

預設是今天。你可以說：

```
「昨天買了書 350 元」
「1月5日的電話費 499 元」
```

### Q: Token 洩漏怎麼辦？

1. 登入網頁介面
2. 前往 **設定** → **API Tokens**
3. 找到該 token，點擊 **撤銷**
4. 建立新的 token

## 可用工具列表

| 工具                 | 功能     | 範例指令              |
| -------------------- | -------- | --------------------- |
| `create_transaction` | 建立交易 | 「記一筆午餐 120 元」 |
| `list_accounts`      | 列出科目 | 「有哪些支出科目？」  |
| `get_account`        | 查詢餘額 | 「現金還剩多少？」    |
| `list_transactions`  | 查詢交易 | 「這週的交易紀錄」    |
| `list_ledgers`       | 列出帳本 | 「我有哪些帳本？」    |

## 進階設定

### 自訂 MCP Server URL

如果後端不在 localhost，更新設定：

```json
{
  "mcpServers": {
    "ledgerone": {
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer ldo_..."
      }
    }
  }
}
```

### 多帳本使用者

如果你有多個帳本，可以建立多個 MCP 連線，每個連線對應不同帳本的預設設定。

## 下一步

- 查看 [API 合約文件](./contracts/mcp-tools.md) 了解完整 API 規格
- 查看 [資料模型](./data-model.md) 了解資料結構

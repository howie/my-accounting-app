# Feature Specification: MCP API 對話式記帳介面

**Feature Branch**: `007-api-for-mcp`
**Created**: 2026-01-11
**Status**: Draft
**Input**: User description: "007-api-for-mcp 產生 mcp 接口之後可以直接串接 ChatGPT, Claude 直接用對話的方式直接幫我記帳"

## Clarifications

### Session 2026-01-11

- Q: API token 的認證機制與有效期限為何？ → A: 長期 token（不過期，可隨時撤銷）
- Q: MCP Server 的部署方式為何？ → A: 整合到現有 FastAPI 後端（共用 process）
- Q: 是否需要實作 API 速率限制？ → A: 不需要（初期版本，信任使用者）

## User Scenarios & Testing _(mandatory)_

### User Story 1 - 對話式新增交易 (Priority: P1)

使用者透過 ChatGPT 或 Claude 等 AI 助手，以自然語言描述一筆支出或收入（例如：「午餐吃了 150 元」或「今天收到薪水 50000」），AI 助手透過 MCP 介面呼叫系統 API，自動建立對應的記帳交易。

**Why this priority**: 這是最核心的功能，讓使用者能透過對話快速記帳，大幅降低記帳的門檻與摩擦。

**Independent Test**: 可以獨立測試 - 透過 MCP 工具呼叫新增交易 API，傳入金額、科目、描述等參數，驗證交易正確寫入系統。

**Acceptance Scenarios**:

1. **Given** AI 助手已連接 MCP 介面, **When** AI 助手呼叫新增交易工具並傳入必要參數（金額、來源科目、目標科目、描述）, **Then** 系統建立交易並回傳成功訊息與交易摘要
2. **Given** AI 助手傳入的科目名稱不存在, **When** AI 助手呼叫新增交易工具, **Then** 系統回傳錯誤訊息列出可用科目，讓 AI 助手能引導使用者選擇
3. **Given** AI 助手傳入的金額格式不正確, **When** AI 助手呼叫新增交易工具, **Then** 系統回傳明確的驗證錯誤訊息

---

### User Story 2 - 查詢科目與餘額 (Priority: P1)

使用者透過 AI 助手詢問帳戶餘額或科目清單（例如：「我的現金還剩多少？」或「列出我所有的支出科目」），AI 助手透過 MCP 介面查詢系統資料並回覆使用者。

**Why this priority**: 記帳後查詢餘額是基本需求，與新增交易同屬核心功能。AI 助手需要科目資訊才能正確建立交易。

**Independent Test**: 可以獨立測試 - 透過 MCP 工具呼叫查詢科目 API，驗證能取得科目清單及各科目餘額。

**Acceptance Scenarios**:

1. **Given** AI 助手已連接 MCP 介面, **When** AI 助手呼叫查詢科目工具, **Then** 系統回傳科目清單，包含科目名稱、類型、餘額
2. **Given** 使用者有多個帳本, **When** AI 助手呼叫查詢科目工具並指定帳本, **Then** 系統回傳該帳本的科目清單
3. **Given** AI 助手查詢特定科目, **When** AI 助手呼叫查詢單一科目工具, **Then** 系統回傳該科目的詳細資訊與餘額

---

### User Story 3 - 查詢交易紀錄 (Priority: P2)

使用者透過 AI 助手查詢過去的交易紀錄（例如：「這個月我花了多少錢吃飯？」或「上週有哪些支出？」），AI 助手透過 MCP 介面查詢並彙整回覆。

**Why this priority**: 查詢歷史紀錄能幫助使用者了解消費模式，但相較於即時記帳是次要需求。

**Independent Test**: 可以獨立測試 - 透過 MCP 工具呼叫查詢交易 API，傳入日期範圍與篩選條件，驗證能取得正確的交易清單。

**Acceptance Scenarios**:

1. **Given** AI 助手已連接 MCP 介面, **When** AI 助手呼叫查詢交易工具並指定日期範圍, **Then** 系統回傳該期間的交易清單
2. **Given** AI 助手指定篩選科目, **When** AI 助手呼叫查詢交易工具, **Then** 系統回傳僅包含該科目的交易
3. **Given** 查詢結果超過 100 筆, **When** AI 助手呼叫查詢交易工具, **Then** 系統回傳分頁結果並提供總筆數

---

### User Story 4 - 帳本管理 (Priority: P2)

使用者透過 AI 助手查詢或切換帳本（例如：「我有哪些帳本？」或「切換到家庭帳本」），AI 助手透過 MCP 介面取得帳本清單。

**Why this priority**: 多帳本支援是進階功能，但 AI 助手需要知道操作的目標帳本。

**Independent Test**: 可以獨立測試 - 透過 MCP 工具呼叫查詢帳本 API，驗證能取得帳本清單。

**Acceptance Scenarios**:

1. **Given** AI 助手已連接 MCP 介面, **When** AI 助手呼叫查詢帳本工具, **Then** 系統回傳使用者的帳本清單
2. **Given** AI 助手指定帳本 ID, **When** AI 助手呼叫後續操作, **Then** 系統在指定帳本上執行操作

---

### Edge Cases

- 未指定帳本：當使用者有多個帳本但未指定時，系統應回傳帳本清單讓 AI 助手詢問使用者
- 科目模糊匹配：使用者說「早餐」但科目叫「餐飲」時，API 應能提供相似科目建議
- 日期解析：AI 傳入「上週」「這個月」等相對日期時，系統應正確解析為日期範圍
- 金額單位：預設使用新台幣，不需處理多幣別轉換
- 高頻率呼叫：初期版本不實作速率限制，系統應能處理正常使用情境的請求頻率
- 無效 token：API token 過期或無效時，回傳明確的認證錯誤
- 空結果：查詢無結果時，回傳空陣列而非錯誤

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide MCP-compatible tool definitions that can be loaded by Claude, ChatGPT, and other MCP-supporting AI assistants
- **FR-002**: System MUST provide a tool for creating transactions with parameters: amount, from_account, to_account, description, date (optional, defaults to today), notes (optional)
- **FR-003**: System MUST provide a tool for listing all accounts with their names, types, and current balances
- **FR-004**: System MUST provide a tool for querying account details by account ID or name
- **FR-005**: System MUST provide a tool for listing transactions with filters: date range, account, limit, offset
- **FR-006**: System MUST provide a tool for listing available ledgers
- **FR-007**: System MUST return structured responses that AI assistants can easily interpret and present to users
- **FR-008**: System MUST return clear error messages with actionable information (e.g., list of valid accounts when an invalid account is specified)
- **FR-009**: System MUST accept ledger_id parameter for all data operations to support multi-ledger scenarios
- **FR-010**: System MUST validate all input parameters and return descriptive validation errors
- **FR-011**: System MUST support account lookup by exact name or ID
- **FR-012**: System MUST return account suggestions when an exact match is not found (fuzzy matching)
- **FR-013**: System MUST authenticate all API requests using long-lived bearer tokens
- **FR-014**: System MUST allow users to create, list, and revoke API tokens from the web interface

### Data Integrity Requirements _(required for features modifying financial data)_

- **DI-001**: System MUST validate all transaction amounts (positive numbers with max 2 decimal places for TWD)
- **DI-002**: System MUST create audit trail entries for all transactions created via MCP API, marking source as "mcp"
- **DI-003**: System MUST enforce double-entry bookkeeping for all transactions (debits = credits)
- **DI-004**: System MUST NOT allow partial transaction creation - all validation must pass before persisting
- **DI-005**: System MUST return the created transaction details upon successful creation for verification

### Key Entities _(include if feature involves data)_

- **MCP Tool Definition**: Schema defining each available tool (name, description, parameters, return type) in MCP-compatible format
- **Tool Response**: Standardized response structure including success status, data, and error information
- **Account Summary**: Condensed account information optimized for AI consumption (id, name, type, balance)
- **Transaction Summary**: Condensed transaction information for listing (id, date, amount, accounts, description)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: AI assistants can successfully create transactions within 2 seconds of tool invocation
- **SC-002**: AI assistants can retrieve account balances within 1 second
- **SC-003**: 95% of valid transaction creation requests succeed on first attempt
- **SC-004**: Error messages are clear enough that AI assistants can provide helpful guidance without additional API calls
- **SC-005**: All MCP tools are documented with examples that AI assistants can use for context
- **SC-006**: System handles concurrent API requests without data corruption or race conditions

## Assumptions

- MCP (Model Context Protocol) is the standard interface for AI assistant tool integration
- Initial implementation targets Claude and ChatGPT as primary AI assistants
- Authentication uses long-lived API tokens that users generate from the web interface; tokens do not expire but can be revoked at any time
- Each user has their own set of API tokens; tokens are not shared across users
- Users can create multiple tokens (e.g., one per AI assistant) and revoke them individually
- The MCP server is integrated into the existing FastAPI backend, sharing the same process and database connections
- AI assistants are responsible for natural language understanding; the API receives structured parameters

## Out of Scope

- Natural language parsing within the API (AI assistants handle this)
- Multi-currency support (TWD only for initial release)
- Recurring transaction creation via MCP
- Budget management via MCP
- Report generation via MCP
- Real-time notifications to AI assistants
- Voice input processing (handled by AI assistant platforms)
- API rate limiting (deferred to future release if needed)

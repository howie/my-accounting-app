# Feature Specification: AI Multi-Channel Integration

**Feature Branch**: `012-ai-multi-channel`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "透過多種 AI 管道（Slack、Telegram、LINE、ChatGPT、Gemini）進行記帳操作，並支援語音輸入和 Email 信用卡帳單自動匯入"

## User Scenarios & Testing _(mandatory)_

### User Story 4 - 使用者帳號綁定與管道管理 (Priority: P1) — Foundation

使用者需要將各管道（Bot、AI 助手、Email）與其記帳系統帳號進行綁定，並能在設定頁面管理已連結的管道。

**Why this priority**: 這是所有管道功能的前提——使用者必須先完成綁定，系統才能辨識訊息來源對應到哪個帳號。沒有這個功能，其他所有 user story 都無法運作。

**Independent Test**: 可在設定頁面發起 Telegram Bot 綁定流程，完成後在管道管理頁面看到已連結的 Telegram 帳號。

**Acceptance Scenarios**:

1. **Given** 使用者已登入系統, **When** 使用者在設定頁面選擇「綁定 Telegram」, **Then** 系統提供綁定指引（如驗證碼），使用者在 Telegram Bot 中輸入驗證碼完成綁定
2. **Given** 使用者已綁定多個管道, **When** 使用者查看管道管理頁面, **Then** 系統顯示所有已綁定管道的狀態（連結時間、最近使用時間）
3. **Given** 使用者已綁定某管道, **When** 使用者選擇解除綁定, **Then** 系統確認後移除綁定，該管道不再能存取使用者帳務資料
4. **Given** 使用者授權 Gmail, **When** 授權流程完成, **Then** 系統安全儲存授權憑證，並顯示已連結的 Gmail 帳號

---

### User Story 1 - AI 助手對話記帳 (Priority: P1)

使用者透過 AI 助手（ChatGPT、Gemini、Claude）以自然語言進行記帳。例如使用者在 ChatGPT 對話中輸入「午餐花了 120 元」，系統自動建立一筆交易記錄，包含金額、日期、和建議的帳戶分類。

**Why this priority**: 這是最核心的價值主張——讓使用者在任何 AI 工具中都能記帳，無需切換到專門的記帳介面。AI 助手整合工作量最低但價值最高，因為使用者已有這些工具的使用習慣。

**Independent Test**: 可透過任一 AI 助手輸入自然語言記帳指令，驗證交易是否正確建立於系統中，並可在主應用程式中查看該筆交易。

**Acceptance Scenarios**:

1. **Given** 使用者已將記帳系統連結至 AI 助手, **When** 使用者輸入「午餐花了 120 元」, **Then** 系統建立一筆支出交易，金額 120，日期為今天，並建議「餐飲」分類
2. **Given** 使用者已連結 AI 助手, **When** 使用者輸入「查詢本月餐飲花費」, **Then** 系統回傳本月餐飲類別的總金額和交易明細摘要
3. **Given** 使用者已連結 AI 助手, **When** 使用者輸入「查帳戶餘額」, **Then** 系統回傳所有帳戶的目前餘額清單
4. **Given** 使用者輸入模糊的記帳指令如「買東西 500」, **When** 系統無法確定分類, **Then** 系統詢問使用者確認分類後再建立交易

---

### User Story 2 - 通訊軟體 Bot 記帳 (Priority: P2)

使用者透過日常使用的通訊軟體（Telegram、LINE、Slack）的 Bot 進行記帳。使用者傳送文字或語音訊息給 Bot，Bot 解析內容並建立交易記錄。

**Why this priority**: 通訊軟體是使用者每天最常開啟的應用，比專門打開記帳 App 更方便。Telegram 支援語音輸入，LINE 在台灣使用率最高，兩者都能大幅降低記帳的摩擦力。

**Independent Test**: 可透過 Telegram Bot 傳送文字訊息「咖啡 85 元」，驗證 Bot 回覆確認訊息，且交易正確建立於系統中。

**Acceptance Scenarios**:

1. **Given** 使用者已綁定 Telegram Bot, **When** 使用者傳送文字訊息「咖啡 85 元」, **Then** Bot 建立交易並回覆確認訊息（含金額、分類、日期）
2. **Given** 使用者已綁定 Telegram Bot, **When** 使用者傳送語音訊息說「晚餐花了三百五」, **Then** Bot 將語音轉為文字、解析金額 350、建立交易並回覆確認
3. **Given** 使用者已綁定 LINE Bot, **When** 使用者傳送「查餘額」, **Then** Bot 回覆所有帳戶的餘額摘要
4. **Given** 使用者已綁定 Slack Bot, **When** 使用者輸入 slash command 記帳指令, **Then** Bot 建立交易並在頻道中回覆確認
5. **Given** Bot 收到無法辨識的訊息, **When** 意圖解析失敗, **Then** Bot 回覆友善的錯誤訊息並提供使用說明

---

### User Story 3 - Email 信用卡帳單自動匯入 (Priority: P3)

使用者授權系統讀取 Email 信箱，系統定期掃描信用卡帳單 email，自動解析交易明細，產生預覽供使用者確認後批次匯入。

**Why this priority**: 信用卡帳單匯入可以一次補齊大量交易記錄，減少逐筆手動輸入的負擔。但因工作量較高且需要 email 授權流程，排在 P3。

**Independent Test**: 可設定 Email 連結後，系統偵測到信用卡帳單 email，解析出交易明細，使用者在預覽畫面確認後匯入所有交易。

**Acceptance Scenarios**:

1. **Given** 使用者已授權 Gmail 存取, **When** 系統偵測到新的信用卡帳單 email, **Then** 系統解析出所有交易明細（日期、商家名稱、金額）並產生預覽清單
2. **Given** 系統已產生帳單預覽, **When** 使用者確認匯入, **Then** 所有交易批次建立，每筆標記來源為「Email 匯入」
3. **Given** 系統已產生帳單預覽, **When** 使用者修改部分交易的分類後確認, **Then** 系統依使用者修改結果匯入交易
4. **Given** 帳單解析部分失敗, **When** 某些交易無法正確解析, **Then** 系統標記這些交易為「需人工確認」，其餘正常匯入
5. **Given** 系統掃描 email, **When** 發現重複的帳單（已匯入過）, **Then** 系統跳過該帳單並通知使用者

---

### Edge Cases

- 使用者同時從多個管道送出記帳指令時，系統如何處理並行請求？（應各自獨立處理，不互相干擾）
- Bot token 或 email 授權失效時，系統如何通知使用者重新授權？
- 自然語言解析結果與使用者意圖不符時，使用者如何修正已建立的交易？（應提供撤銷/修改功能）
- 訊息平台 API 暫時不可用時，系統如何暫存待處理的訊息？
- LINE 免費方案訊息額度用完時，系統如何處理？（應通知使用者並暫停回覆）
- Email 帳單格式變更導致解析失敗時，系統如何通知使用者？
- 使用者嘗試綁定已被其他帳號綁定的管道帳號時，系統應拒絕並提示

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: 系統 MUST 接受來自 AI 助手（ChatGPT、Gemini、Claude）的自然語言記帳指令，並建立對應的交易記錄
- **FR-002**: 系統 MUST 接受來自通訊軟體 Bot（Telegram、LINE、Slack）的文字訊息，解析意圖後執行記帳或查詢操作
- **FR-003**: 系統 MUST 支援透過 Telegram Bot 接收語音訊息，轉換為文字後進行記帳
- **FR-004**: 系統 MUST 提供使用者帳號與各管道帳號的綁定/解除綁定功能
- **FR-005**: 系統 MUST 定期掃描已授權的 Email 信箱，偵測信用卡帳單並解析交易明細
- **FR-006**: 系統 MUST 在匯入 email 帳單交易前，產生預覽清單供使用者確認
- **FR-007**: 系統 MUST 對所有透過外部管道建立的交易，記錄來源管道資訊（如 telegram、line、email-import 等）
- **FR-008**: 系統 MUST 驗證所有外部管道的 webhook 請求真實性（signature verification）
- **FR-009**: 系統 MUST 在自然語言解析無法確定分類時，向使用者詢問確認
- **FR-010**: 系統 MUST 偵測重複的 email 帳單，避免重複匯入
- **FR-011**: 系統 MUST 在管道管理頁面顯示各管道的連結狀態和最近使用時間
- **FR-012**: 系統 MUST 對各管道 endpoint 實施速率限制，每個使用者每分鐘不超過 30 次請求
- **FR-013**: 系統 MUST 在管道授權失效時，透過可用管道或 email 通知使用者重新授權

### Data Integrity Requirements _(required for features modifying financial data)_

- **DI-001**: 系統 MUST 驗證所有透過外部管道提交的財務金額（格式、範圍 0.01~9,999,999.99、精度至小數第二位）
- **DI-002**: 系統 MUST 為所有透過外部管道建立/修改的交易維護審計軌跡（來源管道、原始訊息、時間戳記、操作者）
- **DI-003**: 系統 MUST 確保透過任何管道建立的交易都遵循複式記帳原則（借方 = 貸方）
- **DI-004**: 系統 MUST 在批次匯入 email 帳單前要求使用者明確確認，防止意外資料寫入
- **DI-005**: 系統 MUST 確保所有管道建立的交易金額計算可追溯至原始來源訊息

### Key Entities

- **Channel Binding（管道綁定）**: 記錄使用者帳號與外部管道帳號的對應關係，包含管道類型、外部帳號識別碼、綁定狀態、連結時間
- **Channel Message Log（管道訊息紀錄）**: 記錄所有透過外部管道收到的原始訊息，作為審計軌跡，包含來源管道、原始內容、解析結果、處理狀態
- **Email Import Batch（Email 匯入批次）**: 記錄每次 email 帳單匯入的批次資訊，包含來源 email、解析的交易數量、使用者確認狀態、匯入時間
- **Email Authorization（Email 授權）**: 記錄使用者的 email 存取授權資訊，包含授權狀態、授權範圍、到期時間

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: 使用者透過任一管道以自然語言輸入記帳指令後，90% 以上的情況下系統能在 5 秒內正確建立交易
- **SC-002**: 使用者從發出記帳訊息到收到確認回覆，整體耗時不超過 10 秒
- **SC-003**: 信用卡帳單 email 解析準確率達到 85% 以上（正確提取日期、金額、商家名稱）
- **SC-004**: 使用者完成管道綁定流程不超過 3 分鐘
- **SC-005**: 系統每月穩定處理至少 500 則以上的管道訊息（涵蓋所有管道總和），不發生資料遺失
- **SC-006**: 所有透過外部管道建立的交易，100% 記錄來源管道和原始訊息作為審計軌跡

## Assumptions

- 使用者已有雲端部署的後端服務（依賴 Feature 011-cloud-deployment）
- 使用者會自行在各平台（Telegram BotFather、LINE Developer Console、Slack App 管理介面）建立 Bot 並取得 API credentials
- 目標為個人記帳使用，訊息量在免費方案額度內（LINE 500 則/月、Slack Free workspace）
- AI 助手整合透過現有的 MCP server 或 OpenAPI spec 進行，不需要額外的 AI 模型訓練
- Email 帳單匯入初期僅支援 Gmail（透過 OAuth2），未來可擴展至其他 email 服務
- 自然語言解析使用現有的 LLM provider（Gemini/Claude），不需自建 NLP 模型
- 信用卡帳單 email 格式因銀行而異，初期以台灣主要銀行的常見格式為優先支援目標

## Dependencies

- **011-cloud-deployment**: 後端必須部署到雲端才能接收外部 Webhook
- **001-core-accounting**: 依賴現有的交易建立、帳戶查詢等核心 API
- **007-api-for-mcp**: AI 助手透過 MCP 協定進行操作

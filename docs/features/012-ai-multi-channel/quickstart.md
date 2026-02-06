# Quick Start: AI Multi-Channel Integration

**Feature**: 012-ai-multi-channel
**Prerequisites**: Feature 011 (cloud deployment) completed, backend running

## 1. Install New Dependencies

```bash
cd backend
pip install python-telegram-bot slack-bolt line-bot-sdk \
  google-auth google-auth-oauthlib google-api-python-client \
  pdfplumber apscheduler slowapi
```

## 2. Configure Environment Variables

Add to `.env`:

```env
# Telegram Bot (get from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_WEBHOOK_SECRET=random-secret-string

# LINE Bot (get from LINE Developers Console)
LINE_CHANNEL_SECRET=your-secret
LINE_CHANNEL_ACCESS_TOKEN=your-token

# Slack Bot (get from Slack API portal)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret

# Gmail API (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Encryption key for storing OAuth tokens (generate with: python -c "import secrets; print(secrets.token_hex(32))")
ENCRYPTION_KEY=your-64-char-hex-key
```

## 3. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This will create the new tables:

- `channel_bindings`
- `channel_message_logs`
- `email_authorizations`
- `email_import_batches`

And add columns to `transactions`:

- `source_channel`
- `channel_message_id`

## 4. Set Up Telegram Bot

1. Message `@BotFather` on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token to `TELEGRAM_BOT_TOKEN`
4. Set webhook URL (after deployment):
   ```
   POST https://api.telegram.org/bot{TOKEN}/setWebhook
   ?url=https://your-domain.com/webhooks/telegram
   &secret_token={TELEGRAM_WEBHOOK_SECRET}
   ```

## 5. Set Up LINE Bot

1. Go to LINE Developers Console (developers.line.biz)
2. Create a new Messaging API channel
3. Copy Channel Secret → `LINE_CHANNEL_SECRET`
4. Issue Channel Access Token → `LINE_CHANNEL_ACCESS_TOKEN`
5. Set Webhook URL: `https://your-domain.com/webhooks/line`

## 6. Set Up Slack Bot

1. Go to api.slack.com/apps and create a new app
2. Enable Event Subscriptions
3. Set Request URL: `https://your-domain.com/webhooks/slack`
4. Subscribe to bot events: `message.im`, `app_mention`
5. Add Slash Commands: `/expense`
6. Install app to workspace and copy tokens

## 7. Set Up Gmail API

1. Go to Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 Client ID (Web application)
4. Add redirect URI: `https://your-domain.com/api/v1/email/authorizations/gmail/callback`
5. Copy Client ID and Secret to env vars

## 8. Bind a Channel (User Flow)

1. Log in to web UI
2. Go to Settings > Channels
3. Click "Bind Telegram" → get 6-digit code
4. Open Telegram bot → send the code
5. Done! Start bookkeeping by messaging the bot

## 9. Test Bookkeeping via Bot

Send a message to your Telegram bot:

```
午餐花了 120 元
```

Expected response:

```
已建立交易：
- 金額：$120.00
- 說明：午餐
- 分類：餐飲
- 日期：2026-02-06
```

## 10. Email Import (User Flow)

1. Go to Settings > Email
2. Click "Connect Gmail" → complete OAuth2 flow
3. System scans for credit card statement emails
4. Review parsed transactions in the preview
5. Confirm to import all transactions

#!/bin/bash
set -e

# 從 stdin 讀取 JSON 輸入
input=$(cat)

# 提取檔案路徑
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# 如果不是 TypeScript/JavaScript 檔案，直接退出
if [[ -z "$file_path" ]]; then
  exit 0
fi

case "$file_path" in
  *.ts|*.tsx|*.js|*.jsx)
    ;;
  *)
    exit 0
    ;;
esac

# 如果檔案不存在，退出
if [[ ! -f "$file_path" ]]; then
  exit 0
fi

# 取得 frontend 目錄
frontend_dir="$CLAUDE_PROJECT_DIR/frontend"

# 執行 eslint 和 prettier
if [[ -d "$frontend_dir" ]]; then
  cd "$frontend_dir"
  npx eslint --fix "$file_path" 2>&1 || true
  npx prettier --write "$file_path" 2>&1 || true
fi

exit 0

#!/bin/bash
set -e

# 從 stdin 讀取 JSON 輸入
input=$(cat)

# 提取檔案路徑
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# 如果不是 Python 檔案，直接退出
if [[ -z "$file_path" ]] || [[ "$file_path" != *.py ]]; then
  exit 0
fi

# 如果檔案不存在，退出
if [[ ! -f "$file_path" ]]; then
  exit 0
fi

# 執行 ruff
if command -v ruff &> /dev/null; then
  ruff check --fix "$file_path" 2>&1 || true
  ruff format "$file_path" 2>&1 || true
fi

exit 0

# Troubleshooting: CI Agent Auto-Fix

This document addresses common issues when implementing CI Agent Auto-Fix.

## Error: `unknown option '--allowed-commands'`

### Problem

```
error: unknown option '--allowed-commands'
Error: Process completed with exit code 1.
```

This error occurs when using the `--allowed-commands` flag with the `claude` CLI.

### Root Cause

The `--allowed-commands` flag syntax has changed between different versions of Claude Code CLI:

- **Old syntax** (pre-v1.0): `--allowed-commands="npm:*,git:*"`
- **New syntax** (v1.0+): Different tool restriction mechanism

### Solutions

#### Solution 1: Use Claude Code Action v1.0 (Recommended)

Replace your workflow step with the official GitHub Action:

```yaml
- name: Auto-Fix
  uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: |
      Fix CI errors:
      1. Run checks to see errors
      2. Apply fixes
      3. Commit changes
```

Tool restrictions are now configured differently in v1.0:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: "Fix lint errors"
    # Tool access is configured via the action's internal settings
    # No need for --allowed-commands
```

#### Solution 2: Use Tool Restrictions in Prompt

Instead of command-line flags, specify restrictions in the prompt:

```yaml
- name: Auto-Fix
  run: |
    claude -p "Fix CI errors. You may ONLY use these tools:
    - Read (to read files)
    - Edit (to edit files)
    - Bash commands: npm, git, ruff, mypy, pytest
    Do NOT use any other commands."
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### Solution 3: Use Direct SDK Integration

Create a custom script with proper tool configuration:

**`.github/scripts/auto-fix.mjs`**:

```javascript
import { Anthropic } from "@anthropic-ai/sdk";
import { spawn } from "child_process";
import fs from "fs/promises";

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// Allowed bash commands (whitelist)
const ALLOWED_COMMANDS = {
  npm: ["run", "test", "lint", "build", "install"],
  git: ["add", "commit", "status", "diff"],
  ruff: ["check", "format"],
  mypy: ["src"],
  pytest: ["--", "-v", "--tb=short"],
};

function isCommandAllowed(command) {
  const [cmd, ...args] = command.split(" ");

  if (!ALLOWED_COMMANDS[cmd]) {
    return false;
  }

  // Check if all arguments are in allowed list
  return args.every((arg) =>
    ALLOWED_COMMANDS[cmd].some((allowed) => arg.startsWith(allowed)),
  );
}

async function runCommand(command) {
  if (!isCommandAllowed(command)) {
    throw new Error(`Command not allowed: ${command}`);
  }

  return new Promise((resolve, reject) => {
    const [cmd, ...args] = command.split(" ");
    const proc = spawn(cmd, args, { shell: true });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => (stdout += data));
    proc.stderr.on("data", (data) => (stderr += data));

    proc.on("close", (code) => {
      resolve({ stdout, stderr, code });
    });

    proc.on("error", reject);
  });
}

async function main() {
  console.log("Running auto-fix...");

  // Run lint check
  const { stdout: lintOutput } = await runCommand("ruff check backend/src");

  // Create messages for Claude
  const messages = [
    {
      role: "user",
      content: `Fix these lint errors:\n\n${lintOutput}\n\nOnly fix lint issues, do not change logic.`,
    },
  ];

  // Call Claude API with tool use
  const response = await client.messages.create({
    model: "claude-sonnet-4.5-20250929",
    max_tokens: 4096,
    messages,
    tools: [
      {
        name: "read_file",
        description: "Read a file from the repository",
        input_schema: {
          type: "object",
          properties: {
            path: { type: "string" },
          },
          required: ["path"],
        },
      },
      {
        name: "edit_file",
        description: "Edit a file in the repository",
        input_schema: {
          type: "object",
          properties: {
            path: { type: "string" },
            content: { type: "string" },
          },
          required: ["path", "content"],
        },
      },
      {
        name: "run_command",
        description: "Run an allowed bash command",
        input_schema: {
          type: "object",
          properties: {
            command: { type: "string" },
          },
          required: ["command"],
        },
      },
    ],
  });

  // Process tool calls
  for (const content of response.content) {
    if (content.type === "tool_use") {
      if (content.name === "read_file") {
        const fileContent = await fs.readFile(content.input.path, "utf-8");
        console.log(`Read file: ${content.input.path}`);
      } else if (content.name === "edit_file") {
        await fs.writeFile(content.input.path, content.input.content);
        console.log(`Edited file: ${content.input.path}`);
      } else if (content.name === "run_command") {
        const result = await runCommand(content.input.command);
        console.log(`Ran command: ${content.input.command}`);
        console.log(result.stdout);
      }
    }
  }

  console.log("Auto-fix complete!");
}

main().catch(console.error);
```

**Workflow**:

```yaml
- name: Auto-Fix
  run: |
    npm install @anthropic-ai/sdk
    node .github/scripts/auto-fix.mjs
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### Solution 4: Update Claude Code CLI

If you want to continue using the CLI:

```bash
# Update to latest version
npm install -g @anthropic-ai/claude-code@latest

# Or with Homebrew
brew upgrade claude-code
```

Then check the updated syntax:

```bash
claude --help
```

### Recommended Approach

For production use, we recommend **Solution 1** (Claude Code Action v1.0) because:

✅ Official and well-maintained
✅ Built-in security features
✅ Automatic updates
✅ Better GitHub integration
✅ Simpler configuration

## Error: Agent Cannot Commit Changes

### Problem

```
error: could not commit changes
fatal: unable to auto-detect email address
```

### Solution

Add git configuration before running the agent:

```yaml
- name: Configure Git
  run: |
    git config --global user.name "claude-agent[bot]"
    git config --global user.email "claude-agent[bot]@users.noreply.github.com"

- name: Auto-Fix
  # ... your agent step
```

## Error: Permission Denied (403)

### Problem

```
error: failed to push some refs
remote: Permission to user/repo.git denied
```

### Solutions

#### Solution 1: Add Write Permissions

```yaml
jobs:
  auto-fix:
    permissions:
      contents: write # Required to push commits
      pull-requests: write # Required for PR comments
```

#### Solution 2: Use Personal Access Token

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.PAT_TOKEN }}
    fetch-depth: 0
```

Create PAT at: https://github.com/settings/tokens

- Scopes needed: `repo`, `workflow`

## Error: Workflow Timeout

### Problem

```
Error: The operation was canceled.
```

Workflow exceeds time limit (default 6 hours, but often hit earlier).

### Solutions

#### Solution 1: Add Timeout

```yaml
jobs:
  auto-fix:
    timeout-minutes: 10 # Fail after 10 minutes
```

#### Solution 2: Limit Scope in Prompt

```yaml
prompt: |
  You have 5 minutes to fix errors.
  Focus on quick, safe fixes only.
  Fix maximum 10 files.
  If complex issues, create issue report instead.
```

#### Solution 3: Split into Multiple Jobs

```yaml
jobs:
  auto-fix-backend:
    # Fix backend only
  auto-fix-frontend:
    # Fix frontend only
```

## Error: API Rate Limit Exceeded

### Problem

```
error: rate limit exceeded
status: 429
```

### Solutions

#### Solution 1: Add Retry Logic

```python
import time
from anthropic import Anthropic, RateLimitError

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

for attempt in range(3):
    try:
        response = client.messages.create(...)
        break
    except RateLimitError:
        if attempt < 2:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

#### Solution 2: Reduce Frequency

```yaml
# Only run on specific branches
on:
  push:
    branches:
      - "claude/**" # Not on every branch
```

#### Solution 3: Implement Caching

Cache responses for identical error patterns to reduce API calls.

## Error: Agent Makes Incorrect Fixes

### Problem

Agent fixes introduce new bugs or break functionality.

### Solutions

#### Solution 1: Improve Prompt Specificity

```yaml
prompt: |
  Fix ONLY lint errors. Do NOT:
  - Change logic or functionality
  - Modify test assertions
  - Rename variables or functions
  - Refactor code structure

  ONLY fix:
  - Import ordering
  - Whitespace/formatting
  - Unused imports
  - Type annotations for existing code
```

#### Solution 2: Add Verification Step

```yaml
- name: Auto-Fix
  # ... agent fixes code

- name: Verify Fixes
  run: |
    # Run all checks again
    cd backend
    ruff check .
    mypy src
    pytest

    # If any fail, revert
    if [ $? -ne 0 ]; then
      git reset --hard HEAD~1
      echo "Fixes caused new errors, reverted"
      exit 1
    fi
```

#### Solution 3: Require Human Review

```yaml
# Never auto-merge agent commits
# Always require PR approval
jobs:
  auto-fix:
    # Agent commits, but doesn't merge
```

## Error: High API Costs

### Problem

Monthly Anthropic bill higher than expected.

### Solutions

#### Solution 1: Use Smaller Model

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    model: claude-haiku-3.5 # Cheaper for simple fixes
```

**When to use each model**:

- **Haiku**: Simple lint/format fixes (~70% cheaper)
- **Sonnet**: Type errors, test analysis
- **Opus**: Complex refactoring (if needed)

#### Solution 2: Implement Prompt Caching

```python
# Cache system prompt to reduce input tokens
system_prompt = """You are a code fixer..."""  # Long prompt

response = client.messages.create(
    model="claude-sonnet-4.5-20250929",
    system=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}  # Cache this
    }],
    messages=[...]
)
```

Saves 90% on cached tokens!

#### Solution 3: Reduce Context Size

```yaml
prompt: |
  Fix errors in these specific files only:
  - backend/src/api/main.py
  - backend/src/core/config.py

  Do not analyze other files.
```

#### Solution 4: Set Budget Alerts

In Anthropic Console:

1. Go to Settings → Billing
2. Set monthly budget limit
3. Enable email alerts at 50%, 80%, 100%

## Error: Cannot Find Files to Fix

### Problem

```
error: file not found
```

### Solution

Ensure working directory is correct:

```yaml
- name: Auto-Fix Backend
  working-directory: ./backend
  run: |
    # Now in backend/ directory
    ruff check .
```

Or use absolute paths:

```yaml
prompt: |
  Fix files in: /home/runner/work/repo/repo/backend/src/
```

## Need More Help?

1. **Check workflow logs**: Click on failed job in GitHub Actions
2. **Enable debug logging**:
   ```yaml
   env:
     ACTIONS_STEP_DEBUG: true
   ```
3. **Test locally**: Run commands on your machine first
4. **Check API status**: https://status.anthropic.com
5. **Ask in discussions**: GitHub repository discussions

## Common Command Reference

### Verify API Key

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4.5-20250929","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### Test Claude Code CLI

```bash
echo "print('hello')" > test.py
claude -p "Fix lint errors in test.py"
```

### Check Git Configuration

```bash
git config user.name
git config user.email
```

### View Workflow Permissions

```yaml
# In your workflow file
jobs:
  auto-fix:
    permissions:
      contents: write
      pull-requests: write
      # Add more as needed
```

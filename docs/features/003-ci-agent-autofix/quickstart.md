# Quick Start: CI Agent Auto-Fix

This guide will help you quickly set up CI Agent Auto-Fix in your repository.

## Prerequisites

- Repository admin access
- Anthropic API key ([get one here](https://console.anthropic.com/))
- GitHub Actions enabled

## 5-Minute Setup

### Step 1: Add API Key to GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key
6. Click **Add secret**

### Step 2: Update CI Workflow

Add the auto-fix job to `.github/workflows/ci.yml`:

```yaml
jobs:
  # ... existing check job ...

  # Add this new job
  auto-fix-lint:
    name: Auto-Fix Lint Errors
    needs: backend-quality
    if: failure()
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Configure Git
        run: |
          git config user.name "claude-agent[bot]"
          git config user.email "claude-agent[bot]@users.noreply.github.com"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run Claude Agent Auto-Fix
        run: |
          pip install anthropic
          python .github/scripts/auto-fix-lint.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Step 3: Create Auto-Fix Script

Create `.github/scripts/auto-fix-lint.py`:

```python
#!/usr/bin/env python3
"""Auto-fix lint errors using Claude Agent SDK."""

import os
import subprocess
import sys
from anthropic import Anthropic

def run_command(cmd: str) -> tuple[str, int]:
    """Run a shell command and return output and exit code."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr, result.returncode

def main():
    # Initialize Anthropic client
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Run lint check to get errors
    print("Running lint check...")
    lint_output, lint_code = run_command("cd backend && ruff check . --output-format=text")

    if lint_code == 0:
        print("No lint errors found!")
        sys.exit(0)

    print(f"Found lint errors:\n{lint_output}\n")

    # Get list of Python files
    files_output, _ = run_command("find backend/src -name '*.py' -type f")
    py_files = files_output.strip().split('\n')

    # Read file contents
    file_contents = {}
    for file_path in py_files[:20]:  # Limit to 20 files to avoid token limits
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                file_contents[file_path] = f.read()

    # Create prompt for Claude
    prompt = f"""You are a helpful coding assistant. Fix the following lint errors:

Lint errors:
```

{lint_output}

````

For each file with errors, I'll provide the current content. Please provide the corrected version.

Files to fix:
{chr(10).join(f"- {path}" for path in file_contents.keys())}

For each file that needs changes, respond in this format:
FILE: path/to/file.py
```python
# corrected file content
````

Only include files that need changes. Be conservative - only fix the specific lint errors mentioned.
"""

    # Add file contents to prompt
    for path, content in file_contents.items():
        prompt += f"\n\nCurrent content of {path}:\n```python\n{content}\n```"

    print("Asking Claude to fix errors...")

    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4.5-20250929",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    response = message.content[0].text
    print(f"Claude's response:\n{response}\n")

    # Parse response and apply fixes
    import re

    # Find all FILE: blocks
    file_pattern = r'FILE:\s*(.+?)\n```python\n(.+?)\n```'
    matches = re.finditer(file_pattern, response, re.DOTALL)

    fixed_files = []
    for match in matches:
        file_path = match.group(1).strip()
        new_content = match.group(2)

        print(f"Applying fix to {file_path}...")

        with open(file_path, 'w') as f:
            f.write(new_content)

        fixed_files.append(file_path)

    if not fixed_files:
        print("No fixes applied. Claude may not have found fixable issues.")
        sys.exit(1)

    # Verify fixes
    print("\nVerifying fixes...")
    lint_output_after, lint_code_after = run_command("cd backend && ruff check .")

    if lint_code_after == 0:
        print("✓ All lint errors fixed!")
    else:
        print(f"Some errors remain:\n{lint_output_after}")

    # Commit changes
    print("\nCommitting fixes...")
    run_command("git add .")

    commit_msg = f"""fix: auto-fix lint errors [claude-agent]

Fixed lint errors in:
{chr(10).join(f'- {f}' for f in fixed_files)}

Auto-applied by Claude Agent SDK
"""

    run_command(f'git commit -m "{commit_msg}"')

    # Push changes
    branch = os.environ.get('GITHUB_HEAD_REF') or os.environ.get('GITHUB_REF_NAME')
    if branch:
        print(f"Pushing to {branch}...")
        run_command(f"git push origin HEAD:{branch}")

    print("Done!")

if **name** == "**main**":
main()

````

### Step 4: Make Script Executable

```bash
chmod +x .github/scripts/auto-fix-lint.py
````

### Step 5: Test It!

1. Create a test branch with intentional lint errors:

   ```python
   # backend/src/test_file.py
   def foo(  ):  # Extra spaces
       x=1   # Missing spaces around =
       print( "hello")  # Inconsistent spacing
       return x
   ```

2. Commit and push:

   ```bash
   git add backend/src/test_file.py
   git commit -m "test: add file with lint errors"
   git push
   ```

3. Watch GitHub Actions:
   - `backend-quality` job will fail
   - `auto-fix-lint` job will trigger
   - Agent will fix errors and commit

4. Pull the changes:
   ```bash
   git pull
   ```

## Using Claude Code Action (Alternative Method)

Instead of the Python script, you can use the official Claude Code Action:

### Step 1: Install GitHub App

Run in your terminal:

```bash
claude
/install-github-app
```

Follow the prompts to install the Claude Code GitHub App.

### Step 2: Update Workflow

Replace the auto-fix job with:

```yaml
auto-fix-lint:
  name: Auto-Fix Lint Errors
  needs: backend-quality
  if: failure()
  runs-on: ubuntu-latest
  permissions:
    contents: write
    pull-requests: write
  steps:
    - uses: actions/checkout@v4

    - name: Auto-Fix with Claude
      uses: anthropics/claude-code-action@v1
      with:
        anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
        prompt: |
          Fix the lint errors in the backend code:
          1. Run `cd backend && ruff check .` to see errors
          2. Install dependencies: `cd backend && pip install -e ".[dev]"`
          3. Apply auto-fixes: `ruff check --fix .`
          4. For remaining errors, manually fix them
          5. Commit changes with message "fix: auto-fix lint errors [claude-agent]"
        auto_commit: true
```

## Next Steps

- **Add Type Error Fixes**: Extend to fix mypy errors
- **Add Test Analysis**: Analyze test failures
- **Add Frontend Fixes**: Fix ESLint and TypeScript errors
- **Monitor Costs**: Check Anthropic API usage in console

## Troubleshooting

### Agent Not Triggering

Check:

- Is `backend-quality` job actually failing?
- Is `if: failure()` condition correct?
- Are permissions correct (`contents: write`)?

### Agent Cannot Commit

Fix:

- Add git config in workflow
- Use PAT token instead of GITHUB_TOKEN:
  ```yaml
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.PAT_TOKEN }}
  ```

### Agent Fixes Don't Work

Debug:

- Check Claude's response in workflow logs
- Ensure file paths are correct
- Verify lint errors are fixable (not logic errors)

## Cost Estimate

- **Per run**: ~$0.05-0.10
- **Monthly** (20 PRs): ~$2-4

Very cost-effective compared to developer time!

## Learn More

- Full specification: [`spec.md`](./spec.md)
- Research and analysis: [`research.md`](./research.md)
- [Claude Code Action docs](https://github.com/anthropics/claude-code-action)

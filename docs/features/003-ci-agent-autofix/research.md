# Research: CI Agent Auto-Fix Implementation

**Date**: 2026-01-08
**Feature**: 003-ci-agent-autofix

## Reference Implementation Analysis

### cc-demo Repository

**Source**: https://github.com/hiimoliverwang/cc-demo

#### Key Findings

1. **Workflow Structure**:
   - Three sequential jobs: Check → Auto-Fix (on failure) → Smoke Tests
   - Auto-fix only triggers when check job fails
   - Uses `if: failure()` condition for conditional execution

2. **Claude Agent Integration Methods**:

   **Method 1: Claude Code CLI (cc-demo approach)**

   ```yaml
   - name: Auto-fix
     if: failure()
     run: |
       claude -p "Fix the CI failures:
       1. Run npm run lint and npm run build
       2. Analyze errors
       3. Fix issues
       4. Commit with message 'fix: auto-fix lint and type errors'"
     env:
       ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
   ```

   **Method 2: Claude Code Action (Official GitHub Action)**

   ```yaml
   - name: Auto-fix
     uses: anthropics/claude-code-action@v1
     with:
       anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
       prompt: "Fix the CI failures..."
   ```

   **Method 3: Direct SDK Integration**
   - Use Node.js script with `@anthropic-ai/sdk` + Agent SDK
   - More control but more complex setup

3. **Skills Directory Structure**:

   ```
   .claude/skills/
   ├── add-lint-error.md       # Demo: intentionally add lint errors
   ├── break-smoke-test.md     # Demo: break smoke tests
   ├── cleanup-worktree.md     # Git worktree cleanup
   ├── load-context.md         # Context management
   ├── new-worktree.md         # Git worktree creation
   └── save-context.md         # Context persistence
   ```

4. **Tool Access Control**:
   - In cc-demo, limited to: Read, Edit, Bash(npm:_), Bash(git:_)
   - Prevents destructive operations
   - Allows necessary build/lint/test commands

## Claude Code Action v1.0 Analysis

**Source**: https://github.com/anthropics/claude-code-action

### Key Features

1. **Intelligent Activation**:
   - Responds to @claude mentions in PRs/issues
   - Responds to workflow triggers
   - Responds to explicit prompts

2. **Multiple Input Methods**:

   ```yaml
   # Method 1: Direct prompt
   with:
     prompt: "Fix lint errors"

   # Method 2: From issue/PR body
   with:
     use_pr_description: true

   # Method 3: From trigger event
   # (automatic based on @claude mention)
   ```

3. **Advanced Configuration**:

   ```yaml
   with:
     anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
     model: claude-sonnet-4.5-20250929
     max_tokens: 4096
     temperature: 0.7

     # Tool configuration
     allowed_tools: |
       Read
       Edit
       Bash(npm:*)
       Bash(git:*)

     # Auto-commit
     auto_commit: true
     commit_message_prefix: "fix(auto): "

     # Output
     create_pr_comment: true
     outputs:
       result: steps.claude.outputs.result
   ```

4. **Security Features**:
   - Least privilege tool access
   - Secrets masking
   - Audit logging
   - No auto-merge capability

### Example Workflows

#### Auto-fix Lint Errors

```yaml
name: Auto-fix Lint Errors

on:
  pull_request:
    branches: [main]

jobs:
  lint-check:
    runs-on: ubuntu-latest
    outputs:
      failed: ${{ steps.lint.outcome == 'failure' }}
    steps:
      - uses: actions/checkout@v4
      - name: Run Lint
        id: lint
        run: npm run lint
        continue-on-error: true

  auto-fix:
    needs: lint-check
    if: needs.lint-check.outputs.failed == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Fix Lint Errors
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Fix the linting errors in this repository:
            1. Run `npm run lint` to see errors
            2. Fix all auto-fixable issues
            3. Commit changes with clear message
          auto_commit: true
```

#### Security Review on PR

```yaml
name: Security Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  security-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Security Review
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Review this PR for security issues:
            1. Check for SQL injection vulnerabilities
            2. Check for XSS vulnerabilities
            3. Check for authentication/authorization issues
            4. Check for sensitive data exposure
            5. Provide detailed report as PR comment
          create_pr_comment: true
```

## Troubleshooting Common Issues

### Issue: `error: unknown option '--allowed-commands'`

**Root Cause**: The `--allowed-commands` flag was used in older versions of the Claude Code CLI but has been deprecated or changed in newer versions.

**Solutions**:

1. **Use Claude Code Action v1.0** (Recommended):

   ```yaml
   - uses: anthropics/claude-code-action@v1
     with:
       allowed_tools: |
         Read
         Edit
         Bash(npm:*)
   ```

2. **Use Tool Restriction in Prompt**:

   ```yaml
   - run: |
       claude -p "Fix CI errors. You may only use: Read, Edit, and bash commands for npm and git."
   ```

3. **Use Direct SDK Integration**:

   ```typescript
   import { Agent } from "@anthropic-ai/sdk-agent";

   const agent = new Agent({
     tools: {
       allowedTools: ["Read", "Edit"],
       allowedCommands: ["npm:*", "git:*"],
     },
   });
   ```

4. **Update Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   # or
   brew upgrade claude-code
   ```

### Issue: Agent Cannot Commit Changes

**Solutions**:

- Ensure workflow has `contents: write` permission
- Configure git user:
  ```yaml
  - run: |
      git config user.name "claude-agent[bot]"
      git config user.email "bot@example.com"
  ```
- Use personal access token (PAT) for checkout:
  ```yaml
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.PAT_TOKEN }}
  ```

### Issue: Workflow Timeout

**Solutions**:

- Add timeout to job:
  ```yaml
  jobs:
    auto-fix:
      timeout-minutes: 10
  ```
- Add execution time limit in prompt:
  ```yaml
  prompt: |
    You have 5 minutes to fix CI errors.
    Focus on quick, safe fixes only.
  ```

## Technology Comparison

### Option 1: Claude Code Action (Recommended)

**Pros**:

- Official Anthropic solution
- Well-documented and maintained
- Easy setup with `/install-github-app`
- Built-in safety features
- PR comment integration

**Cons**:

- Less customization than direct SDK
- Requires GitHub App installation
- Tied to GitHub Actions

**Best For**: Most projects, standard CI workflows

### Option 2: Direct SDK Integration

**Pros**:

- Full control over agent behavior
- Can use in non-GitHub environments
- More customization options
- Better error handling

**Cons**:

- More complex setup
- Need to handle auth, commits, etc.
- More maintenance burden

**Best For**: Custom workflows, advanced use cases

### Option 3: Claude Code CLI Headless Mode

**Pros**:

- Simple integration
- Works with existing CLI tools
- Good for local testing

**Cons**:

- Less control than SDK
- Command syntax changes between versions
- Limited workflow integration

**Best For**: Quick prototypes, local development

## Cost Analysis

### API Usage Patterns

**Lint Auto-Fix (Typical)**:

- Input: ~3,000 tokens (file contents + lint output)
- Output: ~1,500 tokens (fixes + commit message)
- Cost per run: ~$0.05 (Claude Sonnet 4.5)

**Type Error Fix (Typical)**:

- Input: ~5,000 tokens (more context needed)
- Output: ~2,000 tokens (type annotations + fixes)
- Cost per run: ~$0.10

**Test Failure Analysis (Complex)**:

- Input: ~8,000 tokens (test files + outputs)
- Output: ~3,000 tokens (detailed analysis)
- Cost per run: ~$0.18

### Monthly Estimates

**Small Project (10 PRs/month)**:

- ~20 auto-fix runs
- ~$2-3/month

**Medium Project (50 PRs/month)**:

- ~100 auto-fix runs
- ~$8-12/month

**Large Project (200 PRs/month)**:

- ~400 auto-fix runs
- ~$30-50/month

### Cost Optimization Strategies

1. **Use Haiku for Simple Fixes**:
   - Lint errors: Claude Haiku (~70% cheaper)
   - Type errors: Claude Sonnet
   - Complex analysis: Claude Sonnet

2. **Implement Caching**:
   - Cache similar error patterns
   - Reuse fixes for common issues
   - Use prompt caching for large contexts

3. **Batch Operations**:
   - Fix multiple files in single run
   - Analyze all test failures together
   - Reduce API calls

4. **Smart Triggering**:
   - Only auto-fix on `claude/**` branches
   - Skip auto-fix for draft PRs
   - Rate limit per PR (1 auto-fix attempt max)

## Integration with Existing CI

### Current CI Pipeline

```
Pre-commit → Backend Quality → Backend Tests → Frontend Quality → Security
```

### Enhanced Pipeline with Agent

```
Pre-commit → Backend Quality → [Auto-Fix] → Re-check → Backend Tests → [Test Analysis] → Frontend Quality → [Auto-Fix] → Re-check → Security
```

### Workflow Dependencies

```yaml
jobs:
  check:
    # runs: ruff, mypy, eslint

  auto-fix:
    needs: check
    if: failure()
    # fixes lint/type errors

  recheck:
    needs: auto-fix
    # re-runs checks to verify fixes

  tests:
    needs: [check, recheck]
    if: success()
    # runs pytest, jest

  test-analysis:
    needs: tests
    if: failure()
    # analyzes test failures
```

## Security Considerations

### Threat Model

| Threat                   | Risk Level | Mitigation                                  |
| ------------------------ | ---------- | ------------------------------------------- |
| Malicious code injection | High       | Code review required, no auto-merge         |
| Secret exposure          | High       | Pre-commit secret scanning, secrets masking |
| Privilege escalation     | Medium     | Limited bash commands, no sudo              |
| Denial of service        | Low        | Timeout limits, rate limiting               |
| API key theft            | High       | Store as GitHub secret, rotate quarterly    |

### Best Practices

1. **Least Privilege**:
   - Only allow necessary tools
   - Restrict bash commands to specific patterns
   - No destructive file operations

2. **Audit Trail**:
   - Log all agent actions
   - Track commits with bot account
   - Monitor API usage

3. **Human Oversight**:
   - Require code review before merge
   - Agent cannot approve PRs
   - Clear labeling of agent commits

4. **Secrets Management**:
   - Use GitHub Secrets for API keys
   - Rotate keys quarterly
   - Monitor for unusual API usage

## Next Steps

1. **Prototype** (Week 1):
   - Set up Claude Code Action in test repository
   - Create simple lint auto-fix workflow
   - Test with intentional lint errors

2. **Pilot** (Week 2-3):
   - Deploy to `claude/**` branches only
   - Monitor success rate and costs
   - Gather developer feedback

3. **Rollout** (Week 4):
   - Extend to all branches
   - Add type error fixes
   - Add test failure analysis

4. **Optimize** (Ongoing):
   - Fine-tune prompts based on results
   - Reduce costs with caching
   - Improve success rates

## References

- [cc-demo Repository](https://github.com/hiimoliverwang/cc-demo)
- [Claude Code Action](https://github.com/anthropics/claude-code-action)
- [Claude Code Action v1.0 Release](https://github.com/anthropics/claude-code-action/releases/tag/v1.0.0)
- [Claude Code GitHub Actions Docs](https://code.claude.com/docs/en/github-actions)
- [Automate Security Reviews](https://www.anthropic.com/news/automate-security-reviews-with-claude-code)
- [CI/CD Integration Guide](https://skywork.ai/blog/how-to-integrate-claude-code-ci-cd-guide-2025/)

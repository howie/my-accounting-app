# Feature 003: CI Agent Auto-Fix

**Status**: Draft
**Created**: 2026-01-08
**Reference**: [cc-demo repository](https://github.com/hiimoliverwang/cc-demo)

## Overview

Integrate Claude Agent SDK into the GitHub Actions CI pipeline to automatically detect, diagnose, and fix common CI failures including linting errors, type checking issues, and test failures.

## Quick Links

- **[📋 Specification](./spec.md)** - Full feature specification with user stories, architecture, and implementation plan
- **[🚀 Quick Start](./quickstart.md)** - Get started in 5 minutes with step-by-step setup
- **[🔬 Research](./research.md)** - Technical research, cost analysis, and reference implementations
- **[🔧 Troubleshooting](./TROUBLESHOOTING.md)** - Solutions to common issues including the `--allowed-commands` error

## What This Feature Does

### Automated Fixes

1. **Lint Errors** - Automatically fix ruff/eslint formatting and style issues
2. **Type Errors** - Add missing type annotations and fix type incompatibilities
3. **Test Failures** - Analyze test failures and fix simple issues

### How It Works

```
Developer pushes code
    ↓
CI runs quality checks
    ↓
Checks fail? → Claude Agent analyzes errors
    ↓
Agent applies fixes automatically
    ↓
Agent commits changes
    ↓
CI re-runs and passes ✓
```

## Key Benefits

✅ **Reduces manual intervention** - Auto-fix common CI errors
✅ **Faster feedback loops** - Issues fixed within minutes
✅ **Consistent code style** - AI applies fixes uniformly
✅ **Developer productivity** - Focus on logic, not formatting
✅ **Cost effective** - ~$0.05 per auto-fix run

## Getting Started

### Prerequisites

- Repository admin access
- Anthropic API key
- GitHub Actions enabled

### 5-Minute Setup

See **[Quick Start Guide](./quickstart.md)** for detailed instructions.

**Summary**:

1. Add `ANTHROPIC_API_KEY` to GitHub Secrets
2. Update `.github/workflows/ci.yml` with auto-fix job
3. Push code with lint errors to test
4. Watch agent automatically fix and commit

### Example Auto-Fix Job

```yaml
auto-fix-lint:
  name: Auto-Fix Lint Errors
  needs: backend-quality
  if: failure()
  runs-on: ubuntu-latest
  permissions:
    contents: write
  steps:
    - uses: actions/checkout@v4

    - name: Auto-Fix with Claude
      uses: anthropics/claude-code-action@v1
      with:
        anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
        prompt: |
          Fix the lint errors:
          1. Run lint check to see errors
          2. Apply auto-fixes
          3. Fix remaining issues manually
          4. Commit changes
        auto_commit: true
```

## Documentation Structure

### Core Documents

| Document             | Purpose                                                                  |
| -------------------- | ------------------------------------------------------------------------ |
| `spec.md`            | Complete feature specification with user stories, architecture, security |
| `quickstart.md`      | Step-by-step setup guide with code examples                              |
| `research.md`        | Technical research, cost analysis, comparison of approaches              |
| `TROUBLESHOOTING.md` | Solutions to common issues and errors                                    |

### Supporting Directories

| Directory     | Purpose                                      |
| ------------- | -------------------------------------------- |
| `contracts/`  | API contracts and integration specs (future) |
| `checklists/` | Quality validation checklists (future)       |
| `issues/`     | Feature-specific issue tracking (future)     |

## Implementation Status

### Phase 1: Basic Lint Auto-Fix (Planned)

- [ ] Set up Claude Agent SDK in GitHub Actions
- [ ] Create auto-fix workflow for backend lint errors
- [ ] Create auto-fix workflow for frontend lint errors
- [ ] Test on sample PRs

### Phase 2: Type Checking (Planned)

- [ ] Extend workflow to handle mypy errors
- [ ] Extend workflow to handle TypeScript errors
- [ ] Test on various type error scenarios

### Phase 3: Test Analysis (Planned)

- [ ] Create test failure analysis workflow
- [ ] Implement simple test fix automation
- [ ] Implement complex issue reporting

### Phase 4: Integration (Planned)

- [ ] Integrate all workflows into unified CI
- [ ] Add monitoring and cost tracking
- [ ] Document best practices

## Common Issues

### ❌ Error: `unknown option '--allowed-commands'`

**Solution**: Use Claude Code Action v1.0 instead of CLI flags.

See **[TROUBLESHOOTING.md#error-unknown-option-allowed-commands](./TROUBLESHOOTING.md#error-unknown-option---allowed-commands)** for detailed solutions.

### ❌ Agent Cannot Commit Changes

**Solution**: Add git configuration and ensure `contents: write` permission.

### ❌ High API Costs

**Solution**: Use Claude Haiku for simple fixes, implement caching, limit scope.

See **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** for more issues and solutions.

## Cost Estimates

### Per Auto-Fix Run

- **Lint fixes**: ~$0.05 (Haiku) to $0.08 (Sonnet)
- **Type fixes**: ~$0.10 (Sonnet)
- **Test analysis**: ~$0.15-0.20 (Sonnet)

### Monthly (50 PRs)

- **Total**: ~$8-12/month
- **ROI**: 10-20 hours saved @ $50/hr = $500-1000 value
- **Net benefit**: ~$490-990/month

## Security

✅ **Least privilege** - Agent restricted to specific tools
✅ **Code review required** - Human approval before merge
✅ **Audit trail** - All agent actions logged
✅ **Secrets protected** - API key in GitHub Secrets
✅ **No auto-merge** - Agent cannot approve PRs

See **[spec.md#security-considerations](./spec.md#security-considerations)** for details.

## References

### Implementation Examples

- [cc-demo Repository](https://github.com/hiimoliverwang/cc-demo) - Reference implementation showing auto-fix workflow
- [Claude Code Action](https://github.com/anthropics/claude-code-action) - Official GitHub Action

### Documentation

- [Claude Code GitHub Actions Docs](https://code.claude.com/docs/en/github-actions)
- [Automate Security Reviews](https://www.anthropic.com/news/automate-security-reviews-with-claude-code)
- [CI/CD Integration Guide](https://skywork.ai/blog/how-to-integrate-claude-code-ci-cd-guide-2025/)

### Research Articles

- [How to Use Claude Code with GitHub Actions](https://apidog.com/blog/claude-code-github-actions/)
- [How to Integrate Claude Code SDK into CI/CD](https://skywork.ai/blog/how-to-integrate-claude-code-sdk-into-ci-cd-pipelines/)
- [Claude Code for PRs and Reviews](https://skywork.ai/blog/how-to-use-claude-code-for-prs-code-reviews-guide/)

## Contributing

This feature is in **Draft** status. Contributions welcome:

1. **Report issues**: Add to `issues/` directory
2. **Suggest improvements**: Update spec.md
3. **Share learnings**: Update research.md
4. **Fix docs**: Improve clarity

## Questions?

- Review **[spec.md](./spec.md)** for comprehensive details
- Check **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** for common issues
- See **[quickstart.md](./quickstart.md)** for setup help

---

**Next Steps**: Follow the [Quick Start Guide](./quickstart.md) to begin implementation.

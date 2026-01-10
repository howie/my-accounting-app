# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based accounting application. The repository is currently in initial setup phase with no code structure implemented yet.

## Feature Development Structure

This project uses the Spec-Driven Development workflow. Feature specifications and documentation are organized as follows:

### Feature Documentation Location

All feature specifications are stored in `/docs/features/`:

```text
docs/features/
├── 001-core-accounting/
│   ├── spec.md          # Feature specification with user stories
│   ├── plan.md          # Implementation plan
│   ├── tasks.md         # Task breakdown
│   ├── research.md      # Technical research
│   ├── data-model.md    # Data models
│   ├── quickstart.md    # Quick start guide
│   ├── contracts/       # API contracts
│   ├── checklists/      # Quality validation checklists
│   └── issues/          # Feature-specific issue tracking
├── 002-feature-name/
│   └── ...
```

### Issue Tracking

Each feature has its own `issues/` subdirectory for tracking bugs, enhancements, and questions specific to that feature:

- **Bugs discovered during development**: `docs/features/###-feature-name/issues/bug-<description>.md`
- **Feature enhancements**: `docs/features/###-feature-name/issues/enhancement-<description>.md`
- **Technical questions**: `docs/features/###-feature-name/issues/question-<description>.md`

When documenting issues:

- Use descriptive filenames (e.g., `bug-balance-calculation-rounding.md`)
- Include reproduction steps for bugs
- Link to relevant code sections when applicable
- Reference the constitution principles if related to data integrity or testing

### Working with Features

Use the speckit slash commands to manage features:

- Create new feature spec: `/speckit.specify "feature description"`
- Create implementation plan: `/speckit.plan`
- Generate task breakdown: `/speckit.tasks`
- Ask clarifying questions: `/speckit.clarify`

All feature files are automatically created in the correct `docs/features/###-feature-name/` structure.

## Development Environment

This is a Python project. Based on the .gitignore configuration, the project may use Abstra (an AI-powered process automation framework) for workflow automation.

### Environment Setup

Standard Python virtual environment practices apply:

- Virtual environments should be created in `.venv/` or `venv/` directories
- Environment variables and secrets should be stored in `.env` files (gitignored)

## Notes

- The `.abstra/` directory contains Abstra-related user credentials, local state, and settings (gitignored)
- Standard Python build artifacts, test coverage reports, and cache directories are gitignored

## Active Technologies

- Python 3.12 (Backend), TypeScript 5.x (Frontend) + FastAPI, SQLModel, Next.js 15, React 19, TanStack Query (006-data-import)
- PostgreSQL 16 (existing schema from 001-core-accounting) (006-data-import)

- Python 3.12 (Backend), TypeScript 5.x (Frontend) (001-core-accounting)
- PostgreSQL 16 (via Docker or Supabase) (001-core-accounting)
- PostgreSQL 16 (existing data model from 001-core-accounting) (002-ui-layout-dashboard)
- PostgreSQL 16 (accounts, transactions), Browser localStorage (user preferences) (003-settings-account-management)

## Recent Changes

- 001-core-accounting: Added Python 3.12 (Backend), TypeScript 5.x (Frontend)

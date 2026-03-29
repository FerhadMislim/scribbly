# Contributing to Scribbly ✏️

Thanks for helping build Scribbly! Please read this guide before opening a PR.

---

## Branching Strategy

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `chore/` | Tooling, deps, config |
| `ai/` | Model pipeline changes |
| `infra/` | Docker, CI, deployment |
| `docs/` | Documentation only |

Example: `feat/style-selector-component`, `fix/upload-file-size-validation`

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add AnimateDiff animation pipeline
fix: handle upload timeout gracefully
chore: update Python dependencies
ai: add storybook LoRA training config
infra: add Fly.io deployment workflow
docs: update README with iOS setup steps
```

---

## Pull Request Process

1. Branch off `main`
2. Write your code + tests
3. Run linting: `make lint`
4. Run tests: `make test`
5. Open PR with the template filled out
6. Get at least **1 approval** from a reviewer
7. CI must pass before merge
8. Squash merge into `main`

---

## Code Style

| Platform | Tool | Config |
|----------|------|--------|
| Python | Ruff (lint + format) | `pyproject.toml` |
| TypeScript | ESLint + Prettier | `.eslintrc` / `.prettierrc` |
| Swift | SwiftLint | `.swiftlint.yml` |

Pre-commit hooks run automatically — install with:
```bash
pip install pre-commit && pre-commit install
```

---

## Environment Setup

Copy `.env.example` to `.env` and fill in values — never commit `.env`.

Required variables:
```
DATABASE_URL=postgresql+asyncpg://artuser:artpass@localhost/artapp
REDIS_URL=redis://localhost:6379
S3_BUCKET=scribbly-dev
S3_ENDPOINT=http://localhost:9000
S3_KEY=minioadmin
S3_SECRET=minioadmin
JWT_SECRET=change-me-in-production
MODEL_PATH=./ai-engine/models
```

---

*Scribbly — Where pencil meets magic. ✏️*

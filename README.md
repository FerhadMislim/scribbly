# ✏️ Scribbly
### *Where pencil meets magic.*

Scribbly is a multi-platform AI-powered creative tool that transforms children's drawings into beautiful, stylized digital artwork and short animations. Parents and children upload a sketch and instantly see it reimagined in styles like Pixar 3D, anime, storybook, or soft illustration — all powered by state-of-the-art diffusion models.

---

## 🌟 What Scribbly Does

- 📸 **Upload** any hand-drawn sketch — pencil, crayon, marker
- 🎨 **Choose a style** — Pixar 3D, Anime, Storybook, Soft Illustration, Colored Sketch
- ✨ **Watch the magic** — AI transforms the drawing in seconds
- 🎞️ **Animate it** — generate a short looping animation from any drawing
- 📱 **Anywhere** — available on Web and iOS

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 · FastAPI · Celery · PostgreSQL · Redis |
| AI Pipeline | Stable Diffusion XL · ControlNet (Scribble/Canny) · LoRA · AnimateDiff |
| Web App | React 18 · TypeScript · Vite · TailwindCSS |
| iOS App | Swift 5.9 · SwiftUI · iOS 17+ |
| Storage | MinIO (local) · AWS S3 (production) |
| Infrastructure | Docker · GitHub Actions · Fly.io · Vercel |

---

## 🗂️ Repository Structure

```
scribbly/
├── backend/          # FastAPI application & Celery workers
├── web/              # React + TypeScript web app
├── ios/              # Swift + SwiftUI iOS app (Xcode project)
├── ai-engine/        # Inference pipeline, model configs, LoRA training
├── infra/            # Docker, docker-compose, deployment configs
├── docs/             # Architecture diagrams, API specs, ADRs
└── scripts/          # Dev utilities, model download scripts
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Xcode 15+ (for iOS)
- Docker + Docker Compose
- NVIDIA GPU with 8GB+ VRAM (optional for local inference)

### Quick Start (Local Dev)

```bash
# 1. Clone the repo
git clone https://github.com/FerhadMislim/scribbly.git
cd scribbly

# 2. Start all services (API + DB + Redis + MinIO)
docker-compose up -d

# 3. Start the backend
cd backend && make dev

# 4. Start the web app
cd web && npm install && npm run dev
```

Visit `http://localhost:3000` — Scribbly is running! 🎉

### Download AI Models

```bash
bash ai-engine/scripts/download_models.sh
```

This downloads SDXL, SD1.5, and the ControlNet Scribble model (~10GB total).

---

## 🎨 Art Styles

| Style ID | Name | Best For |
|----------|------|----------|
| `pixar_3d` | Pixar 3D | Characters, animals |
| `anime` | Anime | People, fantasy scenes |
| `storybook` | Storybook | Landscapes, stories |
| `soft_illustration` | Soft Illustration | Abstract, colorful art |
| `sketch_colored` | Colored Sketch | Retaining the original feel |

---

## 📅 Project Timeline

| Week | Milestone |
|------|-----------|
| 1 | Project setup, architecture, Docker, dev environments |
| 2 | AI inference pipeline, ControlNet, preprocessing |
| 3 | LoRA fine-tuning, AnimateDiff animation pipeline |
| 4 | FastAPI backend — all endpoints, auth, storage |
| 5 | React web app — upload, styles, gallery |
| 6 | iOS SwiftUI app — upload, generation, gallery |
| 7 | Cloud deployment, GPU server, TestFlight |
| 8 | QA, testing, documentation, v1 launch 🚀 |

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend && pytest --cov=app --cov-report=term-missing

# Web tests
cd web && npm test

# E2E tests (requires staging environment)
cd web && npx playwright test
```

---

## 🤝 Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before submitting a PR.

- Branch naming: `feat/`, `fix/`, `chore/`, `ai/`, `infra/`
- Commit format: Conventional Commits (`feat: add style selector`)
- All PRs require 1 reviewer + CI passing

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

## 💛 Built with love for curious kids and creative families.

*Scribbly — Where pencil meets magic.*

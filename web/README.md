# Web

React + TypeScript web application for Scribbly.

## Getting Started

### Prerequisites

- Node.js 20+

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000/api/v1
```

## Project Structure

```
web/
├── src/
│   ├── api/           # API client modules
│   ├── components/    # Reusable React components
│   ├── pages/        # Page components
│   ├── hooks/        # Custom React hooks
│   ├── utils/        # Utility functions
│   ├── types/         # TypeScript type definitions
│   └── App.tsx       # Main application component
├── public/           # Static assets
├── index.html
├── vite.config.ts
└── package.json
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm test` | Run tests |

## Testing

```bash
npm test
npm run test:coverage
```

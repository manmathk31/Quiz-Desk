# Quizdesk Frontend Client

React Single-Page Application (SPA) for the Quizdesk institutional assessment platform.

---

## Technology Stack

- **Framework**: React 19 + TypeScript
- **Bundler & Dev Server**: Vite 8
- **Styling**: Tailwind CSS v4 (`@tailwindcss/vite`)
- **Routing**: React Router v7
- **Iconography**: Lucide React

---

## Setup & Execution (Windows PowerShell)

All commands should be executed from the `frontend/` directory:

### 1. Install Dependencies
```powershell
npm install
```

### 2. Start Development Server
```powershell
npm run dev
```
- Local URL: `http://localhost:5173`

### 3. Build Production Bundle
```powershell
npm run build
```
- Output Directory: `dist/` (type-checked via `tsc -b` and compiled via Vite)

### 4. Preview Production Build
```powershell
npm run preview
```

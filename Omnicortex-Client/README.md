# Omnicortex AI — Frontend

A **React + Vite** based SaaS dashboard that provides multiple AI-powered workflows in a unified platform, including resume generation, AI image generation, and medical image analysis.

---

## Features

- **Resume Generation** — AI-powered resume builder with PDF preview and download
- **AI Image Generation** — Generate images via AI with download support
- **Medical Image Analysis** — Analyze medical images through a dedicated workflow
- **Authentication & Authorization** — Secure JWT-based login and registration
- **Protected Routes** — Route-level access control for authenticated users
- **Persistent Generation History** — Browsing history preserved across sessions
- **Responsive Dashboard UI** — Clean, mobile-friendly interface
- **PDF & Image Preview/Download** — Inline preview with secure file download

---

## Tech Stack

| Technology | Purpose |
|---|---|
| React 19 | Frontend Framework |
| Vite 6 | Build Tool |
| TypeScript | Type Safety |
| Tailwind CSS | Styling |
| React Router DOM | Routing |
| Axios | API Communication |
| React Hot Toast | Notifications |
| Lucide React | Icons |

---

## Project Structure

```
src/
├── api/
├── components/
├── pages/
├── store/
├── utils/
├── App.tsx
└── main.tsx
```

---

## Prerequisites

Make sure the following are installed on your machine:

- **Node.js** v18 or higher
- **npm** (bundled with Node.js)

Verify your installation:

```bash
node -v
npm -v
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Omnicortex-Client
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> Update the URL to match your backend deployment address.

---

## Running the App

### Development Server

```bash
npm run dev
```

App will be available at: `http://127.0.0.1:5173`

### Production Build

```bash
npm run build
```

Output files will be generated in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Type Checking

```bash
npm run type-check
# or
tsc -b
```

---

## Backend Requirements

Ensure the backend server is running before launching the frontend.

**Default Backend URL:** `http://127.0.0.1:8000`

### Required API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | User login |
| POST | `/generate-resume` | Resume generation |
| POST | `/generate-image` | Image generation |
| POST | `/analyze-medical` | Medical image analysis |

---

## Application Routes

### Public Routes

| Route | Description |
|---|---|
| `/login` | User login page |
| `/register` | User registration page |

### Protected Routes

| Route | Description |
|---|---|
| `/dashboard` | Main dashboard |
| `/resume` | Resume generation workflow |
| `/image` | AI image generation workflow |
| `/medical` | Medical image analysis workflow |

---

## Authentication Flow

1. User registers via `POST /auth/register`
2. User logs in via `POST /auth/login`
3. JWT token is stored in local storage
4. Axios interceptor automatically attaches the token to every request:
   ```
   Authorization: Bearer <token>
   ```
5. All protected pages require a valid token to access

---

## Local Storage Keys

| Key | Purpose |
|---|---|
| `omnicortex-ai-auth` | Stores authentication token |
| `omnicortex-ai-resume-page` | Persists resume generation history |
| `omnicortex-ai-image-page` | Persists image generation history |

---

## File Downloads

Generated files are served through a secure proxy route to bypass browser CORS restrictions:

```
/__download
```

---

## License

This project is intended for educational and commercial SaaS development purposes.

© Omnicortex AI

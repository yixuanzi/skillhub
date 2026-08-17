# SkillHub Frontend

Enterprise Skill Ecosystem - Frontend Application

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **React Query** - Data fetching
- **Zustand** - State management
- **Axios** - HTTP client

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

## Design System

### Aesthetic Direction

The frontend uses an **Industrial Futurism** design language:

- **Theme**: Dark, professional, technical
- **Typography**:
  - Display: Orbitron (futuristic headers)
  - Body: IBM Plex Sans (readable content)
  - Monospace: JetBrains Mono (code, data)
- **Colors**:
  - Primary: Cyber Green (#00ff9f)
  - Secondary: Cyan (#00d4ff)
  - Accent: Pink (#ff006e)
  - Background: Void (#0a0a0f)
- **Visual Elements**:
  - Grid backgrounds
  - Glowing borders on hover
  - Card-based layouts
  - Scanline effects
  - Monospace badges

### Component Guidelines

- Use monospace fonts for data, IDs, and technical labels
- Apply uppercase tracking-wider for labels
- Include subtle animations (fade-in, slide-in)
- Use Badge components for status indicators
- Cards have glass-morphism effect with backdrop blur

## Project Structure

```
src/
├── api/              # API client and endpoints
├── components/
│   ├── ui/           # Reusable UI components
│   └── layout/       # Layout components
├── hooks/            # Custom React Query hooks
├── pages/            # Route pages
├── store/            # Zustand stores
├── styles/           # Global styles
├── types/            # TypeScript types
└── utils/            # Utility functions
```

## Features

- **Authentication**: JWT-based login/register plus Aegis Portal OIDC SSO
- **Dashboard**: System overview with stats
- **Skills Management**: Create, build, publish, and test skills
- **Users & Roles**: User management with RBAC
- **ACL Rules**: Access control configuration
- **Audit Logs**: Security event tracking

## Environment Variables

```env
VITE_API_BASE_URL=/api/v1
```

## Aegis Portal OIDC

The login page includes an `SSO 认证登录` action that calls the SkillHub
backend at `/api/v1/sso/start?sso=1`. Portal service launches are detected from
`organization_id + client_id` on the root URL and redirected to the same
server-side OIDC start endpoint. The frontend never reads or forwards
`subscription_id`.

The public `/sso/callback` route exchanges the HttpOnly one-time ticket set by
the backend callback, stores the returned local JWT pair in the existing auth
store, loads the current user, and navigates to `/dashboard`. Portal remains
responsible for authentication and multi-organization selection.

# SkillHub Frontend - Quick Start Guide

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

## Installation Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 3. Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |

## Configuration

### Environment Variables

Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=/api/v1
```

### API Proxy Configuration

The Vite dev server proxies API requests to the backend:

```javascript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## Design System Reference

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Cyber Primary | #00ff9f | CTAs, Success, Active states |
| Cyber Secondary | #00d4ff | Info, Links |
| Cyber Accent | #ff006e | Errors, Destructive actions |
| Cyber Warning | #ffbe0b | Warnings |
| Void 950 | #0a0a0f | Main background |
| Void 900 | #12121a | Card backgrounds |

### Typography

| Name | Font | Usage |
|------|------|-------|
| Display | Orbitron | Headers, Titles |
| Body | IBM Plex Sans | Body text |
| Mono | JetBrains Mono | Code, Data, Labels |

### Components

Key UI components are located in `src/components/ui/`:

- `Button` - Primary, secondary, ghost, danger variants
- `Input` - Text inputs with labels and error states
- `Card` - Container with glassmorphism effect
- `Badge` - Status indicators
- `Modal` - Dialog overlays
- `Alert` - Info, success, warning, danger alerts
- `Table` - Data tables with header/body

## Page Routes

| Path | Page | Protected? |
|------|------|------------|
| `/login` | Login | No |
| `/register` | Register | No |
| `/dashboard` | Dashboard Overview | Yes |
| `/skills` | Skills List | Yes |
| `/skills/new` | Create Skill | Yes |
| `/skills/:id` | Skill Details | Yes |
| `/users` | Users & Roles | Yes |
| `/acl` | ACL Rules | Yes |
| `/settings` | Settings | Yes |

## State Management

### Zustand Stores

- `useAuthStore` - Authentication state (user, tokens)
- `useUIStore` - UI state (sidebar, current module)
- `useSkillFilters` - Skill filtering (search, type, status)

### React Query Hooks

API hooks are in `src/hooks/`:

- `useAuth` - Login, register, logout
- `useSkills` - CRUD operations for skills
- `useUsers` - User and role management
- `useACL` - ACL rules and audit logs

## Architecture

### Layer Structure

```
Pages (Routes)
  ↓
Hooks (React Query)
  ↓
API Client (Axios)
  ↓
Backend API
```

### Directory Structure

```
src/
├── api/              # Axios client + endpoint functions
├── components/
│   ├── ui/           # Reusable UI components
│   └── layout/       # Layout (Sidebar, Header)
├── hooks/            # React Query hooks
├── pages/            # Route components
├── store/            # Zustand state stores
├── styles/           # Global CSS
├── types/            # TypeScript definitions
└── utils/            # Helper functions
```

## Common Patterns

### Fetching Data

```tsx
import { useSkills } from '@/hooks/useSkills';

function MyComponent() {
  const { data, isLoading, error } = useSkills();

  if (isLoading) return <Loading />;
  if (error) return <Alert variant="danger">{error.message}</Alert>;

  return <div>{/* Render data */}</div>;
}
```

### Mutations

```tsx
import { useCreateSkill } from '@/hooks/useSkills';

function CreateForm() {
  const createSkill = useCreateSkill();

  const handleSubmit = async () => {
    try {
      await createSkill.mutateAsync(data);
      // Success - navigation or feedback
    } catch (err) {
      // Handle error
    }
  };
}
```

### Protected Routes

Routes are automatically protected using JWT tokens from localStorage:

- Tokens stored in `access_token` and `refresh_token`
- Auto-refresh on 401 responses
- Redirect to login if not authenticated

## Troubleshooting

### Port Already in Use

If port 5173 is in use:
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### API Connection Errors

1. Ensure backend is running on `http://localhost:8000`
2. Check `VITE_API_BASE_URL` in `.env`
3. Verify CORS configuration on backend

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

1. **Configure Backend**: Ensure the backend API is running
2. **Test Authentication**: Register a new user
3. **Create a Skill**: Use the Skills page to build your first skill
4. **Explore ACL**: Configure access control rules

## Support

For issues or questions, refer to:
- Main README: `frontend/README.md`
- MVP Design: `docs/plans/2025-02-28-mvp-design.md`
- API Docs: `docs/api-design.md`

# AI Course Platform Frontend

A modern Next.js 14 application for creating and managing AI-generated courses.

## 🚀 Features

- **Next.js 14** with App Router for optimal performance
- **TypeScript** for type safety and better developer experience
- **Tailwind CSS** with custom design system featuring blue-violet gradient theme
- **React Query** for efficient server state management
- **Zustand** for client-side state management
- **NextAuth.js** for authentication
- **Framer Motion** for smooth animations
- **React Hook Form** with Zod validation
- **Headless UI** for accessible components

## 🛠 Tech Stack

### Core
- Next.js 14
- React 18
- TypeScript 5
- Tailwind CSS 3

### State Management
- Zustand (client state)
- TanStack React Query (server state)

### UI/UX
- Headless UI
- Heroicons
- Framer Motion
- React Hot Toast

### Forms & Validation
- React Hook Form
- Zod
- Hookform Resolvers

### Authentication
- NextAuth.js

### Development Tools
- ESLint
- Prettier
- Jest
- Testing Library

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── layout.tsx      # Root layout
│   │   ├── page.tsx        # Home page
│   │   └── providers.tsx   # App providers
│   ├── components/         # Reusable components
│   │   └── ui/            # UI components
│   ├── lib/               # Utilities and configurations
│   │   ├── api.ts         # API configuration
│   │   ├── utils.ts       # Utility functions
│   │   └── hooks/         # Custom React hooks
│   ├── store/             # Zustand stores
│   ├── types/             # TypeScript type definitions
│   └── styles/            # Global styles
├── public/                # Static assets
└── Configuration files
```

## 🚦 Getting Started

### Prerequisites

- Node.js 18.0.0 or higher
- npm, yarn, or pnpm

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   
   Update the environment variables in `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your-secret-key-here
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📜 Available Scripts

- `dev` - Start development server
- `build` - Build for production
- `start` - Start production server
- `lint` - Run ESLint
- `lint:fix` - Fix ESLint errors
- `format` - Format code with Prettier
- `type-check` - Run TypeScript type checking
- `test` - Run tests
- `test:watch` - Run tests in watch mode
- `test:coverage` - Run tests with coverage

## 🎨 Design System

### Colors

The design system features a blue-violet gradient theme:

- **Primary**: Blue-violet gradient (`#7c70f2` to `#6b46e5`)
- **Secondary**: Purple shades (`#a855f7` to `#7c3aed`)
- **Accent**: Orange for highlights (`#f97316`)
- **Success**: Green (`#22c55e`)
- **Warning**: Amber (`#f59e0b`)
- **Error**: Red (`#ef4444`)
- **Neutral**: Gray scale for text and backgrounds

### Typography

- **Font Family**: Inter (primary), JetBrains Mono (code)
- **Scale**: Tailwind's default scale with custom line heights
- **Weights**: 300, 400, 500, 600, 700

### Components

Pre-built components following modern design patterns:

- Buttons with multiple variants
- Cards with header, body, footer
- Form inputs with validation states
- Loading states and skeletons
- Badges and alerts
- Custom CSS utilities for gradients and animations

## 🔧 Configuration

### Tailwind CSS

Custom configuration with:
- Extended color palette
- Custom font families
- Additional spacing and border radius
- Custom animations and keyframes
- Component and utility classes

### TypeScript

Strict mode enabled with:
- Path mapping for clean imports
- Exact optional property types
- No unchecked indexed access
- Force consistent casing in file names

### ESLint & Prettier

Configured for:
- Next.js best practices
- TypeScript support
- Automatic code formatting
- Import sorting with Tailwind class sorting

## 🧪 Testing

Testing setup with Jest and Testing Library:

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🚀 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Deploy automatically on push

### Manual Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 📦 Key Dependencies

### Production
- `next`: React framework
- `react`: UI library
- `typescript`: Type safety
- `tailwindcss`: Styling
- `@tanstack/react-query`: Server state management
- `zustand`: Client state management
- `next-auth`: Authentication
- `react-hook-form`: Form handling
- `framer-motion`: Animations

### Development
- `eslint`: Code linting
- `prettier`: Code formatting
- `jest`: Testing framework
- `@testing-library/react`: Testing utilities

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## 📄 License

This project is part of the AI Course Generation Platform.
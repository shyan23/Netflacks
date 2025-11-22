# NetFlacks Frontend

A modern, Netflix-inspired UI for the NetFlacks P2P video streaming platform, built with Next.js 15, TypeScript, and Tailwind CSS.

## Features

- **Beautiful Dark Theme**: Netflix-inspired design with smooth animations
- **Video Library**: Browse all available videos with real-time streaming status
- **Drag & Drop Upload**: Easy video upload with progress tracking
- **Custom Video Player**: Built-in player with buffering visualization
- **Real-time Status**: Live P2P stream status updates
- **Responsive Design**: Works on desktop, tablet, and mobile

## Quick Start

### Prerequisites

- Node.js 18+
- The FastAPI streaming server running on port 8080

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Home page
│   │   ├── layout.tsx         # Root layout with Navbar & Footer
│   │   ├── globals.css        # Global styles & animations
│   │   ├── library/           # Video library page
│   │   ├── upload/            # Upload page
│   │   └── watch/[videoId]/   # Video player page
│   ├── components/            # React components
│   │   ├── Navbar.tsx         # Navigation bar
│   │   ├── VideoCard.tsx      # Video thumbnail card
│   │   ├── VideoPlayer.tsx    # Custom video player
│   │   ├── Footer.tsx         # Footer component
│   │   └── Icons.tsx          # SVG icons
│   ├── lib/                   # Utilities
│   │   └── api.ts             # API service layer
│   ├── hooks/                 # Custom React hooks
│   │   └── useStreamStatus.ts # Stream status polling hook
│   └── types/                 # TypeScript types
│       └── index.ts           # Type definitions
├── public/                    # Static assets
├── next.config.ts             # Next.js config with API proxy
└── .env.local                 # Environment variables
```

## Configuration

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### API Proxy

The Next.js config includes rewrites to proxy API requests to the FastAPI backend:

- `/api/*` → `http://localhost:8080/api/*`
- `/stream/*` → `http://localhost:8080/stream/*`
- `/upload` → `http://localhost:8080/upload`

## Pages

### Home (`/`)
- Hero section with branding
- Feature highlights
- Recently added videos

### Library (`/library`)
- Grid view of all videos
- Real-time streaming status

### Upload (`/upload`)
- Drag & drop upload zone
- Progress tracking
- Automatic distribution to P2P network

### Watch (`/watch/[videoId]`)
- Custom video player
- Real-time buffering progress
- P2P network status panel

## Tech Stack

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Hooks**: State management

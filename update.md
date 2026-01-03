# Frontend Update Documentation

This document details all frontend changes made to the GraderWise project, covering the Landing Page, Authentication (Sign Up/Login), and Dashboard. It is designed to provide a complete understanding of the current frontend state for replication or further development.

## 1. Design System & Global Styles

The application uses a modern, responsive design system built with **Tailwind CSS v4**.

*   **File**: `frontend/app/globals.css`
*   **Theme**: Supports both Light and Dark modes (`dark:bg-slate-950`).
*   **Color Palette**:
    *   **Primary**: Royal Blue (`--color-royal-blue-500` to `900`).
    *   **Backgrounds**: Slate scales for depth (e.g., `slate-950` for dark mode).
    *   **Gradients**: Extensive use of gradients for backgrounds, buttons, and text (`bg-gradient-to-r`, `bg-clip-text`).
*   **Typography**: Geist Sans and Mono fonts.
*   **Libraries**:
    *   `lucide-react`: For consistent, clean iconography.
    *   `framer-motion`: For smooth animations and transitions.

## 2. Landing Page

The landing page (`frontend/app/page.tsx`) is designed to convert visitors with a high-premium aesthetic.

### Key Sections:
1.  **Navigation**:
    *   Sticky navbar with backdrop blur (`backdrop-blur-md`).
    *   Logo with gradient background.
    *   Links: Features, How it Works, Login, and a "Get Started" CTA button.
2.  **Hero Section**:
    *   **Visuals**: "Intelligent Grading for Modern Educators" headline with gradient text.
    *   **Animation**: "Moving Training" background effect using `framer-motion`.
    *   **CTA**: "Try Grading Agent" (primary) and "View NotebookLLM Demo" (secondary).
    *   **Trust Signals**: "Open Source Logic" and "Bring Your Own Keys".
3.  **Stats Section**:
    *   Displays metrics like "90% Grading Time Saved" with hover gradients on text.
4.  **Features Grid**:
    *   Bento-grid style cards showcasing core features: AI-Powered Grading, Privacy First, Professional Dashboard, Context-Aware.
    *   Each card has a unique soft gradient border and background color.
5.  **How It Works**:
    *   3-step process visualization (Ingest Context -> Agentic Analysis -> Review & Export).
    *   Connector line graphic (responsive).
6.  **Use Cases (Academia)**:
    *   Targeted cards for Professors, Teaching Assistants, and Dept. Heads.
    *   Tags for key benefits (e.g., "Scale", "Fairness").
7.  **Footer**:
    *   Links to Features, Company, and legal pages.

## 3. Authentication (Sign Up / Login)

The authentication flow (`frontend/app/signup/page.tsx`) provides a unified experience for both signing up and logging in.

### Features:
*   **Unified Page**: A single page handles both Login and Signup with a toggle switch.
*   **Visuals**:
    *   Rich gradient background (`indigo-900` to `purple-900`).
    *   Glassmorphism card effect (`bg-white/95 backdrop-blur-xl`).
    *   Animated background blobs.
*   **Functionality**:
    *   **State Management**: `isLogin` state toggles form fields (Name is hidden on login).
    *   **Animations**: `AnimatePresence` allows smooth height adjustment when switching modes.
    *   **Mock Integration**: "Sign In with Google" and "Sign In with GitHub" buttons (UI only).
    *   **Form Handling**: Submits to a mock API (1.5s delay), shows a success state, and redirects to `/dashboard`.

## 4. Dashboard

The dashboard is built with a layout-first approach (`frontend/app/(dashboard)`), verifying a professional interface for educators.

### 4.1 Layout & Sidebar
*   **File**: `frontend/components/Sidebar.tsx`
*   **structure**: Fixed sidebar on the left, scrollable content on the right.
*   **User Profile**: Hydrates user name from `localStorage` ("Instructor" default).
*   **Navigation**:
    *   Primary: Dashboard, New Grading Job, Class History, Students.
    *   System: Settings, Support.
    *   **System Status**: "System Online v2.4.0" indicator with pulsing green dot.

### 4.2 Dashboard Home (`/dashboard`)
*   **File**: `frontend/app/(dashboard)/dashboard/page.tsx`
*   **Header**:
    *   Welcome message ("Welcome back, Prof. Anderson").
    *   Quick actions: Notification dropdown, Theme toggle, "Create Assessment" button.
*   **Stats Cards**:
    *   3 key metrics: Total Submissions, Avg. Grading Time, Class Average.
    *   Visuals: Icon with colored background, trend badges (e.g., "+12% from last week").
*   **Quick Actions Panel**:
    *   Shortcuts for "Import Rubric" and "Course Materials".
    *   Prominent "Start New Grading Job" button.
*   **Recent Activity Table**:
    *   Displays recent grading jobs.
    *   **Hydration**: Fetches data from `localStorage` (`gradingHistory`).
    *   **Visuals**: Student initials avatars with random colors, status badges (e.g., "Graded").

## How to Replicate
1.  **Setup**: Initialize a Next.js App Router project with Tailwind CSS.
2.  **Dependencies**: Install `lucide-react` (icons) and `framer-motion` (animations).
3.  **Styles**: Copy `globals.css` into your project for the royal-blue theme.
4.  **Components**:
    *   Implement `Sidebar.tsx` for the layout shell.
    *   Create `page.tsx` for the landing page using the section breakdown above.
    *   Replicate the `signup` logic with the Framer Motion AnimatePresence key.
5.  **State**: Use `localStorage` to persist mock user data and grading history for a functional demo.

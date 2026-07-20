# Comprehensive Client Documentation - Infiverse

## Table of Contents
1.  [Overview & Technology Stack](#1-overview--technology-stack)
2.  [Project Structure](#2-project-structure)
3.  [Data Flow Diagrams](#3-data-flow-diagrams)
    - [Authentication Flow](#31-authentication-flow)
    - ["Start Day" Attendance Flow](#32-start-day-attendance-flow)
4.  [Deep Dive: State Management (Context API)](#4-deep-dive-state-management-context-api)
    - [`AuthProvider`](#41-authprovider)
    - [`SocketProvider`](#42-socketprovider)
    - [`DashboardProvider`](#43-dashboardprovider)
    - [`ThemeProvider`](#44-themeprovider)
5.  [Deep Dive: Page & Component Breakdown](#5-deep-dive-page--component-breakdown)
    - [Core Pages (`pages/`)](#51-core-pages-pages)
    - [Key Reusable Components (`components/`)](#52-key-reusable-components-components)
6.  [Styling & Theming](#6-styling--theming)
7.  [Local Setup & Troubleshooting](#7-local-setup--troubleshooting)
8.  [Handover Plan for Frontend (Nikhil)](#8-handover-plan-for-frontend-nikhil)

---

## 1. Overview & Technology Stack

The Infiverse client is a modern, responsive web application built with React. It serves as the user interface for the Infiverse workforce management system, providing a rich and interactive experience for administrators, managers, and employees.

### 1.1. Core Technologies

-   **Framework**: React 18 with Vite
-   **Routing**: `react-router-dom`
-   **Styling**: Tailwind CSS
-   **UI Components**: `shadcn/ui` - A collection of accessible and composable components.
-   **Data Visualization**: `recharts` for charts and graphs.
-   **State Management**: React Context API.
-   **API Communication**: `axios` for HTTP requests.
-   **Real-time**: `socket.io-client` for WebSocket communication.
-   **Progressive Web App (PWA)**: Enabled via `vite-plugin-pwa` for installability.

---

## 2. Project Structure

The `src` directory is organized by feature and function:

-   **`pages/`**: Contains the top-level components for each route/page (e.g., `Dashboard.jsx`, `Tasks.jsx`, `Login.jsx`).
-   **`components/`**: Contains reusable components.
    -   **`components/ui/`**: Houses the `shadcn/ui` components (e.g., `Button.jsx`, `Card.jsx`, `Input.jsx`).
    -   **`components/admin/`**: Components specific to the admin dashboard.
    -   Other folders group components by feature (e.g., `attendance/`, `tasks/`).
-   **`layouts/`**: Contains layout components that wrap pages, such as `DashboardLayout.jsx` which includes the sidebar and header.
-   **`context/`**: Holds all React Context providers for global state management (e.g., `auth-context.jsx`).
-   **`hooks/`**: Contains custom React hooks (e.g., `use-toast.js`).
-   **`lib/`**: Utility functions, API configuration (`api.js`), and other shared logic.
-   **`assets/`**: Static assets like images and SVGs.

---

## 3. Data Flow Diagrams

### 3.1. Authentication Flow

This diagram illustrates how a user logs in and how the application state is updated.

```
[User] -> Enters credentials in [pages/Login.jsx]
   |
   v
[useAuth hook] -> calls login(credentials)
   |
   v
[context/auth-context.jsx] -> POST /api/auth/login with axios
   |
   v
[Server] -> Validates credentials, returns { token, user }
   |
   v
[context/auth-context.jsx] -> Stores token & user in localStorage
   |                         -> Updates internal state (setUser)
   v
[App.jsx] -> Re-renders due to context change
   |
   v
[components/ProtectedRoute.jsx] -> Reads user from useAuth()
   |                               -> Allows access to protected routes
   v
[pages/Dashboard.jsx] -> Renders the user's dashboard
```

### 3.2. "Start Day" Attendance Flow

This diagram shows the process of a user starting their workday.

```
[User] -> Clicks "Start Day" button in [pages/AttendanceDashboard.jsx]
   |
   v
[Component] -> Calls navigator.geolocation.getCurrentPosition()
   |
   v
[Browser] -> Prompts user for location access, returns coordinates
   |
   v
[Component] -> Calls API: POST /api/attendance/start-day/:userId
   |             with { latitude, longitude, workFromHome }
   v
[Server] -> Validates location against office radius (if not WFH)
   |         -> Creates/updates Attendance record in MongoDB
   v
[Component] -> Receives success response from server
   |             -> Displays success toast notification
   |             -> Updates UI to show "Day Started" status
```

---

## 4. Deep Dive: State Management (Context API)

Global state is managed via React's Context API to avoid prop drilling. Here’s a breakdown of each provider.

### 4.1. `AuthProvider`

-   **File**: `context/auth-context.jsx`
-   **Purpose**: Manages the entire authentication state of the application.
-   **Provided State & Functions**:
    -   `user`: An object containing the logged-in user's data (`id`, `name`, `role`, etc.), or `null` if not logged in.
    -   `loading`: A boolean that is `true` during login or registration API calls.
    -   `login(credentials)`: A function that takes an email and password, calls the login API, and updates the state.
    -   `register(userData)`: A function that takes user data, calls the register API, and updates the state.
    -   `logout()`: A function that clears the user state and removes the token from `localStorage`.

### 4.2. `SocketProvider`

-   **File**: `context/socket-context.jsx`
-   **Purpose**: Establishes and maintains the WebSocket connection to the server.
-   **Provided State & Functions**:
    -   `socket`: The `socket.io-client` instance. Components can use this to emit events or listen for real-time updates from the server (e.g., new notifications).

### 4.3. `DashboardProvider`

-   **File**: `context/DashboardContext.jsx`
-   **Purpose**: Holds state that is shared across various dashboard components.
-   **Provided State & Functions**:
    -   `recentReviews`, `hasNewReviews`: State related to task submission reviews.
    -   `markReviewsAsSeen`: A function to clear new review notifications.
    -   This context is a good candidate for holding shared filters, date ranges, or data that multiple dashboard widgets might need.

### 4.4. `ThemeProvider`

-   **File**: `components/theme-provider.jsx`
-   **Purpose**: Manages the application's visual theme (light/dark mode).
-   **Implementation**: Uses the `next-themes` library to handle theme switching and persists the user's choice in `localStorage`.

---

## 5. Deep Dive: Page & Component Breakdown

### 5.1. Core Pages (`pages/`)

| Page Component | Route | Description |
| :--- | :--- | :--- |
| `Login.jsx` | `/login` | Public page for user login. |
| `Register.jsx` | `/register` | Public page for new user registration. |
| `AdminDashboard.jsx` | `/admindashboard` | **Admin-only**. The central hub for admins, showing aggregate data, system status, and navigation to management pages. |
| `UserDashboard.jsx` | `/userdashboard` | **User-only**. The landing page for regular users, showing their tasks, progress, and attendance status. |
| `Tasks.jsx` | `/tasks` | Displays a list of tasks. Admins can see all tasks, while users see tasks assigned to them. |
| `TaskDetails.jsx` | `/tasks/:id` | Shows the detailed view of a single task. |
| `Progress.jsx` | `/progress` | A form where users submit their daily progress report. This is a critical step before ending the workday. |
| `TodaysAim.jsx` | `/aims` | A simple page for users to set their primary goal for the day. |
| `EmployeeMonitoring.jsx`| `/monitoring` | **Admin-only**. The main UI for the monitoring system. Allows admins to view screenshots and alerts. |
| `AttendanceAnalytics.jsx`| `/attendance-analytics`| **Admin-only**. Displays charts and stats related to team attendance. |
| `SalaryManagement.jsx` | `/salary-management` | **Admin-only**. The main page for managing payroll and calculating salaries for all employees. |
| `UserManagement.jsx` | `/user-management` | **Admin-only**. A page to view, create, and edit user accounts and roles. |

### 5.2. Key Reusable Components (`components/`)

| Component | Location | Description |
| :--- | :--- | :--- |
| `DashboardLayout.jsx` | `layouts/` | The main layout for the authenticated app. It renders the `Sidebar` and a `Header` and provides the main content area for the pages. |
| `ProtectedRoute.jsx` | `components/` | A higher-order component that wraps routes to enforce authentication and role-based access control. |
| `Sidebar.jsx` | `components/ui/` | The main navigation sidebar, with links that change based on the user's role. |
| `ModeToggle.jsx` | `components/` | The UI button for switching between light and dark themes. |
| `PushNotificationSetup.jsx`| `components/` | Handles the logic for subscribing the user to browser push notifications. |

---

## 6. Styling & Theming

-   **Tailwind CSS**: The project uses Tailwind CSS for all styling. Utility classes are applied directly in the JSX. The configuration is in `tailwind.config.js`.
-   **`index.css`**: This file contains the base Tailwind directives (`@tailwind base;`, `@tailwind components;`, `@tailwind utilities;`) and any global custom styles.
-   **Dark Mode**: Handled by the `ThemeProvider` and the `dark:` variant in Tailwind. The `next-themes` library adds a `data-theme="dark"` attribute to the `<html>` element, which Tailwind uses to apply dark mode styles.

---

## 7. Local Setup & Troubleshooting

### 7.1. Setup

1.  Navigate to the `client` directory: `cd Handover-Infi/client`
2.  Install dependencies: `npm install`
3.  (Optional) If your server is not at `http://localhost:5000`, create a `.env.local` file and set `VITE_API_URL`.
4.  Start the dev server: `npm run dev`

### 7.2. Troubleshooting

-   **CORS Error**: If you see a CORS error in the browser console, it means the client's URL is not whitelisted on the server. Ensure the `CORS_ORIGIN` variable in the server's `.env` file matches the client's URL (e.g., `http://localhost:5173`).
-   **401 Unauthorized**: If you are immediately logged out or see 401 errors, your JWT might be expired or invalid. Try clearing your browser's `localStorage` and logging in again.
-   **Connection Refused**: If API calls fail with a "connection refused" error, ensure the server is running and that the `VITE_API_URL` in the client's `.env.local` (if it exists) is correct.

---

## 8. Handover Plan for Frontend (Nikhil)

This section details the pending UI/UX tasks.

### 8.1. High-Priority Tasks

-   **Consent & Alerts UI**
    -   **Consent Toggle**: Implement a UI toggle in the user's settings or dashboard. This should call the `POST /api/consent` endpoint. The toggle should be disabled if the user is currently being monitored and re-enabled once the session is over.
    -   **Alerts Page**: Create a new page for administrators (`/alerts`) to view monitoring alerts.
        -   Fetch data from `/api/monitoring/alerts`.
        -   Display alerts in a table or list, showing employee, timestamp, severity, and description.
        -   For alerts with a `screenshot_id`, display a thumbnail. Clicking the thumbnail should open a dialog (`Dialog` component) showing the full-size image fetched from `/api/monitoring/screenshots/:screenshotId`.

-   **Dashboard Polish**
    -   **Activity Heatmap**: On the admin dashboard, integrate a heatmap to visualize team activity. You can use a library like `react-calendar-heatmap` and feed it data aggregated from the `Attendance` model.
    -   **Summary Cards**: Add `Card` components to the top of the main dashboards (admin and user) to show key stats like "Productivity Score Today," "Idle Time," and "Active Alerts."

### 8.2. Deployment & Domain

-   **Configure Domain**: Configure the purchased domain on Vercel to point to the deployed frontend application.
-   **Apply SSL**: Ensure SSL is correctly configured and force HTTPS redirection.
-   **End-to-End Testing**: After deployment, perform a full end-to-end test of the user journey: login, start day, set aim, submit progress, end day. For admins: create a task, view monitoring data, and check reports.

### 8.3. Code Cleanup

-   **Remove `App_updated.jsx`**: This file in `src/` is a duplicate. Review it for any unique code, merge if necessary into `App.jsx`, and then delete it.
-   **Refactor `console.log`**: Search the project for `console.log` statements and remove any that are not essential for debugging, especially in production builds.
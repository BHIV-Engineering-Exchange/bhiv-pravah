# AI Agent Logistics System - Frontend

Modern React frontend for the AI Agent Logistics System with Tailwind CSS and beautiful design.

## 🚀 Features

- **Modern UI/UX**: Built with React 18 + Vite
- **Tailwind CSS**: Custom design system with gradients, animations, and glass effects
- **Routing**: React Router v6 for seamless navigation
- **Charts**: Recharts for beautiful data visualization
- **Icons**: Lucide React for consistent iconography
- **API Integration**: Axios for backend communication
- **Real-time**: WebSocket support for live updates
- **Notifications**: React Hot Toast for user feedback
- **Dark Mode**: Built-in theme switching

## 📦 Installation

```bash
cd frontend
npm install
```

## 🏃‍♂️ Running the Application

### Development Mode
```bash
npm run dev
```
The app will be available at `http://localhost:3000`

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 🎨 Design System

### Color Palette
- **Primary**: Vibrant Green (HSL: 160 84% 39%)
- **Secondary**: Purple (HSL: 262 83% 58%)
- **Accent**: Orange (HSL: 38 92% 50%)
- **Info**: Blue (HSL: 217 91% 60%)
- **Success**: Green (HSL: 160 84% 39%)
- **Warning**: Orange (HSL: 38 92% 50%)
- **Destructive**: Red (HSL: 0 84% 60%)

### Typography
- **Body**: Inter (weights 300-900)
- **Headings**: Space Grotesk

### Components
- Buttons with gradient effects and glow shadows
- Cards with hover lift animations
- Tables with smooth transitions
- Forms with validation states
- Modals with backdrop blur
- Badges with semantic colors

## 📂 Project Structure

```
src/
├── components/          # Reusable components
│   ├── layout/         # Layout components (Sidebar, Header, etc.)
│   ├── common/         # Common UI components
│   │   ├── ui/        # Base UI components
│   │   ├── forms/     # Form components
│   │   └── charts/    # Chart components
│   └── [domain]/      # Domain-specific components
├── pages/              # Page components
├── services/           # API services
│   ├── api/           # API clients
│   └── websocket/     # WebSocket services
├── hooks/             # Custom React hooks
├── context/           # React context providers
├── utils/             # Utility functions
├── App.jsx            # Main App component
└── main.jsx           # Entry point
```

## 🔌 API Integration

The frontend connects to the backend API at `http://localhost:8000` (configurable via environment variables).

### Environment Variables
Create a `.env` file:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🧭 Available Routes

- `/` - Dashboard Overview
- `/logistics` - Logistics Management
- `/crm` - CRM Management
- `/infiverse` - Employee Monitoring
- `/inventory` - Inventory Management
- `/suppliers` - Supplier Management
- `/products` - Product Catalog
- `/agents` - AI Agents Control
- `/workflows` - Automated Workflows
- `/decisions` - AI Decision Engine
- `/learning` - RL Learning System
- `/notifications` - Alert Management
- `/emails` - Email Automation
- `/reports` - Reports & Analytics
- `/settings` - System Settings
- `/users` - User Management

## 🎯 Key Features by Module

### Dashboard
- System overview with key metrics
- Real-time activity feed
- System health monitoring
- Performance charts

### Logistics
- Order management
- Shipment tracking
- Delivery scheduling
- Automated restocking

### CRM
- Account management
- Lead tracking
- Opportunity pipeline
- Activity management

### Inventory
- Stock level monitoring
- Demand forecasting
- Inventory optimization
- Low stock alerts

### AI & Automation
- AI agent control panel
- Workflow builder
- Decision engine
- RL learning system

## 🛠️ Tech Stack

- **React 18.3** - UI library
- **Vite 5.1** - Build tool
- **React Router 6.22** - Routing
- **Tailwind CSS 3.4** - Styling
- **Axios 1.6** - HTTP client
- **Recharts 2.12** - Charts
- **Lucide React** - Icons
- **React Hot Toast** - Notifications
- **Socket.io Client** - WebSocket
- **date-fns** - Date utilities

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop (1920px+)
- Laptop (1024px - 1919px)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

### 🎯 Responsive Sidebar Features

#### Desktop (≥ 1024px)
- **Collapsible Sidebar**: Toggle between 256px (full) and 64px (icons only)
- **Smooth Transitions**: 300ms animations between states
- **Tooltips**: Hover over icons in collapsed state to see labels
- **Content Adjustment**: Main content automatically adjusts margin

#### Mobile (< 1024px)
- **Overlay Mode**: Sidebar slides in from left with backdrop blur
- **Touch Optimized**: Minimum 44x44px touch targets
- **Auto-close**: Sidebar closes when navigating or clicking backdrop
- **Scroll Lock**: Body scroll is locked when sidebar is open

#### Testing the Sidebar

**Desktop:**
1. Click ChevronLeft/Right button to collapse/expand
2. Watch sidebar smoothly transition between 256px ↔ 64px
3. Hover over icons in collapsed state to see tooltips

**Mobile:**
1. Click hamburger menu (☰) to open
2. Sidebar slides in with dark backdrop
3. Click any menu item or backdrop to close
4. Sidebar auto-closes when navigating

For detailed responsive features, see **[RESPONSIVE_FEATURES.md](./RESPONSIVE_FEATURES.md)**

For sidebar functionality guide, see **[SIDEBAR_DEMO.md](./SIDEBAR_DEMO.md)**

## 🎨 Customization

### Theme Colors
Edit `src/index.css` to customize the color palette:

```css
:root {
  --primary: 160 84% 39%;
  --secondary: 262 83% 58%;
  /* ... other colors */
}
```

### Animations
Customize animations in `tailwind.config.js`:

```js
animation: {
  'fade-in': 'fade-in 0.5s ease-out',
  'hover-lift': 'hover-lift 0.3s ease-out',
  // ... other animations
}
```

## 🚀 Deployment

### Build for production
```bash
npm run build
```

The optimized production build will be in the `dist/` folder.

### Deploy to Vercel/Netlify
The app is ready to deploy to any static hosting service:

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `dist`

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Support

For support, email support@aiagentsystem.com or open an issue on GitHub.

# School Management System - Frontend

React frontend for the School Management System.

## Features

- ✅ Super Admin Login
- ✅ Super Admin Dashboard
- ✅ Create Schools
- ✅ View All Schools
- ✅ Create School Admins
- ✅ JWT Token Authentication
- ✅ Protected Routes
- ✅ Role-based Access Control
- ✅ Responsive Design

## Tech Stack

- **React 18** - UI Library
- **React Router** - Navigation
- **Vite** - Build Tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP Client
- **JWT Decode** - Token Management

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Environment Configuration

The frontend is configured to connect to the backend at `http://localhost:8000`.

To change the backend URL, edit `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'http://your-backend-url:8000';
```

## Default Credentials

**Super Admin:**
- Email: `blackholeinfiverse48@gmail.com`
- Password: `superadmin123`

⚠️ **Note**: These credentials are set during backend setup. They cannot be changed from the frontend.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Login.jsx          # Login page
│   │   ├── Dashboard.jsx      # Main dashboard
│   │   ├── SchoolList.jsx     # List all schools
│   │   ├── CreateSchool.jsx   # Create new school
│   │   └── CreateAdmin.jsx    # Create school admin
│   ├── context/
│   │   └── AuthContext.jsx    # Authentication context
│   ├── services/
│   │   └── api.js             # API service layer
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Global styles
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Features Explained

### 1. Login Page
- Simple email/password login form
- JWT token storage
- Error handling
- Redirects to dashboard on success

### 2. Super Admin Dashboard
- View all schools in a table
- Create new schools
- Create school admins (assigned to specific schools)
- Logout functionality
- Role-based access control

### 3. Protected Routes
- Only authenticated users can access dashboard
- Automatic redirect to login if not authenticated
- Token expiration handling

### 4. API Integration
- All API calls use axios
- JWT token automatically included in requests
- Automatic token refresh handling
- Error handling for 401 (unauthorized) responses

## Security Notes

1. **JWT Tokens**: Stored in localStorage (consider using httpOnly cookies for production)
2. **Token Expiration**: Tokens expire after 30 minutes (configurable in backend)
3. **Role-based Access**: Only SUPER_ADMIN can access the dashboard
4. **Password Requirements**: Admin passwords must be at least 6 characters

## PRANA Telemetry System

### Unified PRANA Core

EMS uses the unified PRANA core telemetry engine (shared with Gurukul). The system is initialized via `ems_prana.js` wrapper at app startup.

- ✅ **Loads once at app startup**: PRANA is imported at the top level of `main.jsx` before React renders
- ✅ **Lives outside React lifecycle**: Uses singleton pattern with global `window.PRANA` namespace
- ✅ **No remounts on route changes**: PRANA modules persist across all route navigations
- ✅ **Unified implementation**: Same core logic as Gurukul, configured for EMS context

**Important**: Do NOT:
- ❌ Wrap PRANA modules in React components
- ❌ Lazy-load PRANA modules
- ❌ Add cleanup logic that removes PRANA event listeners
- ❌ Refactor PRANA code into React hooks or components

### PRANA Kill Switch

For emergency scenarios or demos, PRANA telemetry can be disabled globally:

```javascript
// In browser console or before app loads:
window.PRANA_DISABLED = true;
```

When enabled, the unified PRANA core will:
- Exit immediately on load
- Log a console message indicating telemetry is disabled
- Not attach any event listeners
- Not send any packets to the Bucket

**Usage**:
- Set `window.PRANA_DISABLED = true` before the app loads to prevent PRANA initialization
- Or set it in browser console after load (will prevent new intervals/listeners, but existing ones may continue until next page reload)

**Files**:
- `ems_prana.js` - Thin wrapper that initializes unified PRANA core with EMS context
- `src/utils/*.js` - Wrapper re-exports from unified `prana-core/` (for compatibility)

## Troubleshooting

### CORS Errors
If you encounter CORS errors, ensure the backend has CORS configured correctly:
- Check `app/main.py` for CORS middleware configuration
- Backend should allow requests from `http://localhost:3000`

### Authentication Issues
- Check that the backend is running on `http://localhost:8000`
- Verify your credentials match the super admin setup
- Check browser console for detailed error messages

### Token Expired
- Tokens expire after 30 minutes
- Simply log in again to get a new token
- The app will automatically redirect to login on token expiration

## Next Steps

To extend this frontend:
1. Add pagination for school list
2. Add edit/delete functionality for schools
3. Add school admin management interface
4. Add teacher, parent, and student dashboards
5. Add data visualization/charts
6. Add search and filtering capabilities

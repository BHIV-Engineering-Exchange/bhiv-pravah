# Artha Frontend

React-based frontend for the Artha accounting system.

## Features

- **Invoice Management**: Create, view, and manage invoices
- **Expense Management**: Submit expenses with receipt uploads
- **Navigation**: Clean navigation between different modules
- **Authentication**: JWT-based authentication with role management
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## Components

### Pages
- `Invoices.jsx` - Invoice listing and management
- `Expenses.jsx` - Expense listing and management
- `Dashboard.jsx` - Main dashboard (existing)
- `Ledger.jsx` - Ledger view (existing)
- `Login.jsx` - Authentication (existing)

### Components
- `Navigation.jsx` - Main navigation bar
- `Layout.jsx` - Page layout wrapper
- `InvoiceForm.jsx` - Invoice creation form
- `ExpenseForm.jsx` - Expense submission form with file upload

### Services
- `invoiceService.js` - Invoice API calls
- `expenseService.js` - Expense API calls (exported from invoiceService)
- `api.js` - Base API configuration (existing)
- `authService.js` - Authentication service (existing)

## API Integration

All components integrate with the backend API endpoints:

### Invoice Endpoints
- `GET /api/v1/invoices` - List invoices
- `POST /api/v1/invoices` - Create invoice
- `POST /api/v1/invoices/:id/send` - Send invoice
- `POST /api/v1/invoices/:id/payment` - Record payment

### Expense Endpoints
- `GET /api/v1/expenses` - List expenses
- `POST /api/v1/expenses` - Create expense (with file upload)
- `POST /api/v1/expenses/:id/approve` - Approve expense
- `POST /api/v1/expenses/:id/record` - Record expense

## File Upload Support

The expense form supports file uploads for receipts:
- Multiple file selection
- Image and PDF support
- 10MB file size limit
- 5 files maximum per expense

## Navigation

The application includes a responsive navigation bar with:
- Logo and branding
- Main navigation links
- User information display
- Logout functionality

## Styling

Uses Tailwind CSS for styling with:
- Responsive design
- Consistent color scheme
- Professional table layouts
- Modal dialogs for forms
- Status badges with color coding

## Development

```bash
cd frontend
npm install
npm run dev
```

## Testing

Basic component tests are included:
```bash
npm run test
```

## Environment Variables

Configure the API URL in your environment:
```
VITE_API_URL=http://localhost:5000/api/v1
```
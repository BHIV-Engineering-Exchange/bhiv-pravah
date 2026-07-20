# AI CRM Logistics Backend - MongoDB Edition

Production-ready Node.js + Express + MongoDB backend for Logistics & Inventory AI CRM system.

## 🚀 Features

- **100% MongoDB** - No SQL dependencies
- **JWT Authentication** - Secure token-based auth
- **Role-Based Access Control** - Admin, Manager, Customer roles
- **Automated Inventory Management** - Stock tracking with MongoDB transactions
- **Email Automation** - Automated restock notifications via NodeMailer
- **RESTful APIs** - Clean, well-documented endpoints
- **Production Ready** - Error handling, validation, security

## 📋 Prerequisites

- Node.js 18+ and npm
- MongoDB Atlas account (or local MongoDB)
- SMTP credentials (Gmail/SendGrid) for email features

## 🛠️ Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your MongoDB URL from root .env file
```

3. **Seed the database:**
```bash
npm run seed
```

4. **Start the server:**
```bash
# Development mode
npm run dev

# Production mode
npm start
```

Server will run on `http://localhost:8000`

## 🔑 Default Login Credentials

After seeding:

**Admin:**
- Email: `admin@company.com`
- Password: `Admin@123456`

**Manager:**
- Email: `manager@company.com`
- Password: `Manager@123`

**Customer:**
- Email: `customer1@example.com`
- Password: `Customer@123`

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - Register first admin
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Users (Admin only)
- `GET /api/users` - List all users
- `POST /api/users` - Create user
- `GET /api/users/:id` - Get user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user
- `GET /api/users/stats/summary` - User statistics

### Products
- `GET /api/products` - List products
- `POST /api/products` - Create product (Admin/Manager)
- `GET /api/products/:id` - Get product
- `PUT /api/products/:id` - Update product (Admin/Manager)
- `DELETE /api/products/:id` - Delete product (Admin/Manager)

### Orders
- `GET /api/orders` - List orders
- `POST /api/orders` - Place order (Customer)
- `GET /api/orders/:id` - Get order
- `PUT /api/orders/:id/dispatch` - Mark dispatched (Admin/Manager)
- `PUT /api/orders/:id/deliver` - Confirm delivery (Customer)

### Inventory
- `GET /api/inventory/logs` - Inventory change logs
- `POST /api/inventory/adjust` - Manual adjustment (Admin/Manager)
- `GET /api/inventory/low-stock` - Low stock products
- `GET /api/inventory/stats` - Inventory statistics

### Restock
- `GET /api/restock` - List restock requests
- `POST /api/restock/:id/resend-email` - Resend email
- `PUT /api/restock/:id/complete` - Mark completed

### Dashboard
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/recent-activity` - Recent activity
- `GET /api/dashboard/alerts` - System alerts

## 🔐 Security Features

- JWT token authentication
- bcrypt password hashing
- Role-based authorization middleware
- Request rate limiting
- Helmet.js security headers
- CORS configuration
- Input validation with express-validator

## 📊 MongoDB Collections

- **users** - User accounts with roles
- **products** - Product catalog with inventory
- **orders** - Customer orders with tracking
- **inventory_logs** - Inventory change history
- **restock_requests** - Automated restock tracking

## 🔄 Business Logic

### Order Flow
1. Customer places order
2. System validates stock availability
3. MongoDB transaction reduces inventory
4. Order created with PLACED status
5. If stock < threshold → trigger restock
6. Manager marks as DISPATCHED
7. Customer confirms DELIVERED

### Automated Restocking
1. Stock falls below minThreshold
2. System creates RestockRequest
3. Email sent to supplier automatically
4. Manager marks as RESTOCKED when received
5. Inventory updated via transaction

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"Admin@123456"}'
```

## 📧 Email Configuration

Configure SMTP in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourcompany.com
```

For Gmail, create an [App Password](https://myaccount.google.com/apppasswords).

## 🏗️ Project Structure

```
backend-nodejs/
├── src/
│   ├── config/          # Database & constants
│   ├── middleware/      # Auth, validation, errors
│   ├── models/          # MongoDB schemas
│   ├── routes/          # API routes
│   ├── scripts/         # Seed & utilities
│   ├── services/        # Email service
│   └── server.js        # Main app entry
├── package.json
└── .env
```

## 🚀 Production Deployment

1. Set `NODE_ENV=production` in `.env`
2. Configure production MongoDB URL
3. Set secure `JWT_SECRET`
4. Configure production CORS origins
5. Use process manager (PM2):

```bash
npm install -g pm2
pm2 start src/server.js --name ai-crm-backend
pm2 save
```

## 📝 License

MIT

## 👨‍💻 Author

AI CRM Logistics Team

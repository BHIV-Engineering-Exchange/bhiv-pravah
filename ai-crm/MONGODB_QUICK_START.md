# MongoDB Backend Quick Start Guide

## 🚀 Backend Setup & Run

### 1. Install Dependencies
```bash
cd backend-nodejs
npm install
```

### 2. Environment Configuration
The `.env` file is already configured with your MongoDB Atlas connection. No changes needed.

### 3. Seed the Database
```bash
npm run seed
```

This will create:
- **Admin account**: admin@company.com / Admin@123456
- **Manager account**: manager@company.com / Manager@123
- **Customer accounts**: customer1@example.com / Customer@123
- **Sample products** with inventory

### 4. Start the Backend Server
```bash
# Development mode (auto-restart on changes)
npm run dev

# OR production mode
npm start
```

Server will run on **http://localhost:8000**

---

## 🎨 Frontend Setup & Run

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start the Frontend
```bash
npm run dev
```

Frontend will run on **http://localhost:5173**

---

## 🔐 Login Credentials

After seeding, use these credentials:

### Admin Dashboard
- Email: `admin@company.com`
- Password: `Admin@123456`
- Full access to all features

### Manager Dashboard
- Email: `manager@company.com`
- Password: `Manager@123`
- Can manage inventory and dispatch orders

### Customer Dashboard (Shopkeeper)
- Email: `customer1@example.com`
- Password: `Customer@123`
- Can place orders and confirm deliveries

---

## ✅ Verify Backend is Running

### Health Check
```bash
curl http://localhost:8000/health
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@company.com\",\"password\":\"Admin@123456\"}"
```

You should get a JWT token in response.

---

## 🎯 Key Features Working

### ✅ Implemented & Working
- JWT Authentication with role-based access
- User Management (Admin, Manager, Customer roles)
- Product Catalog with inventory tracking
- Order Management with status tracking
- Automated inventory reduction on orders
- Low stock detection and alerts
- Restock request system
- Email automation for suppliers (when SMTP configured)
- Dashboard with real-time statistics
- MongoDB transactions for data consistency

### 📊 Dashboard Features
- **Admin**: Full system overview, user management, product catalog, inventory, orders, restock requests
- **Manager**: Inventory management, order dispatch, stock adjustments
- **Customer**: Product catalog, place orders, track deliveries, confirm delivery

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check Node.js version (requires 18+)
node --version

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### MongoDB connection error
- Check your internet connection
- Verify MongoDB Atlas cluster is running
- Check `.env` has correct MONGODB_URL

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` is set to `http://localhost:8000` in frontend

---

## 📧 Email Configuration (Optional)

To enable automated restock emails to suppliers:

1. Edit `backend-nodejs/.env`
2. Add your SMTP credentials:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

For Gmail, create an [App Password](https://myaccount.google.com/apppasswords).

---

## 🎮 Testing the Complete Flow

### 1. Login as Admin
- Go to http://localhost:5173
- Login with admin@company.com / Admin@123456

### 2. Create Products (if not seeded)
- Navigate to Products
- Click "Add Product"
- Fill in details with supplier email

### 3. Create Customer
- Navigate to Users
- Click "Create User"
- Select role: Customer
- Fill in shop details

### 4. Login as Customer
- Logout from admin
- Login with customer credentials
- View product catalog
- Place an order

### 5. Verify as Admin
- Login as admin again
- Check Orders section
- See inventory reduced automatically
- If stock < threshold, check Restock Requests
- Mark order as "Dispatched"

### 6. Confirm as Customer
- Login as customer
- View order tracking
- Click "Delivered" button

### 7. Check as Admin
- Login as admin
- See delivery confirmation in dashboard

---

## 📚 API Documentation

All API endpoints are documented in `backend-nodejs/README.md`

Key endpoints:
- `POST /api/auth/login` - Login
- `GET /api/products` - List products
- `POST /api/orders` - Place order
- `PUT /api/orders/:id/dispatch` - Dispatch order
- `PUT /api/orders/:id/deliver` - Confirm delivery
- `GET /api/dashboard/stats` - Dashboard statistics

---

## 🔒 Security Notes

- JWT tokens expire in 7 days
- Passwords are hashed with bcrypt
- Role-based access control on all sensitive endpoints
- Rate limiting enabled (100 requests per 15 minutes)
- CORS configured for localhost only

---

## 📝 Next Steps

1. Configure email for automated restock notifications
2. Customize product categories
3. Add more sample data
4. Deploy to production (see DEPLOYMENT_GUIDE.md)
5. Configure custom domain and SSL

---

## 💡 Production Deployment

When ready for production:

1. Set `NODE_ENV=production` in backend `.env`
2. Use a strong `JWT_SECRET`
3. Update `CORS_ORIGINS` with your production domain
4. Use environment variables for sensitive data
5. Enable MongoDB Atlas IP whitelist
6. Set up SSL/TLS certificates
7. Use PM2 or Docker for process management

---

## 🆘 Support

For issues:
1. Check backend logs in terminal
2. Check browser console for frontend errors
3. Verify MongoDB connection
4. Ensure all dependencies are installed
5. Check port 8000 is not in use by other apps

---

**Happy Coding! 🚀**

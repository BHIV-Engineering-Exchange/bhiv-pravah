# MongoDB Setup Guide

This project now supports **MongoDB** as the database backend, providing better scalability and flexibility compared to SQLite.

## Features

- ✅ **MongoDB Integration**: Full support for MongoDB as the primary database
- ✅ **Backward Compatible**: Can still use SQLite if needed
- ✅ **Easy Migration**: Scripts to migrate existing SQLite data to MongoDB
- ✅ **Unified API**: Same API interface regardless of database backend
- ✅ **Indexes**: Optimized indexes for fast queries
- ✅ **Sample Data**: Automatic initialization with sample data

## Quick Start

### 1. Install MongoDB

#### macOS (using Homebrew):
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Linux (Ubuntu/Debian):
```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
```

#### Windows:
Download and install from: https://www.mongodb.com/try/download/community

### 2. Configure Environment

Edit your `.env` file:

```bash
# Set database type to MongoDB
DATABASE_TYPE=mongodb

# MongoDB connection string (local)
MONGODB_URL=mongodb://localhost:27017/ai_crm_logistics

# Or use individual parameters
# MONGODB_HOST=localhost
# MONGODB_PORT=27017
# MONGODB_DATABASE=ai_crm_logistics
# MONGODB_USERNAME=
# MONGODB_PASSWORD=
```

### 3. Initialize MongoDB Database

Run the initialization script to create collections and sample data:

```bash
python init_mongodb.py
```

This will:
- Test MongoDB connection
- Create database indexes
- Add sample data for testing

### 4. Start the Application

```bash
# Start backend
cd backend
python -m uvicorn api_app:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

## MongoDB Atlas (Cloud)

To use MongoDB Atlas instead of local MongoDB:

1. Create a free account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get your connection string
4. Update `.env`:

```bash
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/ai_crm_logistics?retryWrites=true&w=majority
```

## Migration from SQLite

If you have existing data in SQLite and want to migrate to MongoDB:

```bash
python migrate_sqlite_to_mongodb.py
```

This will:
- Read all data from your SQLite database
- Create corresponding documents in MongoDB
- Preserve all relationships and data integrity

## Database Structure

### Collections

**Logistics:**
- `orders` - Customer orders
- `returns` - Product returns
- `restock_requests` - Automated restock requests
- `inventory` - Current stock levels
- `purchase_orders` - Supplier purchase orders
- `suppliers` - Supplier information
- `products` - Product catalog
- `shipments` - Delivery tracking
- `couriers` - Courier services
- `agent_logs` - AI agent action logs
- `human_reviews` - Pending human reviews

**CRM:**
- `accounts` - Customer accounts
- `contacts` - Contact persons
- `leads` - Sales leads
- `opportunities` - Sales opportunities
- `activities` - Activities and interactions
- `tasks` - Task management
- `notes` - Notes and comments
- `communication_logs` - Communication history

**System:**
- `users` - User authentication
- `alerts` - System alerts
- `kpi_metrics` - Performance metrics
- `notification_logs` - Notification history

## Switching Between Databases

To switch back to SQLite, simply change the `.env` file:

```bash
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///logistics_agent.db
```

The application will automatically use the appropriate database backend.

## API Usage

The API endpoints remain the same regardless of the database backend:

```python
# Example: Get all orders
GET /api/orders

# Example: Create a new account
POST /api/crm/accounts
{
  "name": "New Company",
  "account_type": "customer",
  "email": "contact@company.com"
}
```

## Performance Benefits

MongoDB offers several advantages:

- **Scalability**: Easily scale horizontally with sharding
- **Flexibility**: Schema-less design allows for evolving data models
- **Speed**: Faster read/write operations for large datasets
- **Replication**: Built-in replication for high availability
- **Aggregation**: Powerful aggregation framework for analytics

## Troubleshooting

### Connection Failed

```bash
# Check if MongoDB is running
# macOS
brew services list | grep mongodb

# Linux
sudo systemctl status mongod

# Test connection manually
mongosh "mongodb://localhost:27017/ai_crm_logistics"
```

### Permission Errors

If you get authentication errors:

```bash
# Create a user in MongoDB
mongosh
use ai_crm_logistics
db.createUser({
  user: "your_username",
  pwd: "your_password",
  roles: ["readWrite"]
})
```

Then update `.env`:
```bash
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
```

### Port Already in Use

If port 27017 is already in use:

```bash
# Find process using the port
lsof -i :27017

# Kill the process or use a different port
MONGODB_PORT=27018
```

## Backup and Restore

### Backup MongoDB Database

```bash
mongodump --db=ai_crm_logistics --out=backup/
```

### Restore MongoDB Database

```bash
mongorestore --db=ai_crm_logistics backup/ai_crm_logistics/
```

## Advanced Configuration

### Enable Authentication

```bash
# Start MongoDB with authentication
mongod --auth --dbpath /data/db
```

### Enable Replication

For production environments, set up a replica set:

```bash
mongod --replSet rs0
```

## Support

For issues or questions:
- Check MongoDB documentation: https://docs.mongodb.com/
- Open an issue on GitHub
- Contact the development team

## License

Same as the main project license (MIT)

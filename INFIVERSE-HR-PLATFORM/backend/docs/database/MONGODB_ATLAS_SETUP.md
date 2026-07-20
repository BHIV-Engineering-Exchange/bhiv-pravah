# 🗄️ MongoDB Atlas Setup Guide

## **MongoDB Atlas Cloud Database Configuration**
**Updated**: January 22, 2026  
**Version**: v4.3.0  
**Status**: ✅ Production Ready  

---

## 🚀 Getting Started with MongoDB Atlas

### **Step 1: Create MongoDB Atlas Account**
1. Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account
3. Verify your email address
4. Complete the onboarding process

### **Step 2: Create a New Cluster**
1. Click "Build a Database" on the MongoDB Atlas dashboard
2. Select "Shared" tier (free forever with limitations)
3. Choose cloud provider and region closest to your users
4. Select cluster tier (M0 for free tier)
5. Name your cluster (e.g., "bhiv-hr-cluster")
6. Click "Create Cluster"

### **Step 3: Database User Creation**
1. Navigate to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Built-in Role" and select "Atlas Admin"
4. Enter username and password (remember the password)
5. Click "Add User"

### **Step 4: Network Access Configuration**
1. Navigate to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
4. For production: Add specific IP addresses only
5. Click "Confirm"

### **Step 5: Get Connection String**
1. Click "Connect" on your cluster
2. Select "Drivers" option
3. Copy the connection string
4. Replace `<password>` with your database user password
5. Your connection string should look like:
   ```
   mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/bhiv_hr
   ```

---

## 🔧 Application Configuration

### **Environment Variables Setup**
Update your `.env` file with the MongoDB Atlas connection string:

```env
# Database (Replace with your actual MongoDB Atlas connection string)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/bhiv_hr

# Authentication Secrets
API_KEY_SECRET=<your-api-key>
JWT_SECRET_KEY=<your-jwt-secret>
CANDIDATE_JWT_SECRET_KEY=<your-candidate-jwt-secret>
GATEWAY_SECRET_KEY=<your-gateway-secret>

# Service URLs (Localhost)
GATEWAY_SERVICE_URL=http://localhost:8000
AGENT_SERVICE_URL=http://localhost:9000
LANGGRAPH_SERVICE_URL=http://localhost:9001
```

### **Connection Pool Configuration**
For optimal performance with MongoDB Atlas, configure your connection settings:

```python
# services/gateway/app/database.py
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI")

client = AsyncIOMotorClient(
    MONGODB_URI,
    maxPoolSize=10,          # Maximum connections in the pool
    minPoolSize=2,           # Minimum connections in the pool
    maxIdleTimeMS=30000,     # Close connections after 30 seconds of inactivity
    serverSelectionTimeoutMS=5000,  # Wait 5 seconds for server selection
    socketTimeoutMS=45000,   # Close sockets after 45 seconds of inactivity
    connectTimeoutMS=20000,  # Connect timeout
)

db = client.bhiv_hr
```

---

## 📋 Collections Schema

### **Core Application Collections**

#### **1. candidates Collection**
```javascript
{
    "_id": ObjectId("..."),
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "location": "San Francisco, CA",
    "experience_years": 5,
    "technical_skills": "Python, Django, FastAPI, MongoDB",
    "seniority_level": "Senior",
    "education_level": "Bachelor's",
    "resume_path": "/resumes/john_doe.pdf",
    "password_hash": "$2b$12$...",  // bcrypt hashed
    "status": "applied",  // applied, screening, interview, offer, hired, rejected
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes:**
- `email` (unique)
- `status`
- `location`, `experience_years` (compound)
- `technical_skills` (text index for search)

#### **2. jobs Collection**
```javascript
{
    "_id": ObjectId("..."),
    "title": "Senior Python Developer",
    "department": "Engineering",
    "location": "Remote",
    "experience_level": "Senior",
    "requirements": "Python, Django, FastAPI, MongoDB, REST APIs, 5+ years",
    "description": "We are looking for a senior Python developer...",
    "client_id": "client123",
    "employment_type": "Full-time",
    "status": "active",  // active, paused, closed, draft
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes:**
- `status`, `department` (compound)
- `client_id`, `status` (compound)
- `requirements` (text index for search)

#### **3. applications Collection**
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "cover_letter": "I am excited about this opportunity...",
    "status": "applied",  // applied, screening, interview, offer, hired, rejected, withdrawn
    "applied_date": ISODate("2026-01-22T10:00:00Z"),
    "last_updated": ISODate("2026-01-22T10:00:00Z"),
    "source": "portal",  // portal, referral, direct, etc.
    "notes": "Strong candidate with relevant experience",
    "created_at": ISODate("2026-01-22T10:00:00Z"),
    "updated_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes:**
- `candidate_id`, `status` (compound)
- `job_id`, `status` (compound)
- `applied_date` (descending)

#### **4. feedback Collection**
```javascript
{
    "_id": ObjectId("..."),
    "candidate_id": ObjectId("..."),
    "job_id": ObjectId("..."),
    "integrity": 5,  // 1-5 scale
    "honesty": 5,
    "discipline": 4,
    "hard_work": 5,
    "gratitude": 4,
    "average_score": 4.6,  // Calculated: (5+5+4+5+4)/5
    "comments": "Excellent candidate with strong values",
    "evaluator_id": ObjectId("..."),
    "evaluation_type": "interview",  // interview, assessment, reference
    "created_at": ISODate("2026-01-22T10:00:00Z")
}
```

**Indexes:**
- `candidate_id`, `job_id` (compound)
- `average_score` (descending)

---

## 🔒 Security Configuration

### **Database User Permissions**
For production environments, create specific database users with limited permissions:

```javascript
// Create users with specific roles
db.createUser({
  user: "gateway_user",
  pwd: passwordPrompt(),
  roles: [
    { role: "readWrite", db: "bhiv_hr" }
  ]
});

db.createUser({
  user: "agent_user",
  pwd: passwordPrompt(),
  roles: [
    { role: "readWrite", db: "bhiv_hr" }
  ]
});
```

### **Connection Security**
- Always use TLS/SSL connections (enabled by default with Atlas)
- Enable IP whitelisting for production clusters
- Use strong passwords for database users
- Regularly rotate database credentials

---

## 📊 Performance Optimization

### **Recommended Indexes**
```javascript
// Single field indexes
db.candidates.createIndex({ "email": 1 }, { unique: true })
db.candidates.createIndex({ "status": 1 })
db.jobs.createIndex({ "status": 1 })
db.clients.createIndex({ "client_id": 1 }, { unique: true })

// TTL indexes for automatic cleanup
db.rate_limits.createIndex({ "created_at": 1 }, { expireAfterSeconds: 3600 }) // 1 hour
db.matching_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 86400 }) // 24 hours

// Compound indexes
db.candidates.createIndex({ "location": 1, "experience_years": 1 })
db.jobs.createIndex({ "status": 1, "department": 1 })
db.feedback.createIndex({ "candidate_id": 1, "job_id": 1 })
db.applications.createIndex({ "candidate_id": 1, "status": 1 })
db.applications.createIndex({ "job_id": 1, "status": 1 })

// Text indexes for search
db.candidates.createIndex({ "technical_skills": "text" })
db.jobs.createIndex({ "requirements": "text", "description": "text" })
```

### **Connection Pool Settings**
Optimize your application's connection pooling for MongoDB Atlas:

```javascript
const client = new MongoClient(MONGODB_URI, {
  maxPoolSize: 10,          // Maintain up to 10 socket connections
  minPoolSize: 2,           // Maintain at least 2 socket connections
  maxIdleTimeMS: 30000,     // Close sockets after 30 seconds of inactivity
  serverSelectionTimeoutMS: 5000,  // Wait 5 seconds for server selection
  socketTimeoutMS: 45000,   // Close sockets after 45 seconds of inactivity
  connectTimeoutMS: 20000,  // Give up initial connection after 20 seconds
  retryWrites: true,        // Enable retryable writes
  retryReads: true          // Enable retryable reads
});
```

---

## 🛠️ Troubleshooting

### **Common Connection Issues**

#### **Connection Timeout**
- Verify your IP address is whitelisted in Network Access
- Check firewall settings on your local machine
- Ensure the connection string is correct

#### **Authentication Failure**
- Confirm the username and password are correct
- Verify the database user exists and has proper permissions
- Check that the database name in the connection string is correct

#### **Slow Queries**
- Ensure proper indexes are created for your queries
- Use explain() to analyze query performance
- Consider optimizing your aggregation pipelines

### **Testing Connection**
```bash
# Test MongoDB connection
mongo "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/bhiv_hr" --eval "db.runCommand({serverStatus: 1})"

# Test from application
python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    client = AsyncIOMotorClient('your_connection_string')
    await client.admin.command('ping')
    print('Connected successfully!')
    client.close()

asyncio.run(test_connection())
"
```

---

## 📈 Monitoring & Maintenance

### **Atlas Dashboard Metrics**
Monitor these key metrics in your MongoDB Atlas dashboard:
- Connections: Should remain within cluster limits
- Operations: Read/Write operations per second
- Queue Depth: Number of queued operations
- Database Size: Storage utilization
- Index Size: Memory usage for indexes

### **Backup Configuration**
MongoDB Atlas provides automatic backups. Configure backup settings:
- Backup frequency and retention policies
- Point-in-time recovery options
- Automated backup verification

### **Alert Configuration**
Set up alerts for:
- Connection failures
- Slow queries
- High memory usage
- Disk space warnings
- Failed authentication attempts

---

**BHIV HR Platform MongoDB Atlas Setup Guide** - Complete configuration for production-ready MongoDB Atlas deployment with security, performance, and monitoring.

*Built with Integrity, Honesty, Discipline, Hard Work & Gratitude*

**Last Updated**: January 22, 2026 | **Status**: ✅ Production Ready | **Database**: MongoDB Atlas | **Security**: TLS Encrypted | **Backups**: Automated
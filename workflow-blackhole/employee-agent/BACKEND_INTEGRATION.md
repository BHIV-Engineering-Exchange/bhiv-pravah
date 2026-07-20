# Backend Integration Guide

This guide helps you implement the required API endpoints in your Node.js/Express backend to support the Employee Activity Agent.

## Required Endpoints

The agent requires these four endpoints:

1. `POST /api/agent/login` - Authenticate agent
2. `POST /api/attendance/start` - Start work day
3. `POST /api/attendance/end` - End work day
4. `POST /api/activity/ingest` - Receive activity data

## Database Schema

### User Model
Already exists in your system. Ensure it has:
```javascript
{
  email: String,
  password: String, // hashed
  role: String,
  // ... other fields
}
```

### Attendance Model
You should already have this for start/end day tracking:
```javascript
{
  userId: ObjectId,
  date: Date,
  startTime: Date,
  endTime: Date,
  status: String, // 'active', 'ended'
  // ... other fields
}
```

### Activity Model (NEW)
Create this model for agent data:
```javascript
const activitySchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  attendanceId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Attendance',
    required: true
  },
  timestamp: {
    type: Date,
    required: true,
    default: Date.now
  },
  mouseEvents: {
    type: Number,
    default: 0
  },
  keyboardEvents: {
    type: Number,
    default: 0
  },
  idleSeconds: {
    type: Number,
    default: 0
  },
  activeApp: {
    type: String,
    default: 'Unknown'
  },
  intervalDuration: {
    type: Number,
    default: 30 // seconds
  }
}, {
  timestamps: true
});

// Index for efficient queries
activitySchema.index({ userId: 1, timestamp: -1 });
activitySchema.index({ attendanceId: 1 });

module.exports = mongoose.model('Activity', activitySchema);
```

## Endpoint Implementation

### 1. POST /api/agent/login

Authenticate the employee and return a JWT token.

```javascript
// routes/agentRoutes.js
const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password are required'
      });
    }

    // Find user
    const user = await User.findOne({ email: email.toLowerCase() });
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Check if user is active (optional)
    if (user.status && user.status !== 'active') {
      return res.status(403).json({
        success: false,
        message: 'Account is not active'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      { 
        userId: user._id,
        email: user.email,
        role: user.role
      },
      process.env.JWT_SECRET,
      { expiresIn: '7d' } // Token valid for 7 days
    );

    // Return success
    res.json({
      success: true,
      token,
      user: {
        id: user._id,
        email: user.email,
        username: user.username,
        role: user.role
      }
    });

  } catch (error) {
    console.error('Agent login error:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
});

module.exports = router;
```

### 2. POST /api/attendance/start

Start a new attendance record.

```javascript
// routes/attendanceRoutes.js
const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const Attendance = require('../models/Attendance');

router.post('/start', authMiddleware, async (req, res) => {
  try {
    const userId = req.user.userId; // From JWT middleware
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Check if day already started
    const existingAttendance = await Attendance.findOne({
      userId,
      date: { $gte: today },
      status: 'active'
    });

    if (existingAttendance) {
      return res.json({
        success: true,
        message: 'Day already started',
        attendanceId: existingAttendance._id,
        attendance: existingAttendance
      });
    }

    // Create new attendance record
    const attendance = new Attendance({
      userId,
      date: new Date(),
      startTime: new Date(),
      status: 'active'
    });

    await attendance.save();

    res.json({
      success: true,
      message: 'Day started successfully',
      attendanceId: attendance._id,
      attendance
    });

  } catch (error) {
    console.error('Start day error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to start day'
    });
  }
});

module.exports = router;
```

### 3. POST /api/attendance/end

End the active attendance record.

```javascript
// routes/attendanceRoutes.js (continued)

router.post('/end', authMiddleware, async (req, res) => {
  try {
    const userId = req.user.userId;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Find active attendance
    const attendance = await Attendance.findOne({
      userId,
      date: { $gte: today },
      status: 'active'
    });

    if (!attendance) {
      return res.status(400).json({
        success: false,
        message: 'No active day found'
      });
    }

    // Update attendance
    attendance.endTime = new Date();
    attendance.status = 'ended';
    
    // Calculate total hours (optional)
    const duration = attendance.endTime - attendance.startTime;
    attendance.totalHours = duration / (1000 * 60 * 60);

    await attendance.save();

    res.json({
      success: true,
      message: 'Day ended successfully',
      attendance
    });

  } catch (error) {
    console.error('End day error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to end day'
    });
  }
});
```

### 4. POST /api/activity/ingest

Receive and store activity data from the agent.

```javascript
// routes/activityRoutes.js
const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const Activity = require('../models/Activity');
const Attendance = require('../models/Attendance');

router.post('/ingest', authMiddleware, async (req, res) => {
  try {
    const userId = req.user.userId;
    const {
      attendanceId,
      timestamp,
      mouseEvents,
      keyboardEvents,
      idleSeconds,
      activeApp,
      intervalDuration
    } = req.body;

    // Validate required fields
    if (!attendanceId) {
      return res.status(400).json({
        success: false,
        message: 'Attendance ID is required'
      });
    }

    // Verify attendance exists and is active
    const attendance = await Attendance.findById(attendanceId);
    if (!attendance) {
      return res.status(404).json({
        success: false,
        message: 'Attendance record not found'
      });
    }

    if (attendance.userId.toString() !== userId) {
      return res.status(403).json({
        success: false,
        message: 'Attendance record does not belong to this user'
      });
    }

    if (attendance.status !== 'active') {
      return res.status(400).json({
        success: false,
        message: 'Attendance day is not active. Please start your day first.'
      });
    }

    // Create activity record
    const activity = new Activity({
      userId,
      attendanceId,
      timestamp: timestamp || new Date(),
      mouseEvents: mouseEvents || 0,
      keyboardEvents: keyboardEvents || 0,
      idleSeconds: idleSeconds || 0,
      activeApp: activeApp || 'Unknown',
      intervalDuration: intervalDuration || 30
    });

    await activity.save();

    // Optional: Update last activity time on attendance
    attendance.lastActivityTime = new Date();
    await attendance.save();

    res.json({
      success: true,
      message: 'Activity data ingested successfully'
    });

  } catch (error) {
    console.error('Activity ingestion error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to ingest activity data'
    });
  }
});

module.exports = router;
```

## Authentication Middleware

```javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

module.exports = function authMiddleware(req, res, next) {
  try {
    // Get token from header
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'No token provided'
      });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Attach user info to request
    req.user = decoded;
    
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token expired'
      });
    }
    
    return res.status(401).json({
      success: false,
      message: 'Invalid token'
    });
  }
};
```

## Register Routes

```javascript
// index.js or app.js
const agentRoutes = require('./routes/agentRoutes');
const attendanceRoutes = require('./routes/attendanceRoutes');
const activityRoutes = require('./routes/activityRoutes');

// Register routes
app.use('/api/agent', agentRoutes);
app.use('/api/attendance', attendanceRoutes);
app.use('/api/activity', activityRoutes);
```

## Testing Endpoints

### Using cURL

```bash
# 1. Login
curl -X POST http://localhost:5000/api/agent/login \
  -H "Content-Type: application/json" \
  -d '{"email":"employee@company.com","password":"<your_password>"}'

# Response: {"success":true,"token":"eyJhbGc...","user":{...}}

# 2. Start Day (use token from login)
curl -X POST http://localhost:5000/api/attendance/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Response: {"success":true,"attendanceId":"..."}

# 3. Ingest Activity
curl -X POST http://localhost:5000/api/activity/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "attendanceId": "ATTENDANCE_ID_FROM_START",
    "mouseEvents": 100,
    "keyboardEvents": 50,
    "idleSeconds": 10,
    "activeApp": "Visual Studio Code",
    "intervalDuration": 30
  }'

# 4. End Day
curl -X POST http://localhost:5000/api/attendance/end \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman

Import the collection from `/postman_collection.json` (if you create one) or create requests manually:

1. Create a new collection "Employee Agent API"
2. Add environment with `baseUrl` variable
3. Create requests for each endpoint
4. Use `{{token}}` variable for auth header

## Analytics & Reporting

### Query Activity Data

```javascript
// Get activity summary for a user on a specific day
router.get('/activity/summary/:userId/:date', authMiddleware, async (req, res) => {
  try {
    const { userId, date } = req.params;
    const startOfDay = new Date(date);
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(date);
    endOfDay.setHours(23, 59, 59, 999);

    const activities = await Activity.find({
      userId,
      timestamp: { $gte: startOfDay, $lte: endOfDay }
    }).sort({ timestamp: 1 });

    const summary = {
      totalMouseEvents: activities.reduce((sum, a) => sum + a.mouseEvents, 0),
      totalKeyboardEvents: activities.reduce((sum, a) => sum + a.keyboardEvents, 0),
      totalIdleSeconds: activities.reduce((sum, a) => sum + a.idleSeconds, 0),
      recordCount: activities.length,
      activities
    };

    res.json({ success: true, summary });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Set secure JWT expiration** (7-30 days max)
3. **Rate limit API endpoints** (use `express-rate-limit`)
4. **Validate all inputs** (use `express-validator`)
5. **Log authentication attempts**
6. **Monitor for unusual activity patterns**

## CORS Configuration

```javascript
// For agent to connect from Electron
const cors = require('cors');

app.use(cors({
  origin: '*', // In production, be more specific
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

## Environment Variables

```env
# Add to your .env file
JWT_SECRET=your-super-secret-jwt-key-change-this
NODE_ENV=production
PORT=5000
MONGODB_URI=mongodb+srv://...
```

## Deployment Checklist

- [ ] Activity model created and migrated
- [ ] All four endpoints implemented
- [ ] Authentication middleware working
- [ ] JWT secret set in environment
- [ ] HTTPS enabled (via Render or reverse proxy)
- [ ] CORS configured correctly
- [ ] Database indexes created
- [ ] Error logging set up
- [ ] Rate limiting enabled
- [ ] Tested with actual Electron agent

## Next Steps

1. Implement the endpoints in your backend
2. Test with cURL or Postman
3. Update agent `.env` with your backend URL
4. Test agent connection
5. Monitor logs for any issues
6. Build dashboard to view activity data

# 🗄️ BHIV HR Platform - Essential MongoDB Queries

## **MongoDB Quick Reference & Monitoring Queries**
**Updated**: January 22, 2026  
**Version**: v4.3.0 (Schema v4.3.0)  
**Status**: ✅ Production Ready - MongoDB Connection Operational  
**Collections**: 17+ total  
**Services**: 3 core microservices with 111 endpoints  

---

## 📊 SYSTEM OVERVIEW
- Services: Gateway (80), Agent (6), LangGraph (25)
- Database: MongoDB Atlas with 17+ collections and 75+ indexes
- Features: RL integration, multi-channel communication, enterprise security
- Performance: <50ms query response, <0.02s AI matching
- Recent Fix: MongoDB connection resolved (January 22, 2026)

---

## 🔍 COLLECTION VERIFICATION & HEALTH CHECKS

### Current database information
```javascript
// Get database stats
db.stats()

// Get all collection names
db.getCollectionNames()

// Get collection stats for each collection
db.candidates.stats()
db.jobs.stats()
db.applications.stats()
db.feedback.stats()
db.interviews.stats()
db.offers.stats()
db.users.stats()
db.clients.stats()
db.audit_logs.stats()
db.rate_limits.stats()
db.notifications.stats()
db.ml_feedback.stats()
db.performance_metrics.stats()
```

### Database health and performance summary
```javascript
// Get overall database information
{
  database_name: "bhiv_hr",
  collections_count: db.getCollectionNames().length,
  total_documents: db.candidates.countDocuments() + 
                  db.jobs.countDocuments() + 
                  db.applications.countDocuments() +
                  db.feedback.countDocuments() +
                  db.interviews.countDocuments() +
                  db.offers.countDocuments() +
                  db.users.countDocuments() +
                  db.clients.countDocuments(),
  storage_size: db.stats().storageSize,
  avg_obj_size: db.stats().avgObjSize,
  indexes_count: db.stats().indexes
}
```

---

## 📊 DATA OVERVIEW & STATISTICS

### Comprehensive data counts with growth metrics
```javascript
// Get counts for all major collections
[
  {
    collection: "candidates",
    count: db.candidates.countDocuments(),
    latest_record: db.candidates.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.candidates.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "jobs",
    count: db.jobs.countDocuments(),
    latest_record: db.jobs.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.jobs.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "applications",
    count: db.applications.countDocuments(),
    latest_record: db.applications.findOne({}, { sort: { applied_date: -1 } }),
    earliest_record: db.applications.findOne({}, { sort: { applied_date: 1 } })
  },
  {
    collection: "feedback",
    count: db.feedback.countDocuments(),
    latest_record: db.feedback.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.feedback.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "interviews",
    count: db.interviews.countDocuments(),
    latest_record: db.interviews.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.interviews.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "offers",
    count: db.offers.countDocuments(),
    latest_record: db.offers.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.offers.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "users",
    count: db.users.countDocuments(),
    latest_record: db.users.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.users.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "clients",
    count: db.clients.countDocuments(),
    latest_record: db.clients.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.clients.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "audit_logs",
    count: db.audit_logs.countDocuments(),
    latest_record: db.audit_logs.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.audit_logs.findOne({}, { sort: { created_at: 1 } })
  },
  {
    collection: "ml_feedback",
    count: db.ml_feedback.countDocuments(),
    latest_record: db.ml_feedback.findOne({}, { sort: { created_at: -1 } }),
    earliest_record: db.ml_feedback.findOne({}, { sort: { created_at: 1 } })
  }
]
```

### Production data validation summary
```javascript
{
  section: "Production Data Summary",
  total_candidates: db.candidates.countDocuments(),
  active_jobs: db.jobs.countDocuments({ status: "active" }),
  active_clients: db.clients.countDocuments({ status: "active" }),
  total_assessments: db.feedback.countDocuments(),
  total_ml_feedback: db.ml_feedback.countDocuments(),
  avg_bhiv_score: db.feedback.aggregate([
    { $group: { _id: null, avg_score: { $avg: "$average_score" } } }
  ]).toArray()[0]?.avg_score || 0
}
```

---

## 👥 CANDIDATES ANALYSIS & INSIGHTS

### Top candidates with comprehensive metrics
```javascript
db.candidates.aggregate([
  {
    $lookup: {
      from: "feedback",
      localField: "_id",
      foreignField: "candidate_id",
      as: "feedback_docs"
    }
  },
  {
    $lookup: {
      from: "interviews",
      localField: "_id",
      foreignField: "candidate_id",
      as: "interview_docs"
    }
  },
  {
    $lookup: {
      from: "offers",
      localField: "_id",
      foreignField: "candidate_id",
      as: "offer_docs"
    }
  },
  {
    $lookup: {
      from: "applications",
      localField: "_id",
      foreignField: "candidate_id",
      as: "application_docs"
    }
  },
  {
    $lookup: {
      from: "matching_cache",
      localField: "_id",
      foreignField: "candidate_id",
      as: "match_docs"
    }
  },
  {
    $addFields: {
      feedback_count: { $size: "$feedback_docs" },
      interview_count: { $size: "$interview_docs" },
      offer_count: { $size: "$offer_docs" },
      application_count: { $size: "$application_docs" },
      best_ai_match: { $max: "$match_docs.score" }
    }
  },
  {
    $addFields: {
      performance_tier: {
        $switch: {
          branches: [
            { case: { $gte: ["$average_score", 4.5] }, then: "⭐ Excellent" },
            { case: { $gte: ["$average_score", 4.0] }, then: "🌟 Very Good" },
            { case: { $gte: ["$average_score", 3.5] }, then: "✨ Good" },
            { case: { $gte: ["$average_score", 3.0] }, then: "📈 Average" },
            { case: { $gt: ["$average_score", 0] }, then: "📉 Below Average" }
          ],
          default: "❓ Not Assessed"
        }
      }
    }
  },
  {
    $sort: { average_score: -1, created_at: -1 }
  },
  {
    $limit: 25
  },
  {
    $project: {
      name: 1,
      email: 1,
      location: 1,
      experience_years: 1,
      seniority_level: 1,
      bhiv_score: "$average_score",
      status: 1,
      feedback_count: 1,
      interview_count: 1,
      offer_count: 1,
      application_count: 1,
      best_ai_match: 1,
      created_at: 1,
      performance_tier: 1
    }
  }
])
```

### Candidate distribution analytics
```javascript
// Location distribution
db.candidates.aggregate([
  {
    $match: { location: { $exists: true, $ne: null } }
  },
  {
    $group: {
      _id: "$location",
      count: { $sum: 1 },
      avg_experience: { $avg: "$experience_years" },
      avg_bhiv_score: { $avg: "$average_score" }
    }
  },
  {
    $addFields: {
      percentage: {
        $round: [
          { $multiply: [{ $divide: ["$count", { $sum: "$count" }] }, 100] },
          2
        ]
      }
    }
  },
  {
    $sort: { count: -1 }
  },
  {
    $project: {
      location: "$_id",
      count: 1,
      percentage: 1,
      avg_experience: 1,
      avg_bhiv_score: 1
    }
  }
])

// Experience level distribution
db.candidates.aggregate([
  {
    $group: {
      _id: {
        $switch: {
          branches: [
            { case: { $gte: ["$experience_years", 10] }, then: "Senior (10+ years)" },
            { case: { $gte: ["$experience_years", 5] }, then: "Mid-Level (5-9 years)" },
            { case: { $gte: ["$experience_years", 2] }, then: "Junior (2-4 years)" }
          ],
          default: "Entry Level (0-1 years)"
        }
      },
      count: { $sum: 1 },
      avg_bhiv_score: { $avg: "$average_score" }
    }
  },
  {
    $addFields: {
      percentage: {
        $round: [
          { $multiply: [{ $divide: ["$count", { $sum: "$count" }] }, 100] },
          2
        ]
      }
    }
  },
  {
    $sort: { count: -1 }
  },
  {
    $project: {
      experience_level: "$_id",
      count: 1,
      percentage: 1,
      avg_bhiv_score: 1
    }
  }
])
```

---

## 💼 JOBS ANALYSIS & INSIGHTS

### Active jobs with detailed metrics
```javascript
db.jobs.aggregate([
  {
    $match: { status: "active" }
  },
  {
    $lookup: {
      from: "applications",
      localField: "_id",
      foreignField: "job_id",
      as: "application_docs"
    }
  },
  {
    $lookup: {
      from: "feedback",
      localField: "_id",
      foreignField: "job_id",
      as: "feedback_docs"
    }
  },
  {
    $addFields: {
      application_count: { $size: "$application_docs" },
      feedback_count: { $size: "$feedback_docs" },
      avg_feedback_score: { $avg: "$feedback_docs.average_score" }
    }
  },
  {
    $sort: { application_count: -1, created_at: -1 }
  },
  {
    $project: {
      title: 1,
      department: 1,
      location: 1,
      experience_level: 1,
      requirements: 1,
      description: 1,
      client_id: 1,
      application_count: 1,
      feedback_count: 1,
      avg_feedback_score: 1,
      created_at: 1,
      updated_at: 1
    }
  }
])
```

---

## 🎯 MATCHING & RECOMMENDATIONS

### Top AI matches for a specific job
```javascript
db.matching_cache.aggregate([
  {
    $match: { 
      job_id: ObjectId("..."), // Replace with actual job ID
      expires_at: { $gt: new Date() } // Only valid cache entries
    }
  },
  {
    $lookup: {
      from: "candidates",
      localField: "candidate_id",
      foreignField: "_id",
      as: "candidate_info"
    }
  },
  {
    $unwind: "$candidate_info"
  },
  {
    $sort: { score: -1 }
  },
  {
    $limit: 10
  },
  {
    $project: {
      candidate_id: 1,
      candidate_name: "$candidate_info.name",
      candidate_email: "$candidate_info.email",
      match_score: 1,
      skills_match_score: 1,
      experience_match_score: 1,
      location_match_score: 1,
      values_alignment_score: 1,
      algorithm_version: 1,
      reasoning: 1,
      cached_at: 1,
      expires_at: 1
    }
  }
])
```

---

## 📈 REINFORCEMENT LEARNING ANALYTICS

### ML feedback and performance metrics
```javascript
db.ml_feedback.aggregate([
  {
    $group: {
      _id: "$feedback_source",
      total_feedback: { $sum: 1 },
      avg_reward: { $avg: "$reward_signal" },
      avg_feedback_score: { $avg: "$feedback_score" }
    }
  },
  {
    $sort: { total_feedback: -1 }
  },
  {
    $project: {
      feedback_source: "$_id",
      total_feedback: 1,
      avg_reward: 1,
      avg_feedback_score: 1
    }
  }
])
```

### RL model performance tracking
```javascript
db.performance_metrics.aggregate([
  {
    $match: { 
      metric_name: { $regex: /model|accuracy|precision|recall|f1/i }
    }
  },
  {
    $sort: { timestamp: -1 }
  },
  {
    $limit: 20
  }
])
```

---

## 🔒 SECURITY & AUDIT LOGS

### Recent audit activity
```javascript
db.audit_logs.aggregate([
  {
    $sort: { created_at: -1 }
  },
  {
    $limit: 50
  },
  {
    $project: {
      collection_name: 1,
      operation: 1,
      document_id: 1,
      user_id: 1,
      user_type: 1,
      ip_address: 1,
      endpoint: 1,
      created_at: 1
    }
  }
])
```

### Security violations monitoring
```javascript
db.audit_logs.aggregate([
  {
    $match: {
      created_at: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } // Last 7 days
    }
  },
  {
    $group: {
      _id: {
        ip_address: "$ip_address",
        operation: "$operation"
      },
      count: { $sum: 1 },
      first_occurrence: { $min: "$created_at" },
      last_occurrence: { $max: "$created_at" }
    }
  },
  {
    $match: { count: { $gt: 10 } } // More than 10 occurrences
  },
  {
    $sort: { count: -1 }
  }
])
```

---

## ⚡ PERFORMANCE MONITORING

### Rate limiting analysis
```javascript
db.rate_limits.aggregate([
  {
    $match: {
      created_at: { $gte: new Date(Date.now() - 60 * 60 * 1000) } // Last hour
    }
  },
  {
    $group: {
      _id: {
        ip_address: "$ip_address",
        endpoint: "$endpoint"
      },
      total_requests: { $sum: "$request_count" },
      windows: { $sum: 1 },
      is_blocked: { $max: "$is_blocked" }
    }
  },
  {
    $sort: { "total_requests": -1 }
  },
  {
    $limit: 20
  }
])
```

### System performance metrics
```javascript
db.performance_metrics.aggregate([
  {
    $match: {
      timestamp: { $gte: new Date(Date.now() - 24 * 60 * 60 * 1000) } // Last 24 hours
    }
  },
  {
    $group: {
      _id: {
        metric_name: "$metric_name",
        source_service: "$source_service"
      },
      avg_value: { $avg: "$value" },
      min_value: { $min: "$value" },
      max_value: { $max: "$value" },
      count: { $sum: 1 }
    }
  },
  {
    $sort: { "avg_value": -1 }
  }
])
```
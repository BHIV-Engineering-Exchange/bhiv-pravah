# KarmaChain API Endpoint Examples

## Main Application Endpoints

### Health Check
- **Endpoint**: `GET /health`
- **Example Response**:
```json
{
  "status": "healthy"
}
```

## Legacy Karma API (api/v1)

### Get Karma Profile
- **Endpoint**: `GET /api/v1/karma/{user_id}`
- **Example Request**: `GET /api/v1/karma/Siddhesh_2004`
- **Example Response**:
```json
{
  "user_id": "Siddhesh_2004",
  "role": "learner",
  "merit_score": 15.5,
  "paap_score": 2.0,
  "net_karma": 13.5,
  "weighted_karma_score": 18.2,
  "balances": {
    "DharmaPoints": 25,
    "SevaPoints": 10,
    "PunyaTokens": 0,
    "PaapTokens": {
      "minor": 2,
      "medium": 0,
      "maha": 0
    }
  },
  "action_stats": {
    "total_actions": 5,
    "pending_atonements": 0,
    "completed_atonements": 0
  },
  "corrective_guidance": [],
  "module_scores": {
    "finance": 15.0,
    "insightflow": 62.5,
    "gurukul": 42.5,
    "game": 31.5
  },
  "last_updated": "2026-01-14T13:14:27.123456+00:00"
}
```

### Log Action
- **Endpoint**: `POST /api/v1/log-action/`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "action": "completing_lessons",  // Must be one of: completing_lessons, helping_peers, solving_doubts, selfless_service, cheat
  "role": "learner",               // Must be one of: learner, volunteer, seva, guru
  "intensity": 1.0,                // Optional, default 1.0
  "context": "karma_learning_module", // Optional
  "metadata": {                    // Optional
    "session_duration": "30 minutes",
    "topic_covered": "karma_fundamentals"
  }
}
```

### Submit Atonement
- **Endpoint**: `POST /api/v1/submit-atonement/`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "plan_id": "atonement_plan_123",
  "atonement_type": "Jap",         // Must be one of: Jap, Tap, Bhakti, Daan
  "amount": 108.0,
  "proof_text": "Completed 108 repetitions of mantra", // Optional
  "tx_hash": "abc123def456"        // Optional
}
```

## Version 1 Karma API (/v1/)

### Log Action (V1)
- **Endpoint**: `POST /v1/log-action/`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "action": "helping_peers",       // Must be one of: completing_lessons, helping_peers, solving_doubts, selfless_service, cheat
  "role": "volunteer",             // Must be one of: learner, volunteer, seva, guru
  "note": "Assisted fellow students with doubts",
  "context": "gurukul_session",
  "metadata": {
    "duration": "45 minutes",
    "students_helped": 3
  },
  "affected_user_id": "student_123",        // Optional
  "relationship_description": "mentor-student" // Optional
}
```

### Submit Appeal (V1)
- **Endpoint**: `POST /v1/log-action/appeal`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "reason": "Dispute on penalty received",
  "evidence": "Evidence supporting the appeal",
  "target_action": "cheat_penalty"
}
```

### Submit Atonement (V1)
- **Endpoint**: `POST /v1/log-action/atonement`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "plan_id": "plan_456",
  "atonement_type": "Tap",         // Must be one of: Jap, Tap, Bhakti, Daan
  "amount": 1.0,
  "proof_text": "Completed day of fasting",
  "context": "atonement_completion"
}
```

### Process Death Event (V1)
- **Endpoint**: `POST /v1/log-action/death`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "reason": "Reached death threshold",
  "loka_destination": "Mrityuloka" // Must be one of: Swarga, Mrityuloka, Antarloka, Naraka
}
```

## Wallet Operations

### View Balance
- **Endpoint**: `GET /balance/view-balance/{user_id}`
- **Example Request**: `GET /balance/view-balance/Siddhesh_2004`
- **Example Response**:
```json
{
  "user_id": "Siddhesh_2004",
  "role": "learner",
  "balances": {
    "DharmaPoints": 25,
    "SevaPoints": 10,
    "PunyaTokens": 0,
    "PaapTokens": {
      "minor": 2,
      "medium": 0,
      "maha": 0
    }
  },
  "merit_score": 15.5,
  "token_attributes": {
    "DharmaPoints": {
      "expiry_days": 365,
      "stackable": true,
      "daily_decay": 0.0
    },
    "SevaPoints": {
      "expiry_days": 365,
      "stackable": true,
      "daily_decay": 0.0005
    },
    "PunyaTokens": {
      "expiry_days": 730,
      "stackable": true,
      "daily_decay": 0.0001
    }
  }
}
```

### Redeem Tokens
- **Endpoint**: `POST /redeem/`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "token_type": "DharmaPoints",   // Must be one of: DharmaPoints, SevaPoints, PunyaTokens, PaapTokens.minor, etc.
  "amount": 5.0
}
```

### Get Best Policy
- **Endpoint**: `GET /policy/`
- **Example Response**:
```json
{
  "best_policy": {
    "learner": "completing_lessons",
    "volunteer": "helping_peers",
    "seva": "selfless_service",
    "guru": "selfless_service"
  },
  "Q_shape": [4, 5]
}
```

## Rnanubandhan API

### Get Rnanubandhan Network
- **Endpoint**: `GET /api/v1/rnanubandhan/{user_id}`
- **Example Request**: `GET /api/v1/rnanubandhan/Siddhesh_2004`
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "network_summary": {
    "total_debts": 1,
    "total_credits": 0,
    "outstanding_amount": 2.5
  },
  "debts": [
    {
      "relationship_id": "debt_123",
      "debtor_id": "Siddhesh_2004",
      "creditor_id": "other_user_456",
      "amount": 2.5,
      "severity": "minor",
      "status": "active",
      "created_at": "2026-01-14T10:00:00Z"
    }
  ],
  "credits": []
}
```

### Get User Debts
- **Endpoint**: `GET /api/v1/rnanubandhan/{user_id}/debts`
- **Example Request**: `GET /api/v1/rnanubandhan/Siddhesh_2004/debts`
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "debts": [
    {
      "relationship_id": "debt_123",
      "creditor_id": "other_user_456",
      "amount": 2.5,
      "severity": "minor",
      "status": "active",
      "description": "Helped with assignment",
      "created_at": "2026-01-14T10:00:00Z"
    }
  ]
}
```

### Get User Credits
- **Endpoint**: `GET /api/v1/rnanubandhan/{user_id}/credits`
- **Example Request**: `GET /api/v1/rnanubandhan/Siddhesh_2004/credits`
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "credits": []
}
```

### Create Debt Relationship
- **Endpoint**: `POST /api/v1/rnanubandhan/create-debt`
- **Example Request**:
```json
{
  "debtor_id": "Siddhesh_2004",
  "receiver_id": "other_user_456",
  "action_type": "helping_peers",
  "severity": "minor",             // Must be one of: minor, medium, maha
  "amount": 2.5,
  "description": "Received help with assignment"  // Optional
}
```

### Repay Debt
- **Endpoint**: `POST /api/v1/rnanubandhan/repay-debt`
- **Example Request**:
```json
{
  "relationship_id": "debt_123",
  "amount": 2.5,
  "repayment_method": "atonement"  // Optional, default "atonement"
}
```

### Transfer Debt
- **Endpoint**: `POST /api/v1/rnanubandhan/transfer-debt`
- **Example Request**:
```json
{
  "relationship_id": "debt_123",
  "new_debtor_id": "another_user_789"
}
```

### Get Specific Relationship
- **Endpoint**: `GET /api/v1/rnanubandhan/relationship/{relationship_id}`
- **Example Request**: `GET /api/v1/rnanubandhan/relationship/debt_123`
- **Example Response**:
```json
{
  "status": "success",
  "relationship": {
    "relationship_id": "debt_123",
    "debtor_id": "Siddhesh_2004",
    "creditor_id": "other_user_456",
    "amount": 2.5,
    "severity": "minor",
    "status": "active",
    "description": "Received help with assignment",
    "created_at": "2026-01-14T10:00:00Z"
  }
}
```

## Agami Karma API

### Predict Future Karma
- **Endpoint**: `POST /api/v1/agami/predict`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "scenario": {
    "environment": "gurukul",
    "actions": ["completing_lessons", "helping_peers"],
    "duration": "1 week"
  }
}
```

### Get User Prediction
- **Endpoint**: `GET /api/v1/agami/user/{user_id}`
- **Example Request**: `GET /api/v1/agami/user/Siddhesh_2004`
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "prediction": {
    "expected_karma_growth": 5.2,
    "risk_factors": ["low_activity"],
    "recommendations": ["increase_helping_peers", "focus_on_selfless_service"],
    "confidence": 0.85
  }
}
```

### Update Context Weights
- **Endpoint**: `POST /api/v1/agami/context-weights`
- **Example Request**:
```json
{
  "context_key": "gurukul_student",
  "weights": {
    "Dharma": 1.2,
    "Artha": 1.0,
    "Kama": 0.8,
    "Moksha": 1.5
  }
}
```

### Get Context Weights
- **Endpoint**: `GET /api/v1/agami/context-weights/{context_key}`
- **Example Request**: `GET /api/v1/agami/context-weights/gurukul_student`
- **Example Response**:
```json
{
  "status": "success",
  "context_key": "gurukul_student",
  "weights": {
    "Dharma": 1.2,
    "Artha": 1.0,
    "Kama": 0.8,
    "Moksha": 1.5
  }
}
```

### Get Sample Scenarios
- **Endpoint**: `GET /api/v1/agami/scenarios`
- **Example Response**:
```json
{
  "status": "success",
  "scenarios": {
    "student_in_gurukul": {
      "context": {
        "environment": "gurukul",
        "role": "student",
        "goal": "learning"
      },
      "description": "Student performing Artha actions in Gurukul environment"
    },
    "warrior_in_game_realm": {
      "context": {
        "environment": "game_realm",
        "role": "warrior",
        "goal": "conquest"
      },
      "description": "Warrior performing Kama actions in Game Realm"
    },
    "merchant_in_marketplace": {
      "context": {
        "environment": "marketplace",
        "role": "merchant",
        "goal": "prosperity"
      },
      "description": "Merchant performing Artha actions in marketplace"
    }
  }
}
```

## Behavioral Normalization API

### Normalize Single State
- **Endpoint**: `POST /api/v1/normalize_state`
- **Example Request**:
```json
{
  "module": "gurukul",            // Must be one of: finance, game, gurukul, insight
  "action_type": "completing_lessons",
  "raw_value": 10.0,
  "context": {                   // Optional
    "difficulty": "medium",
    "completion_rate": 0.85
  },
  "metadata": {                  // Optional
    "session_id": "session_123",
    "duration": "45_min"
  }
}
```

### Normalize Batch States
- **Endpoint**: `POST /api/v1/normalize_state/batch`
- **Example Request**:
```json
{
  "states": [
    {
      "module": "gurukul",       // Must be one of: finance, game, gurukul, insight
      "action_type": "completing_lessons",
      "raw_value": 10.0,
      "context": {},
      "metadata": {}
    },
    {
      "module": "game",          // Must be one of: finance, game, gurukul, insight
      "action_type": "completing_quest",
      "raw_value": 15.0,
      "context": {},
      "metadata": {}
    }
  ]
}
```

### Update Prarabdha
- **Endpoint**: `POST /api/v1/update_prarabdha`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "increment": 2.5,
  "context": {                   // Optional
    "reason": "good_deed",
    "activity": "helping_others"
  },
  "metadata": {                  // Optional
    "source": "gurukul_module",
    "timestamp": "2026-01-14T12:00:00Z"
  }
}
```

## Karmic Feedback Engine API

### Compute and Publish Feedback Signal
- **Endpoint**: `POST /api/v1/feedback_signal`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "include_modules": true,        // Optional, default true
  "include_behavioral_bias": true // Optional, default true
}
```

### Get Feedback Signal
- **Endpoint**: `GET /api/v1/feedback_signal/{user_id}`
- **Example Request**: `GET /api/v1/feedback_signal/Siddhesh_2004?include_modules=true&include_behavioral_bias=true`
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "influence_data": {
    "module_aggregation": {
      "finance": 15.0,
      "game": 18.0,
      "gurukul": 22.5,
      "insight": 12.0
    },
    "behavioral_bias": {
      "learning_orientation": 0.8,
      "service_orientation": 0.6,
      "wealth_orientation": 0.4
    },
    "dynamic_influence_score": 16.75
  },
  "signal_id": null
}
```

### Batch Feedback Signals
- **Endpoint**: `POST /api/v1/feedback_signal/batch`
- **Example Request**:
```json
{
  "user_ids": ["Siddhesh_2004", "user_123", "user_456"],
  "include_modules": true,        // Optional, default true
  "include_behavioral_bias": true // Optional, default true
}
```

### Check System Health
- **Endpoint**: `GET /api/v1/feedback_signal/health`
- **Example Response**:
```json
{
  "status": "healthy",
  "endpoint": "http://insightflow.example.com/api/v1/telemetry",
  "status_code": 200,
  "response_time": 0.125,
  "error": null
}
```

### Get Configuration
- **Endpoint**: `GET /api/v1/feedback_signal/config`
- **Example Response**:
```json
{
  "status": "success",
  "config": {
    "stp_bridge_url": "http://insightflow.example.com/api/v1/telemetry",
    "retry_attempts": 3,
    "timeout": 30,
    "enabled": true,
    "feedback_batch_size": 10,
    "feedback_interval": 300
  }
}
```

## Karmic Analytics API

### Get Karma Trends
- **Endpoint**: `GET /api/v1/analytics/karma_trends`
- **Example Request**: `GET /api/v1/analytics/karma_trends?weeks=4`
- **Example Response**:
```json
{
  "status": "success",
  "data": {
    "dharma_seva_trends": [
      {
        "week": "2026-W01",
        "dharma_points": 125.5,
        "seva_points": 89.2
      }
    ],
    "paap_punya_trends": [
      {
        "week": "2026-W01",
        "paap_ratio": 0.15,
        "punya_ratio": 0.25
      }
    ]
  }
}
```

### Generate Dharma/Seva Flow Chart
- **Endpoint**: `GET /api/v1/analytics/charts/dharma_seva_flow`
- **Example Request**: `GET /api/v1/analytics/charts/dharma_seva_flow?weeks=4&download=false`
- **Example Response**:
```json
{
  "status": "success",
  "chart_generated": true,
  "filepath": "./analytics_exports/dharma_seva_flow_2026-01-14.png",
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Generate Paap/Punya Ratio Chart
- **Endpoint**: `GET /api/v1/analytics/charts/paap_punya_ratio`
- **Example Request**: `GET /api/v1/analytics/charts/paap_punya_ratio?weeks=4&download=false`
- **Example Response**:
```json
{
  "status": "success",
  "chart_generated": true,
  "filepath": "./analytics_exports/paap_punya_ratio_2026-01-14.png",
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Export Weekly Summary
- **Endpoint**: `GET /api/v1/analytics/exports/weekly_summary`
- **Example Request**: `GET /api/v1/analytics/exports/weekly_summary?weeks=4&download=true`
- **Example Response**:
```json
{
  "status": "success",
  "download_url": "/analytics_exports/demo_weekly_summary.csv",
  "filepath": "./analytics_exports/demo_weekly_summary.csv"
}
```

### Get Live Metrics
- **Endpoint**: `GET /api/v1/analytics/metrics/live`
- **Example Response**:
```json
{
  "status": "success",
  "data": {
    "total_users": 150,
    "active_users_today": 45,
    "total_karma_generated": 1250.5,
    "average_karma_per_user": 8.34,
    "top_performing_action": "helping_peers",
    "current_leaderboard": [
      {
        "user_id": "top_user_1",
        "karma_score": 125.5
      }
    ]
  }
}
```

## Karma Lifecycle Engine API

### Get Prarabdha Counter
- **Endpoint**: `GET /api/v1/karma/lifecycle/prarabdha/{user_id}`
- **Example Request**: `GET /api/v1/karma/lifecycle/prarabdha/Siddhesh_2004`
- **Example Response**:
```json
{
  "user_id": "Siddhesh_2004",
  "prarabdha": 15.5,
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Update Prarabdha Counter
- **Endpoint**: `POST /api/v1/karma/lifecycle/prarabdha/update`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004",
  "increment": 2.5
}
```

### Check Death Threshold
- **Endpoint**: `POST /api/v1/karma/lifecycle/death/check`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004"
}
```
- **Example Response**:
```json
{
  "user_id": "Siddhesh_2004",
  "current_prarabdha": -205.0,
  "death_threshold": -200.0,
  "threshold_reached": true,
  "details": {
    "current_prarabdha": -205.0,
    "death_threshold": -200.0,
    "threshold_reached": true,
    "loka_destination": "Naraka"
  },
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Process Death Event
- **Endpoint**: `POST /api/v1/karma/lifecycle/death/process`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004"
}
```
- **Example Response**:
```json
{
  "status": "success",
  "user_id": "Siddhesh_2004",
  "loka": "Naraka",               // Must be one of: Swarga, Mrityuloka, Antarloka, Naraka
  "description": "Lower realm of purification through suffering",
  "inheritance": {
    "DharmaPoints": 0,
    "SevaPoints": 0,
    "PunyaTokens": 0,
    "PaapTokens": {
      "minor": 0,
      "medium": 0,
      "maha": 0
    }
  },
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Process Rebirth
- **Endpoint**: `POST /api/v1/karma/lifecycle/rebirth/process`
- **Example Request**:
```json
{
  "user_id": "Siddhesh_2004"
}
```
- **Example Response**:
```json
{
  "status": "success",
  "old_user_id": "Siddhesh_2004",
  "new_user_id": "Siddhesh_2005",
  "inheritance": {
    "SanchitaKarma": 50.0,
    "PrarabdhaKarma": 0.0,
    "DridhaKarma": 10.0
  },
  "starting_level": "learner",
  "timestamp": "2026-01-14T13:14:27.123456+00:00"
}
```

### Simulate Lifecycle Cycles
- **Endpoint**: `POST /api/v1/karma/lifecycle/simulate`
- **Example Request**:
```json
{
  "cycles": 10,                  // Optional, default 50
  "initial_users": 5             // Optional, default 10
}
```
- **Example Response**:
```json
{
  "status": "simulation_completed",
  "cycles_simulated": 10,
  "results": [
    {
      "cycle": 1,
      "events": [
        {
          "type": "life_event",
          "user_id": "sim_user_1642123456000_0",
          "prarabdha_change": 15.5
        }
      ]
    }
  ],
  "timestamp": "2026-01-14T13:14:27.123456+00:00",
  "statistics": {
    "total_cycles": 10,
    "initial_users": 5,
    "total_births": 5,
    "total_deaths": 0,
    "total_rebirths": 0,
    "loka_distribution": {
      "Swarga": 0,
      "Mrityuloka": 5,
      "Antarloka": 0,
      "Naraka": 0
    },
    "final_active_users": 5
  }
}
```

## Valid Values Reference

### Valid Actions
- `completing_lessons`
- `helping_peers`
- `solving_doubts`
- `selfless_service`
- `cheat`

### Valid Roles
- `learner`
- `volunteer`
- `seva`
- `guru`

### Valid Token Types
- `DharmaPoints`
- `SevaPoints`
- `PunyaTokens`
- `PaapTokens.minor`
- `PaapTokens.medium`
- `PaapTokens.maha`
- `SanchitaKarma`
- `PrarabdhaKarma`
- `DridhaKarma`
- `AdridhaKarma`
- `Rnanubandhan.minor`
- `Rnanubandhan.medium`
- `Rnanubandhan.major`

### Valid Modules
- `finance`
- `game`
- `gurukul`
- `insight`

### Valid Severity Levels
- `minor`
- `medium`
- `maha`

### Valid Loka Types
- `Swarga` - Heavenly realm
- `Mrityuloka` - Middle realm (human world)
- `Antarloka` - Intermediate realm
- `Naraka` - Lower realm

### Valid Paap Classes
- `cheat`
- `disrespect_guru`
- `break_promise`
- `harm_others`
- `false_speech`
- `theft`
- `violence`

### Valid Atonement Types
- `Jap`
- `Tap`
- `Bhakti`
- `Daan`

### Valid Relationship Statuses
- `active`
- `repaid`
- `transferred`

### Valid Repayment Methods
- `atonement`
- `service`
- `donation`
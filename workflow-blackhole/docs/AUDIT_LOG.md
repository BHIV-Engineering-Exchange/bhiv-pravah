# Audit Log Instructions

## 1. Overview

The audit log is a critical security and compliance feature within Infiverse. It records significant events and actions performed by users and the system, creating an immutable trail of activity. This is essential for security analysis, troubleshooting, and demonstrating compliance with regulations like GDPR.

All audit logs are stored in the `auditlogs` collection in MongoDB.

## 2. Logged Events

The system logs the following key events:

- **User Authentication**:
  - `USER_LOGIN_SUCCESS`: Successful user login.
  - `USER_LOGIN_FAILURE`: Failed login attempt (includes the reason, e.g., invalid credentials).
  - `USER_LOGOUT`: User logout.

- **User & Admin Actions**:
  - `USER_CREATED`: A new user account is created.
  - `USER_UPDATED`: A user's profile or role is modified.
  - `USER_DELETED`: A user account is deleted.
  - `ADMIN_ACTION`: An administrative action is performed (e.g., changing system settings).

- **Monitoring & Consent**:
  - `MONITORING_STARTED`: Monitoring is initiated for a user.
  - `MONITORING_STOPPED`: Monitoring is stopped.
  - `CONSENT_GIVEN`: A user provides consent for monitoring.
  - `CONSENT_REVOKED`: A user pauses or revokes consent.

- **Data & Security**:
  - `DATA_EXPORTED`: A user exports data (e.g., a report).
  - `SECURITY_ALERT`: A potential security issue is flagged by the system (e.g., multiple failed logins).
  - `POLICY_VIOLATION`: A monitoring policy is violated (e.g., access to a disallowed site).

## 3. Audit Log Structure

Each audit log entry contains the following fields:

- `timestamp`: The date and time when the event occurred.
- `user`: The ID of the user who performed the action (if applicable).
- `event`: The type of event (e.g., `USER_LOGIN_SUCCESS`).
- `ipAddress`: The IP address from which the action was initiated.
- `details`: A JSON object containing additional context about the event (e.g., the ID of the user who was modified).

### Example Log Entry:
```json
{
  "_id": "63a5d2f1c3b4e8a1d2f3e4b5",
  "timestamp": "2025-09-17T10:00:00.000Z",
  "user": "63a5d2f1c3b4e8a1d2f3e4a1",
  "event": "USER_UPDATED",
  "ipAddress": "192.168.1.10",
  "details": {
    "targetUser": "63a5d2f1c3b4e8a1d2f3e4b2",
    "changes": {
      "role": "Manager"
    }
  }
}
```

## 4. How to Use the Audit Logs

Administrators can query the `auditlogs` collection directly in MongoDB to investigate incidents or perform compliance checks.

### Example Queries:

- **Find all failed login attempts for a specific user**:
  ```javascript
  db.auditlogs.find({
    event: 'USER_LOGIN_FAILURE',
    'details.email': 'user@example.com'
  })
  ```

- **Review all administrative actions performed in the last 7 days**:
  ```javascript
  db.auditlogs.find({
    event: 'ADMIN_ACTION',
    timestamp: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
  })
  ```

By regularly reviewing these logs, administrators can maintain a high level of security and ensure that the system is being used appropriately.

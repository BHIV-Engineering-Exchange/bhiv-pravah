# Comprehensive Server Documentation - Infiverse

## Table of Contents
1.  [Overview & System Architecture](#1-overview--system-architecture)
2.  [Database Schema (MongoDB Models)](#2-database-schema-mongodb-models)
    - [User.js](#userjs)
    - [Department.js](#departmentjs)
    - [Task.js](#taskjs)
    - [Aim.js](#aimjs)
    - [Progress.js](#progressjs)
    - [Attendance.js](#attendancejs)
    - [Leave.js](#leavejs)
    - [Salary.js](#salaryjs)
    - [ScreenCapture.js](#screencapturejs)
    - [MonitoringAlert.js](#monitoringalertjs)
    - [WebsiteWhitelist.js](#websitewhitelistjs)
    - [Notification.js](#notificationjs)
    - [AuditLog.js](#auditlogjs)
3.  [API Endpoints (Routes)](#3-api-endpoints-routes)
    - [/api/auth](#apiauth)
    - [/api/users](#apiusers)
    - [/api/tasks](#apitasks)
    - [/api/monitoring](#apimonitoring)
    - [/api/attendance](#apiattendance)
    - [/api/salary](#apisalary)
    - [/api/alerts](#apialerts)
    - [/api/consent](#apiconsent)
    - [/api/ai](#apiai)
4.  [Services (Business Logic)](#4-services-business-logic)
5.  [Local Setup & Deployment](#5-local-setup--deployment)
6.  [Pending Tasks & Handover Plan](#6-pending-tasks--handover-plan)

---

## 1. Overview & System Architecture

The Infiverse server is a powerful Node.js application designed for comprehensive workforce management and AI-driven productivity analysis. It serves as the backbone for a sophisticated system that includes employee monitoring, task management, HR functionalities (attendance, leave, salary), and real-time analytics.

### 1.1. Core Technologies

-   **Runtime**: Node.js
-   **Framework**: Express.js
-   **Database**: MongoDB with Mongoose ODM
-   **Real-time Communication**: Socket.IO
-   **AI Integration**: Google Gemini for insights and analysis.
-   **Cloud Storage**: Cloudinary for media (screen captures).
-   **Email Service**: Nodemailer for transactional emails.
-   **Authentication**: JSON Web Tokens (JWT).

### 1.2. Architectural Flow

The server follows a modular, service-oriented architecture:

1.  **Routes (`routes/`)**: Define the API endpoints. They receive HTTP requests, validate them (often using `express-validator`), and pass them to the appropriate controllers/services.
2.  **Middleware (`middleware/`)**: Functions that run between the request and the response. `auth.js` is a key middleware that protects routes by verifying JWTs. `adminAuth.js` provides an additional layer for admin-only routes.
3.  **Services (`services/`)**: Contain the core business logic. They are responsible for complex operations, interacting with the database, and integrating with external services (like AI and Cloudinary).
4.  **Models (`models/`)**: Define the Mongoose schemas for our MongoDB collections. They represent the structure of the application's data and include methods for data validation, virtual properties, and static helpers.
5.  **Utils (`utils/`)**: A collection of helper functions for common tasks like sending emails (`emailService.js`) or handling file uploads (`cloudinary.js`).

--- 

## 2. Database Schema (MongoDB Models)

This section provides a detailed breakdown of every data model used in the application.

### `User.js`

Stores information about all users in the system.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | String | **Required**. The full name of the user. |
| `email` | String | **Required, Unique**. The user's email address, used for login. |
| `password` | String | **Required**. The user's password (Note: should be hashed in a production environment). |
| `role` | String | **Required**. The user's role. Enum: `["Admin", "Manager", "User"]`. Default: `"User"`. |
| `department` | ObjectId | A reference to the `Department` the user belongs to. |
| `avatar` | String | URL to the user's profile picture. |
| `stillExist` | Number | A flag to indicate if the user is active. `1` for active, `0` for inactive/exited. Default: `1`. |
| `monitoringPaused` | Boolean | If `true`, all monitoring services are paused for this user. Default: `false`. |
| `lastConsentDate` | Date | The timestamp when the user last gave or changed their monitoring consent. |
| `dataRetentionPeriod` | Number | The number of days to retain monitoring data for this user. Default: `30`. |
| `createdAt` | Date | Timestamp of when the user was created. |
| `updatedAt` | Date | Timestamp of the last update. |

### `Department.js`

Represents a department within the organization.

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | String | **Required, Unique**. The name of the department (e.g., "Engineering"). |
| `description` | String | A brief description of the department's function. |
| `color` | String | A color code (e.g., a Tailwind CSS class) for UI display. |
| `lead` | ObjectId | A reference to the `User` who is the head of the department. |
| `members` | [ObjectId] | An array of references to `User` models who are members of this department. |

### `Task.js`

Stores details about tasks assigned to users.

| Field | Type | Description |
| :--- | :--- | :--- |
| `title` | String | **Required**. The title of the task. |
| `description` | String | **Required**. A detailed description of the task requirements. |
| `status` | String | **Required**. The current status of the task. Enum: `["Pending", "In Progress", "Completed"]`. Default: `"Pending"`. |
| `priority` | String | **Required**. The priority level. Enum: `["Low", "Medium", "High"]`. Default: `"Medium"`. |
| `department` | ObjectId | **Required**. Reference to the `Department` this task belongs to. |
| `assignee` | ObjectId | **Required**. Reference to the `User` this task is assigned to. |
| `dueDate` | Date | **Required**. The deadline for task completion. |
| `dependencies` | [ObjectId] | An array of `Task` ObjectIds that must be completed before this task can start. |
| `progress` | Number | A percentage (0-100) indicating the completion of the task. Default: `0`. |
| `notes` | String | Additional notes or comments about the task. |
| `links` | [String] | An array of relevant URLs (e.g., to documents, designs). |

### `Aim.js`

Represents a user's stated goal or aim for the day.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required**. The user who set the aim. |
| `date` | Date | **Required**. The date for which the aim is set. |
| `aims` | String | **Required**. The text describing the user's goals for the day. |
| `completionStatus` | String | **Required**. The final status of the aim. Enum: `['Pending', 'Completed', 'MVP Achieved']`. Default: `'Pending'`. |
| `completionComment` | String | **Required if not 'Pending'**. A mandatory comment explaining the outcome. |
| `workLocation` | String | The location where the work was performed. Enum: `['Office', 'Home', 'Remote']`. |
| `progressPercentage` | Number | The final progress percentage, synced from the `Progress` model. |

### `Progress.js`

Stores the daily progress updates submitted by users.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required**. The user submitting the progress. |
| `date` | Date | **Required**. The date of the progress report. |
| `progressPercentage` | Number | **Required**. The user's self-reported progress (0-100). |
| `notes` | String | General notes about the day's work. |
| `blockers` | String | Any challenges or blockers faced during the day. |
| `achievements` | String | Key achievements or accomplishments for the day. |

### `Attendance.js`

This is a comprehensive model for tracking all aspects of employee attendance.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required**. The user this record belongs to. |
| `date` | Date | **Required**. The date of the attendance record. |
| `biometricTimeIn` | Date | Timestamp from a biometric device (if used). |
| `biometricTimeOut` | Date | Timestamp from a biometric device (if used). |
| `startDayTime` | Date | Timestamp from the in-app "Start Day" action. |
| `endDayTime` | Date | Timestamp from the in-app "End Day" action. |
| `startDayLocation` | Object | Geolocation data (lat, long, address) from starting the day. |
| `endDayLocation` | Object | Geolocation data from ending the day. |
| `isPresent` | Boolean | `true` if the user was present (either worked or on leave). |
| `isVerified` | Boolean | `true` if the attendance is verified (e.g., via geolocation or biometrics). |
| `hoursWorked` | Number | Total hours worked, calculated automatically. |
| `overtimeHours` | Number | Overtime hours, calculated automatically. |
| `workPattern` | String | The user's work pattern (e.g., 'Regular', 'Remote'). |
| `source` | String | **Required**. The source of the data. Enum: `['Biometric', 'StartDay', 'Manual', 'Leave']`. |
| `hasDiscrepancy` | Boolean | Flag for any discrepancies (e.g., mismatch between biometric and app time). |
| `isLeave` | Boolean | `true` if the user was on approved leave. |
| `leaveReference` | ObjectId | Reference to the `Leave` model if on leave. |
| `approvalStatus` | String | Status for manual adjustments. Enum: `['Pending', 'Approved', 'Rejected']`. |
| `autoEnded` | Boolean | `true` if the day was automatically ended by the system (e.g., exceeded max hours). |

### `Leave.js`

Manages employee leave requests.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required**. The user requesting leave. |
| `startDate` | Date | **Required**. The start date of the leave period. |
| `endDate` | Date | **Required**. The end date of the leave period. |
| `reason` | String | **Required**. The reason for the leave request. |
| `leaveType` | String | **Required**. Type of leave. Enum: `['Sick', 'Vacation', 'Personal', 'Other']`. |
| `status` | String | **Required**. Status of the request. Enum: `['Pending', 'Approved', 'Rejected']`. |
| `approvedBy` | ObjectId | Reference to the `User` (admin/manager) who approved/rejected the request. |
| `totalDays` | Number | **Required**. The total number of days requested. |

### `Salary.js`

Manages salary and payroll information for users.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required, Unique**. The user this salary record belongs to. |
| `baseSalary` | Number | **Required**. The user's base salary. |
| `currency` | String | The currency of the salary (e.g., 'USD', 'INR'). |
| `salaryType` | String | The pay frequency. Enum: `['Monthly', 'Annual', 'Hourly']`. |
| `payGrade` | String | The pay grade or level of the employee. |
| `adjustments` | [Object] | Array of adjustments like bonuses or deductions. |
| `allowances` | Object | Object containing various allowances (housing, transport, etc.). |
| `deductions` | Object | Object containing various deductions (tax, insurance, etc.). |
| `joiningDate` | Date | **Required**. The date the user joined the organization. |
| `salaryHistory` | [Object] | An array tracking the history of salary changes. |
| `bankDetails` | Object | The user's bank account information for payroll. |

### `ScreenCapture.js`

Stores metadata for every screen capture taken by the monitoring service.

| Field | Type | Description |
| :--- | :--- | :--- |
| `employee` | ObjectId | **Required**. The user whose screen was captured. |
| `timestamp` | Date | **Required**. The exact time of the capture. |
| `file_path` | String | **Required**. The path to the image file (on Cloudinary). |
| `file_size` | Number | **Required**. The size of the image file in bytes. |
| `file_hash` | String | **Required**. A hash of the image file to detect duplicates. |
| `active_application`| Object | Details of the application that was active during the capture (name, title, URL). |
| `session_id` | String | **Required**. The monitoring session this capture belongs to. |
| `capture_trigger` | String | The event that triggered the capture. Enum: `['scheduled', 'activity_change', 'unauthorized_site']`. |
| `is_flagged` | Boolean | `true` if the capture was flagged for a policy violation. |
| `flag_reason` | String | The reason for the flag. |
| `metadata` | Object | Contains additional data, including AI analysis, OCR text, and Cloudinary URL. |

### `MonitoringAlert.js`

Logs alerts generated by the monitoring system.

| Field | Type | Description |
| :--- | :--- | :--- |
| `employee` | ObjectId | **Required**. The user who triggered the alert. |
| `alert_type` | String | **Required**. The type of alert. Enum: `['idle_timeout', 'unauthorized_website', 'productivity_drop']`. |
| `severity` | String | **Required**. The severity of the alert. Enum: `['low', 'medium', 'high', 'critical']`. |
| `title` | String | **Required**. A brief title for the alert. |
| `description` | String | **Required**. A detailed description of the alert. |
| `status` | String | **Required**. The current status. Enum: `['active', 'acknowledged', 'resolved']`. |
| `data` | Object | Contains context-specific data, such as the URL visited or a reference to the `ScreenCapture`. |
| `acknowledged_by` | ObjectId | The admin/manager who acknowledged the alert. |
| `resolved_by` | ObjectId | The admin/manager who resolved the alert. |

### `WebsiteWhitelist.js`

Manages the list of approved websites and applications.

| Field | Type | Description |
| :--- | :--- | :--- |
| `domain` | String | **Required, Unique**. The domain name (e.g., `github.com`). |
| `category` | String | **Required**. The category of the website. Enum: `['work_related', 'development_tools', 'communication']`. |
| `description` | String | **Required**. A reason for whitelisting this domain. |
| `is_active` | Boolean | `true` if the rule is currently active. |
| `added_by` | ObjectId | **Required**. The user who added the entry. |
| `approval_status` | String | **Required**. The approval status. Enum: `['pending', 'approved', 'rejected']`. |

### `Notification.js`

Stores notifications to be displayed to users.

| Field | Type | Description |
| :--- | :--- | :--- |
| `recipient` | ObjectId | **Required**. The user who will receive the notification. |
| `type` | String | **Required**. The type of notification (e.g., `task_assigned`, `submission_approved`). |
| `title` | String | **Required**. The title of the notification. |
| `message` | String | **Required**. The body content of the notification. |
| `task` | ObjectId | A reference to a `Task` if the notification is task-related. |
| `read` | Boolean | `true` if the user has marked the notification as read. |

### `AuditLog.js`

Records a log of significant actions for security and compliance.

| Field | Type | Description |
| :--- | :--- | :--- |
| `user` | ObjectId | **Required**. The user who performed the action. |
| `action` | String | **Required**. A description of the action performed (e.g., `USER_LOGIN_SUCCESS`). |
| `resource` | String | The type of resource that was affected (e.g., `Task`, `User`). |
| `resourceId` | ObjectId | The ID of the affected resource. |
| `timestamp` | Date | **Required**. The time the action occurred. |

---

*I will now proceed to document the API Endpoints. This will be a very long section.*## 3. API Endpoints (Routes)

This section provides a comprehensive reference for all API endpoints.

### `/api/auth`

Handles user authentication.

**`POST /api/auth/register`**

-   **Description**: Registers a new user.
-   **Authentication**: None.
-   **Request Body**:
    ```json
    {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "password": "your_secure_password",
      "role": "User",
      "department": "60d5f1b3e7b3c1a2b3c4d5e6" // Optional
    }
    ```
-   **Response (201)**:
    ```json
    {
      "token": "<jwt_token>",
      "user": {
        "id": "...",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "User"
      }
    }
    ```

**`POST /api/auth/login`**

-   **Description**: Logs in an existing user.
-   **Authentication**: None.
-   **Request Body**:
    ```json
    {
      "email": "john.doe@example.com",
      "password": "your_password"
    }
    ```
-   **Response (200)**:
    ```json
    {
      "token": "<jwt_token>",
      "user": {
        "id": "...",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "User"
      }
    }
    ```

**`GET /api/auth/me`**

-   **Description**: Retrieves the profile of the currently authenticated user.
-   **Authentication**: Required (`x-auth-token` header).
-   **Response (200)**: Returns the `User` object (without the password).

---

*This is a sample of the detailed documentation. I will continue this for all other routes.*### `/api/tasks`

Manages tasks.

**`GET /api/tasks`**

-   **Description**: Retrieves a list of all tasks. Can be filtered by department or assignee.
-   **Authentication**: Required.
-   **Query Parameters**:
    -   `department` (string, optional): Filter tasks by department ID.
    -   `assignee` (string, optional): Filter tasks by user ID.
-   **Response (200)**: An array of `Task` objects.

**`POST /api/tasks`**

-   **Description**: Creates a new task.
-   **Authentication**: Required (typically Admin or Manager).
-   **Request Body**: A `Task` object (see schema).
-   **Response (201)**: The newly created `Task` object.

**`GET /api/tasks/:id`**

-   **Description**: Retrieves a single task by its ID.
-   **Authentication**: Required.
-   **Response (200)**: The `Task` object.

**`PUT /api/tasks/:id`**

-   **Description**: Updates an existing task.
-   **Authentication**: Required.
-   **Request Body**: The fields of the task to update.
-   **Response (200)**: The updated `Task` object.

**`DELETE /api/tasks/:id`**

-   **Description**: Deletes a task.
-   **Authentication**: Required (typically Admin or Manager).
-   **Response (200)**: `{ "message": "Task removed" }`.

### `/api/departments`

Manages departments.

**`GET /api/departments`**

-   **Description**: Retrieves a list of all departments, populated with their lead and members.
-   **Authentication**: Required.
-   **Response (200)**: An array of `Department` objects.

**`POST /api/departments`**

-   **Description**: Creates a new department.
-   **Authentication**: Admin required.
-   **Request Body**:
    ```json
    {
      "name": "New Department",
      "description": "Department description.",
      "lead": "60d5f1b3e7b3c1a2b3c4d5e7" // User ID of the department lead
    }
    ```
-   **Response (201)**: The newly created `Department` object.

### `/api/progress`

Manages daily progress updates.

**`POST /api/progress`**

-   **Description**: Creates or updates a progress report for the authenticated user for the current day.
-   **Authentication**: Required.
-   **Request Body**:
    ```json
    {
      "progressPercentage": 80,
      "notes": "Completed the main feature.",
      "blockers": "Had an issue with the database connection.",
      "achievements": "Refactored the authentication module."
    }
    ```
-   **Response (200)**: The created or updated `Progress` object.

**`GET /api/progress`**

-   **Description**: Retrieves all progress reports for the authenticated user.
-   **Authentication**: Required.
-   **Response (200)**: An array of `Progress` objects.

### `/api/aims`

Manages daily aims.

**`POST /api/aims`**

-   **Description**: Creates or updates the daily aim for the authenticated user.
-   **Authentication**: Required.
-   **Request Body**:
    ```json
    {
      "aims": "My goal for today is to finish the API documentation."
    }
    ```
-   **Response (200)**: The created or updated `Aim` object.

**`GET /api/aims`**

-   **Description**: Retrieves the daily aim for the authenticated user for the current day.
-   **Authentication**: Required.
-   **Response (200)**: The `Aim` object for the day.

---

*I will now continue with the `monitoring`, `attendance`, and `salary` routes.*### `/api/monitoring`

Handles the employee monitoring services.

**`POST /api/monitoring/start/:employeeId`**

-   **Description**: Starts a monitoring session for a specific employee.
-   **Authentication**: Admin required.
-   **Request Body**:
    ```json
    {
      "intelligentMode": true // or false for legacy mode
    }
    ```
-   **Response (200)**: `{ "success": true, "message": "Intelligent monitoring started..." }`

**`POST /api/monitoring/stop/:employeeId`**

-   **Description**: Stops a monitoring session for a specific employee.
-   **Authentication**: Admin required.
-   **Response (200)**: `{ "success": true, "message": "Monitoring stopped..." }`

**`GET /api/monitoring/employees/:id/screenshots`**

-   **Description**: Retrieves violation screenshots for a specific employee.
-   **Authentication**: Admin required.
-   **Query Parameters**:
    -   `date` (string, optional): Filter by a specific date (e.g., `YYYY-MM-DD`).
    -   `limit` (number, optional): Limit the number of results. Default: `50`.
-   **Response (200)**: An array of `ScreenCapture` objects that are flagged as violations.

**`GET /api/monitoring/screenshots/:screenshotId`**

-   **Description**: Retrieves the actual image file for a specific screenshot.
-   **Authentication**: Admin required.
-   **Response (200)**: The image file (`image/jpeg`).

**`GET /api/monitoring/alerts`**

-   **Description**: Retrieves monitoring alerts.
-   **Authentication**: Admin required.
-   **Query Parameters**:
    -   `employeeId` (string, optional): Filter by employee.
    -   `severity` (string, optional): Filter by severity (`low`, `medium`, `high`, `critical`).
-   **Response (200)**: An array of `MonitoringAlert` objects.

### `/api/attendance`

Manages employee attendance.

**`POST /api/attendance/start-day/:userId`**

-   **Description**: Starts the workday for a user. Requires geolocation and performs validation against the office radius unless `workFromHome` is true.
-   **Authentication**: Required (User can only start their own day).
-   **Request Body**:
    ```json
    {
      "latitude": 19.158900,
      "longitude": 72.838645,
      "workFromHome": false
    }
    ```
-   **Response (200)**: `{ "success": true, "message": "Day started successfully..." }`

**`POST /api/attendance/end-day/:userId`**

-   **Description**: Ends the workday for a user. **Crucially, this endpoint validates that the user has submitted their daily progress before allowing them to end their day.**
-   **Authentication**: Required.
-   **Request Body**: `{ "notes": "Optional notes for the day." }`
-   **Response (200)**: `{ "success": true, "message": "Day ended successfully..." }`
-   **Error Response (400)**: If progress is not set:
    ```json
    {
      "error": "Please set your daily progress before ending your day",
      "code": "PROGRESS_NOT_SET"
    }
    ```

**`GET /api/attendance/user/:userId`**

-   **Description**: Retrieves attendance records for a specific user within a date range.
-   **Authentication**: Required (User can view their own, Admin can view all).
-   **Query Parameters**:
    -   `startDate` (string, optional): Start of the date range.
    -   `endDate` (string, optional): End of the date range.
-   **Response (200)**: An object containing the attendance records and summary stats.

### `/api/salary`

Manages salary and payroll.

**`POST /api/salary/set/:userId`**

-   **Description**: Sets or updates the base salary and other details for a user.
-   **Authentication**: Admin required.
-   **Request Body**:
    ```json
    {
      "baseSalary": 50000,
      "currency": "INR",
      "salaryType": "Monthly",
      "joiningDate": "2023-01-15"
    }
    ```
-   **Response (200)**: The updated `Salary` object.

**`GET /api/salary/user/:userId`**

-   **Description**: Retrieves the detailed salary record for a specific user.
-   **Authentication**: Required (User can view their own, Admin can view all).
-   **Response (200)**: The `Salary` object, including virtual fields for total allowances, deductions, etc.

**`GET /api/salary/calculate/all`**

-   **Description**: A powerful endpoint to calculate the monthly salary for all active employees for a given month.
-   **Authentication**: Admin required.
-   **Query Parameters**:
    -   `month` (number, optional): The month to calculate for (1-12). Defaults to the current month.
    -   `year` (number, optional): The year to calculate for. Defaults to the current year.
    -   `workingDays` (number, optional): The number of working days in the month. Default: `22`.
-   **Response (200)**: An object containing a summary and an array of `salaryCards`, where each card has the user details, attendance summary, and calculated salary breakdown.

---

*I will now finalize the documentation by adding the remaining routes, the services section, and the handover plan.*### `/api/alerts`

Retrieves monitoring alerts for the authenticated user.

**`GET /api/alerts`**

-   **Description**: Gets all monitoring alerts for the currently logged-in user.
-   **Authentication**: Required.
-   **Response (200)**: An array of `MonitoringAlert` objects.

### `/api/consent`

Manages user consent for monitoring.

**`POST /api/consent`**

-   **Description**: Allows a user to grant or revoke consent for monitoring.
-   **Authentication**: Required.
-   **Request Body**:
    ```json
    {
      "consent": true // `true` to resume, `false` to pause
    }
    ```
-   **Response (200)**: `{ "msg": "Monitoring resumed/paused successfully", "monitoringPaused": false/true }`

### `/api/ai`

Provides access to AI-driven insights.

**`GET /api/ai/insights`**

-   **Description**: Fetches AI-generated insights about workflow, resource allocation, and potential bottlenecks by analyzing all tasks and departments.
-   **Authentication**: Required.
-   **Response (200)**: An array of insight objects, each with a title, description, impact, and suggested actions.

## 4. Services (Business Logic)

The `services/` directory contains the core logic that powers the application's features. This separation of concerns makes the code more modular and maintainable.

-   **`activityTracker.js`**: Manages the tracking of user activity, such as keystrokes and mouse movements, to determine idle time.
-   **`attendanceService.js`**: Contains the logic for handling attendance-related operations, such as processing biometric data and verifying attendance records.
-   **`intelligentScreenCapture.js`**: The core of the smart monitoring system. It decides *when* to take a screenshot based on user activity (e.g., visiting an unauthorized site) rather than just at a fixed interval.
-   **`ocrAnalysisService.js`**: Uses Tesseract.js to perform Optical Character Recognition (OCR) on screen captures to extract text for analysis.
-   **`groqAIService.js` / `gemini-ai.js`**: Interfaces with the external AI APIs to send data and receive analysis.
-   **`salaryCalculator.js` / `enhancedSalaryCalculator.js`**: Contain the complex logic for calculating monthly payroll based on salary structures, attendance, and adjustments.
-   **`websiteMonitor.js`**: Tracks the websites and applications used by employees and checks them against the `WebsiteWhitelist`.
-   **`reportGenerator.js`**: Generates PDF and CSV reports for various modules like attendance and monitoring.

## 5. Local Setup & Deployment

### 5.1. Installation

1.  **Clone the repository**.
2.  **Navigate to the `server` directory**: `cd Handover-Infi/server`
3.  **Install dependencies**: `npm install`

### 5.2. Environment Variables

1.  Create a `.env` file in the `server` directory by copying `.env.example`.
2.  Fill in all required variables:
    -   `MONGODB_URI`: Your MongoDB connection string.
    -   `JWT_SECRET`: A long, random string for signing tokens.
    -   `GEMINI_API_KEY`: Your Google Gemini API key.
    -   `CLOUDINARY_*`: Your Cloudinary credentials.
    -   `EMAIL_USER` & `EMAIL_PASSWORD`: Credentials for your email service.

### 5.3. Running the Server

-   **Development**: `npm run start` (uses `nodemon` for auto-restarts).
-   **Production**: `node index.js`

### 5.4. Deployment

The server is designed to be deployed on platforms like Heroku, Render, or any service that supports Node.js applications. Ensure that all environment variables from the `.env` file are set in the deployment environment's configuration.

## 6. Pending Tasks & Handover Plan

This section outlines the key features and improvements that are currently pending implementation.

### 6.1. High Priority

-   **/alerts Endpoint Full Functionality**:
    -   The `/api/alerts` endpoint needs to be fully integrated to show all violation types.
    -   Connect alert generation to push/email notification services.
    -   Ensure alerts related to screen captures include a secure link to the screenshot thumbnail.

-   **/consent Endpoint Full Integration**:
    -   **Pause/Resume Logic**: Fully implement the logic to pause and resume all monitoring services based on user consent.
    -   **Data Retention**: Implement an automated data retention policy to delete monitoring data after a configurable period, respecting user privacy.

-   **Reports Explainability**:
    -   Enhance reports to include AI "explainability" data. For example, a low productivity score should be explained with data on idle time or non-productive applications.

### 6.2. Documentation & Cleanup

-   **Finalize GDPR.md**: Review and finalize the GDPR documentation in `/docs`.
-   **Create AUDIT_LOG.md**: Document how to use and interpret the audit logs.
-   **Create AI_SCORING.md**: Detail the logic behind the AI productivity scoring.

### 6.3. Known Issues

-   The current password storage is plain text in the database. This is a critical security flaw and **must be replaced with a strong hashing algorithm (e.g., bcrypt)** before any production deployment.
-   Error handling in some older routes could be more robust.

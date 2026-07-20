# AI Agent Logistics System - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Using the Dashboard](#using-the-dashboard)
4. [Chatbot Interface](#chatbot-interface)
5. [Human Review System](#human-review-system)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum
- 10GB disk space
- Internet connection for OpenAI API (optional)

### Quick Start
1. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the System**:
   ```bash
   python start_server.py
   ```

4. **Access the Dashboard**:
   Open http://localhost:8501 in your browser

## System Overview

The AI Agent Logistics System automates key logistics operations:

### Core Components
- **Restock Agent**: Monitors returns and creates restock requests
- **Procurement Agent**: Manages purchase orders with suppliers
- **Delivery Agent**: Handles shipment creation and tracking
- **Chatbot**: Answers customer queries about orders and restocks
- **Human Review**: Escalates complex decisions to human operators

### Data Flow
```
Returns → Agent Analysis → Restock Decision → Human Review (if needed) → Execution
```

## Using the Dashboard

### Main Dashboard
The main dashboard provides an overview of:
- System health status
- Recent agent activities
- Pending human reviews
- Key performance metrics

### Navigation
- **Orders**: View and manage customer orders
- **Returns**: Monitor product returns
- **Restocks**: Track restock requests and status
- **Agents**: Monitor agent performance
- **Reviews**: Handle pending human reviews

### Key Features

#### Real-time Monitoring
- Live system metrics
- Agent activity logs
- Performance charts

#### Data Management
- Import/export data
- Bulk operations
- Data validation

#### Reporting
- Generate custom reports
- Export to Excel/PDF
- Schedule automated reports

## Chatbot Interface

### Supported Queries
The chatbot can handle:
- Order status inquiries: "Where is my order #123?"
- Restock information: "When will Product A101 be restocked?"
- General help: "What can you help me with?"

### Query Examples
```
User: "Where is my order #101?"
Bot: "📦 Your order #101 is: Shipped."

User: "When will Product A101 be restocked?"
Bot: "🔁 Product A101 is pending restock (Qty: 10)."
```

### Escalation
Complex queries are automatically escalated to human support with a reference ID.

## Human Review System

### When Reviews are Triggered
- High-quantity restocks (>20 units)
- Low-confidence decisions (<70%)
- Urgent customer queries
- New products without historical data

### Review Interface
Access the review interface via:
1. Dashboard → Reviews tab
2. Command line: `python review_interface.py`

### Review Commands
```bash
list        # Show pending reviews
review <id> # Review specific decision
approve <id> "notes"  # Approve with notes
reject <id> "notes"   # Reject with notes
stats       # Show review statistics
```

### Best Practices
- Review high-value decisions promptly
- Provide clear notes for future reference
- Monitor review patterns for system improvement

## Monitoring and Alerts

### System Monitoring
The system continuously monitors:
- CPU and memory usage
- API response times
- Agent processing times
- Database performance

### Alert Types
- **Critical**: System failures, high resource usage
- **Warning**: Performance degradation, high pending orders
- **Info**: Successful operations, routine updates

### Notification Channels
- Email alerts for critical issues
- Slack notifications for warnings
- Dashboard notifications for all events

### Configuration
Set up alerts in your `.env` file:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=admin@company.com,ops@company.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## Troubleshooting

### Common Issues

#### Agent Not Processing
**Symptoms**: No new restock requests, stale logs
**Solutions**:
1. Check agent logs: `tail -f data/logs.csv`
2. Verify data files exist in `data/` directory
3. Restart agent: `python agent.py`

#### API Not Responding
**Symptoms**: Dashboard shows connection errors
**Solutions**:
1. Check if API is running: `curl http://localhost:8000/health`
2. Restart API server: `python start_server.py`
3. Check port conflicts

#### Database Issues
**Symptoms**: Data not saving, query errors
**Solutions**:
1. Check database file permissions
2. Run database migration: `python migrate_to_database.py`
3. Verify disk space

#### High Memory Usage
**Symptoms**: System slowdown, out of memory errors
**Solutions**:
1. Restart services: `python start_server.py`
2. Check for memory leaks in logs
3. Increase system memory

### Log Files
- **Agent logs**: `data/logs.csv`
- **Review logs**: `data/review_log.csv`
- **System logs**: `data/monitoring_metrics.json`
- **Error logs**: Check console output

### Getting Help
1. Check the troubleshooting section
2. Review system logs
3. Run health check: `python deploy.py health-check`
4. Contact system administrator

### Performance Optimization
- Adjust agent intervals in environment variables
- Optimize database queries
- Monitor resource usage
- Scale horizontally if needed

## Advanced Configuration

### Environment Variables
Key configuration options:
```bash
# Agent Settings
AGENT_INTERVAL=300          # Agent cycle interval (seconds)
CONFIDENCE_THRESHOLD=0.7    # Human review threshold

# API Settings
API_HOST=0.0.0.0           # API host
API_PORT=8000              # API port

# Features
ENABLE_SMART_CHATBOT=true  # OpenAI-powered chatbot
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_HUMAN_REVIEW=true
```

### Scaling
For high-volume operations:
1. Use multiple worker processes
2. Implement load balancing
3. Use external database (PostgreSQL)
4. Set up monitoring and alerting

### Security
- Use HTTPS in production
- Implement API authentication
- Regular security updates
- Monitor access logs

# Deployment Checklist

Use this checklist to ensure proper deployment of the Employee Activity Agent.

## Pre-Deployment

### Backend Preparation
- [ ] Backend API is deployed and accessible
- [ ] HTTPS is enabled on backend (required for production)
- [ ] Database is set up and running
- [ ] Environment variables are configured (JWT_SECRET, etc.)

### API Endpoints Implementation
- [ ] `POST /api/agent/login` - Returns JWT token
- [ ] `POST /api/attendance/start` - Creates attendance record, returns ID
- [ ] `POST /api/attendance/end` - Ends attendance record
- [ ] `POST /api/activity/ingest` - Accepts and stores activity data
- [ ] All endpoints tested with Postman/cURL

### Database Schema
- [ ] User model exists with email/password fields
- [ ] Attendance model created
- [ ] Activity model created (new)
- [ ] Database indexes created for performance
- [ ] Test data created for development

## Agent Configuration

### Environment Setup
- [ ] `.env` file created from `.env.example`
- [ ] `AGENT_API_BASE_URL` set to production backend URL
- [ ] Backend URL uses HTTPS (not HTTP)
- [ ] URL is accessible from employee workstations

### Dependencies
- [ ] Run `npm install` successfully
- [ ] All dependencies installed without errors
- [ ] `iohook` compiled successfully (requires build tools)
- [ ] No security vulnerabilities (`npm audit`)

### Testing
- [ ] Login works with test credentials
- [ ] Start Day creates attendance record in backend
- [ ] Activity data is sent every 30 seconds
- [ ] Activity data appears in backend database
- [ ] End Day stops tracking immediately
- [ ] End Day updates attendance record in backend
- [ ] Tray icon shows correct status
- [ ] Stats update in real-time in UI
- [ ] Logout clears session correctly

## Building

### Windows Build
- [ ] Run `npm run build:win`
- [ ] Build completes without errors
- [ ] Installer created in `dist/` folder
- [ ] Test installer on clean Windows machine
- [ ] App launches successfully
- [ ] No antivirus false positives
- [ ] All features work in built version

### macOS Build
- [ ] Run `npm run build:mac` (on macOS)
- [ ] Build completes without errors
- [ ] DMG created in `dist/` folder
- [ ] Test DMG on clean macOS machine
- [ ] App launches successfully
- [ ] Accessibility permission prompt appears
- [ ] All features work in built version

## Distribution

### Documentation
- [ ] README.md reviewed and updated
- [ ] QUICK_START.md distributed to employees
- [ ] Privacy policy shared with employees
- [ ] IT support documentation prepared
- [ ] Backend integration guide shared with backend team

### Files to Distribute
- [ ] Windows installer (`.exe`)
- [ ] macOS installer (`.dmg`)
- [ ] Quick start guide (PDF or link)
- [ ] Privacy notice (PDF or link)
- [ ] IT support contact information

### Employee Communication
- [ ] Announcement email sent
- [ ] Installation instructions provided
- [ ] Privacy policy communicated
- [ ] Support channel established (email/helpdesk)
- [ ] Training session scheduled (optional)

## Installation Support

### Windows Installation
- [ ] Installer runs without admin rights (or document requirement)
- [ ] Installation path documented
- [ ] Startup behavior documented
- [ ] Uninstall process tested
- [ ] Windows Defender/antivirus whitelisting (if needed)

### macOS Installation
- [ ] DMG opens successfully
- [ ] Drag-to-Applications flow tested
- [ ] Accessibility permissions documented
- [ ] Input Monitoring permissions documented
- [ ] Gatekeeper approval process documented
- [ ] Uninstall process tested

## Security & Compliance

### Security Review
- [ ] Code reviewed for security issues
- [ ] No hardcoded credentials
- [ ] JWT tokens properly secured
- [ ] HTTPS enforced for API calls
- [ ] No sensitive data logged
- [ ] Error messages don't leak information

### Privacy Compliance
- [ ] Consent screen reviewed by legal
- [ ] Privacy policy approved
- [ ] Data retention policy defined
- [ ] GDPR compliance verified (if applicable)
- [ ] Employee rights documented (access, deletion, etc.)
- [ ] Data processing agreement in place

### Monitoring
- [ ] Backend logging configured
- [ ] Error tracking set up (Sentry, etc.)
- [ ] Usage analytics configured (optional)
- [ ] Health check endpoint available
- [ ] Alert system configured for errors

## Post-Deployment

### Day 1
- [ ] Monitor backend logs for errors
- [ ] Check successful logins
- [ ] Verify activity data ingestion
- [ ] Respond to support requests
- [ ] Document common issues

### Week 1
- [ ] Review activity data quality
- [ ] Identify and fix bugs
- [ ] Update documentation with FAQs
- [ ] Survey employee feedback
- [ ] Performance optimization if needed

### Month 1
- [ ] Analyze usage patterns
- [ ] Review security logs
- [ ] Plan feature improvements
- [ ] Update documentation
- [ ] Review privacy compliance

## Rollback Plan

### If Issues Occur
- [ ] Backup plan documented
- [ ] Employees know how to uninstall
- [ ] Backend can disable agent API
- [ ] Communication plan for rollback
- [ ] Data retention during rollback period

## Support Resources

### Internal Documentation
- [ ] Knowledge base articles created
- [ ] Common issues documented
- [ ] Troubleshooting guide available
- [ ] Contact information published
- [ ] Escalation process defined

### Employee Resources
- [ ] FAQ document created
- [ ] Video tutorial created (optional)
- [ ] Step-by-step screenshots available
- [ ] Support email/helpdesk set up
- [ ] Response time SLA defined

## Verification

### Final Checks Before Launch
- [ ] All items above completed
- [ ] Pilot test with small group successful
- [ ] Legal approval obtained
- [ ] Management approval obtained
- [ ] Rollout plan approved
- [ ] Support team trained
- [ ] Monitoring dashboards ready

### Sign-Off
- [ ] Technical Lead: _________________ Date: _______
- [ ] IT Manager: _________________ Date: _______
- [ ] Legal/Compliance: _________________ Date: _______
- [ ] HR/Management: _________________ Date: _______

---

**Last Updated**: [Date]  
**Version**: 1.0  
**Prepared by**: [Name/Team]

# Demo Runbook - BHIV HR Platform

**Version**: 1.0  
**Last Updated**: January 29, 2026  
**Target Audience**: Demo Presenters, Sales Team, Stakeholders  
**Platform**: Windows + Docker + Render Cloud + MongoDB Atlas  
**Status**: ✅ Demo Ready

---

## 📋 Table of Contents

1. [Pre-Demo Checklist](#pre-demo-checklist)
2. [Demo Flow](#demo-flow)
3. [Step-by-Step Instructions](#step-by-step-instructions)
4. [Failure Recovery Procedures](#failure-recovery-procedures)
5. [Emergency Contacts](#emergency-contacts)
6. [Post-Demo Cleanup](#post-demo-cleanup)

---

## ✅ Pre-Demo Checklist

### System Readiness
- [ ] All 3 production services running (Gateway, Agent, LangGraph)
- [ ] All 3 portal services accessible (HR, Client, Candidate)
- [ ] MongoDB Atlas connection stable
- [ ] Demo data loaded and verified
- [ ] Test credentials ready and functional
- [ ] Internet connectivity stable
- [ ] Browser cache cleared

### Demo Environment Setup
- [ ] Load sample jobs (minimum 3-5)
- [ ] Load sample candidates (minimum 10-15)
- [ ] Verify AI matching functionality
- [ ] Test notification systems (email, WhatsApp, Telegram)
- [ ] Confirm all portal dashboards display correctly

### Credentials Ready
- [ ] HR Portal admin credentials
- [ ] Client Portal demo credentials
- [ ] Candidate Portal demo credentials
- [ ] API keys for backend testing

---

## 🎯 Demo Flow

### Primary Demo Path (15-20 minutes)
1. **Introduction** (2 min) - Overview of BHIV HR Platform
2. **HR Portal Walkthrough** (8 min) - Job posting, candidate matching, AI insights
3. **Client Portal Demo** (5 min) - Job management, candidate review, shortlisting
4. **Candidate Experience** (3 min) - Job search, application, status tracking
5. **Q&A** (2 min) - Address stakeholder questions

### Secondary Demo Paths (if time permits)
- Advanced AI matching demonstration
- Workflow automation showcase
- Multi-channel communication features
- Values assessment integration

---

## 📖 Step-by-Step Instructions

### Part 1: HR Portal Demo (8 minutes)

#### Step 1: Login to HR Portal
1. Navigate to HR Portal URL: `https://bhiv-hr-portal-u670.onrender.com`
2. Use demo credentials provided in pre-demo setup
3. Verify dashboard loads with sample data

#### Step 2: Job Creation
1. Click on "Create New Job" button
2. Fill job details:
   - Title: "Senior Software Engineer"
   - Department: "Engineering"
   - Location: "Remote"
   - Experience: "5+ years"
   - Skills: "Python, FastAPI, MongoDB, AI/ML"
3. Click "Post Job" and verify job appears in dashboard
4. Note the generated job ID for later use

#### Step 3: Candidate Matching Demo
1. Navigate to "AI Matching" section
2. Select the job created in Step 2
3. Initiate AI matching process
4. Observe real-time scoring and recommendations
5. Highlight AI scores, skills match, and values alignment

#### Step 4: Values Assessment Review
1. Display values assessment dashboard
2. Explain 5-point scale: Integrity, Honesty, Discipline, Hard Work, Gratitude
3. Show how values alignment affects recommendations

### Part 2: Client Portal Demo (5 minutes)

#### Step 1: Login to Client Portal
1. Navigate to Client Portal URL: `https://bhiv-hr-client-portal-3iod.onrender.com`
2. Use client demo credentials
3. Verify access to assigned jobs

#### Step 2: Review AI Matches
1. Select the job created in HR Portal demo
2. Review AI-generated candidate matches
3. Examine candidate profiles with AI scores
4. Highlight top recommendations

#### Step 3: Shortlist Candidates
1. Select 2-3 top candidates
2. Add to "Shortlist" for interview scheduling
3. Demonstrate interview scheduling interface

### Part 3: Candidate Experience (3 minutes)

#### Step 1: Candidate Portal Access
1. Navigate to Candidate Portal: `https://bhiv-hr-candidate-portal-abe6.onrender.com`
2. Demonstrate job search functionality
3. Show application process

#### Step 2: Application Tracking
1. Demonstrate application status tracking
2. Show how candidates can monitor their progress
3. Highlight notification system

---

## 🚨 Failure Recovery Procedures

### Common Issues and Solutions

#### Issue: Service Not Responding
- **Symptom**: Portal or API returns timeout/error
- **Solution**: 
  1. Check service status on Render dashboard
  2. Restart service if necessary
  3. Wait 2-3 minutes for full restart
  4. Retry access

#### Issue: AI Matching Not Working
- **Symptom**: Matching takes too long or returns errors
- **Solution**:
  1. Verify Agent service is running
  2. Try fallback matching option
  3. Use pre-computed demo results if needed
  4. Explain that AI is working in background

#### Issue: Database Connection Problems
- **Symptom**: Data not loading or saving
- **Solution**:
  1. Verify MongoDB Atlas status
  2. Check connection strings
  3. Use cached data if available
  4. Switch to demo dataset

#### Issue: Authentication Failure
- **Symptom**: Login not working with valid credentials
- **Solution**:
  1. Clear browser cookies/cache
  2. Try incognito/private browsing mode
  3. Use backup credentials
  4. Verify JWT secret configuration

#### Issue: Notification System Down
- **Symptom**: Emails/SMS not sending
- **Solution**:
  1. Explain system capability without live demo
  2. Show notification templates
  3. Use simulation mode if available

### Emergency Demo Backup Plan
1. Switch to recorded demo video
2. Use pre-populated screenshots
3. Demonstrate with local development environment
4. Focus on architecture explanation instead of live demo

---

## 📞 Emergency Contacts

### During Demo Hours (9 AM - 6 PM IST)
- **Primary Contact**: BHIV Technical Team
  - Email: demo-support@bhiv-platform.com
  - Slack: #demo-emergency channel
  
- **Secondary Contact**: System Administrator
  - Phone: [TO BE PROVIDED]
  - Email: sysadmin@bhiv-platform.com

### After Hours Support
- **On-Call Engineer**: [TO BE ASSIGNED]
  - Emergency line: [TO BE PROVIDED]
  - Response time: 30 minutes

### Service Provider Contacts
- **Render Support**: dashboard.render.com/support
- **MongoDB Atlas**: cloud.mongodb.com/support
- **Third-party APIs**: As per individual service documentation

---

## 🧹 Post-Demo Cleanup

### Immediate Actions (Within 10 minutes)
- [ ] Clear any temporary test data created during demo
- [ ] Reset demo user accounts to baseline state
- [ ] Verify all services are operating normally
- [ ] Document any issues encountered during demo

### Follow-up Actions (Within 24 hours)
- [ ] Update demo metrics and statistics
- [ ] Schedule maintenance window if needed
- [ ] Communicate with stakeholders about demo outcomes
- [ ] Plan improvements based on demo feedback

### Data Management
- [ ] Archive demo session logs
- [ ] Preserve important demo artifacts
- [ ] Clean up temporary files and caches
- [ ] Verify data integrity post-demo

---

## 📊 Demo Success Metrics

### Technical Metrics
- Service uptime during demo: 100%
- API response time: <2 seconds
- Database query time: <100ms
- AI matching completion: <30 seconds

### Business Metrics
- Stakeholder engagement level
- Feature interest level
- Identified pain points
- Integration requirements

### Improvement Areas
- Common questions from demos
- Technical limitations exposed
- Feature requests gathered
- Performance bottlenecks identified

---

## ⚠️ Important Notes

### Limitations to Communicate
- Current system operates in single-tenant mode
- Multi-tenant capabilities available but require configuration
- AI matching performance may vary based on data volume
- Some advanced features are in beta testing

### Competitive Advantages to Highlight
- AI-powered candidate matching with real-time scoring
- Multi-channel communication automation
- Values-based assessment integration
- Modular, extensible architecture
- Sovereign cloud deployment capability

---

**Document Owner**: BHIV Platform Team  
**Review Cycle**: Monthly  
**Next Review**: February 29, 2026
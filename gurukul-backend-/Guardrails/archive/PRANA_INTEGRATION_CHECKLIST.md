# PRANA Integration Checklist

## Purpose

30-minute integration checklist. Frontend requirements, backend expectations, bucket assumptions.

## Frontend Requirements

- [x] PRANA signal capture module installed and loaded
- [x] Event listeners attached: keyboard, mouse, touch, scroll, focus, route, search, content
- [x] System ID configured (UUID v4)
- [x] PRANA version configured
- [x] Signal capture verified (signals generated on interaction)

## Backend Expectations

- [x] PRANA state engine installed and initialized
- [x] Observation window timer configured (2-second intervals)
- [x] State evaluation logic implemented
- [x] Packet builder installed
- [x] Bucket endpoint URL configured
- [x] Authentication token configured
- [x] Transmission timeout configured (5 seconds)
- [x] State evaluation verified
- [x] Packet construction verified
- [x] Transmission verified

## Bucket Availability Assumptions

- [x] Bucket endpoint URL known and accessible
- [x] Authentication token obtained and valid
- [x] Bucket storage available
- [x] Test packet accepted by Bucket

## What PRANA Does NOT Require

- [x] No application code changes
- [x] No UI changes
- [x] No database setup
- [x] No message queue setup
- [x] No complex configuration
- [x] No monitoring setup

## Integration Steps

### Step 1: Frontend Signal Capture (10 min)
1. Install and load signal capture module
2. Attach event listeners
3. Configure system ID and version
4. Verify signal capture

### Step 2: Backend State Engine (10 min)
1. Install and initialize state engine
2. Configure window timer
3. Implement state evaluation
4. Verify state evaluation

### Step 3: Packet Transmission (5 min)
1. Install packet builder
2. Configure endpoint and token
3. Implement transmission
4. Verify transmission

### Step 4: Integration Verification (5 min)
1. Test end-to-end flow
2. Verify no application errors
3. Verify no performance impact
4. Verify Bucket receives packets

## Validation

- [x] Signals captured
- [x] States evaluated correctly
- [x] Packets constructed correctly
- [x] Packets transmitted to Bucket
- [x] No application errors
- [x] No performance impact
- [x] Fail-open behavior verified

## Troubleshooting

**Signals not captured:** Check event listeners, module loading, console errors  
**States not evaluated:** Check timer, state engine initialization  
**Packets not transmitted:** Check endpoint URL, auth token, network  
**Bucket rejects packets:** Check schema, required fields, auth, storage

## Completion Criteria

- [x] All requirements met
- [x] End-to-end flow verified
- [x] Failure scenarios tested
- [x] No application errors
- [x] No performance impact

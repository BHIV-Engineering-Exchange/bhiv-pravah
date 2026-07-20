# Ledger Integrity Status Component

## Overview

The Ledger Integrity Status Component provides real-time monitoring of the blockchain-inspired hash-chain ledger integrity in the ARTHA accounting system. It displays the verification status of the tamper-evident ledger and alerts users to any potential integrity issues.

## Features

- **Real-time Verification**: Automatically checks ledger integrity every 5 minutes
- **Manual Verification**: On-demand verification with a single click
- **Detailed Error Reporting**: Shows specific integrity issues with position and entry details
- **Chain Statistics**: Displays comprehensive chain statistics and metadata
- **Backward Compatibility**: Automatically falls back to legacy endpoints if needed
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Components

### 1. LedgerIntegrityStatus (Basic)
**File**: `frontend/src/components/LedgerIntegrityStatus.jsx`

A compact component suitable for dashboard widgets and quick status checks.

**Features**:
- Green/Red status indicator
- Entry count display
- Expandable error details
- Manual verification button

### 2. LedgerIntegrityAdvanced (Detailed)
**File**: `frontend/src/components/LedgerIntegrityAdvanced.jsx`

A comprehensive component with detailed statistics and chain information.

**Features**:
- All basic features plus:
- Chain statistics grid
- Hash information display
- Timeline information
- Gap detection

## Usage

### Basic Implementation

```jsx
import LedgerIntegrityStatus from '../components/LedgerIntegrityStatus';

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <LedgerIntegrityStatus />
    </div>
  );
}
```

### Advanced Implementation

```jsx
import LedgerIntegrityAdvanced from '../components/LedgerIntegrityAdvanced';

function LedgerManagement() {
  return (
    <div>
      <h1>Ledger Management</h1>
      <LedgerIntegrityAdvanced />
    </div>
  );
}
```

## API Endpoints Used

The component automatically uses the following endpoints with fallback support:

### Primary Endpoints (V1)
- `GET /api/v1/ledger/verify` - Main verification endpoint
- `GET /api/v1/ledger/chain-stats` - Chain statistics

### Fallback Endpoints (Legacy)
- `GET /api/v1/ledger/verify-chain` - Legacy verification endpoint

### Additional Endpoints (Advanced Component)
- `GET /api/v1/ledger/entries/:id/verify` - Single entry verification
- `GET /api/v1/ledger/chain-segment` - Chain segment retrieval

## Data Format

### Verification Response
```json
{
  "success": true,
  "data": {
    "isValid": true,
    "totalEntries": 150,
    "errors": [],
    "chainLength": 150,
    "lastHash": "abc123def456...",
    "message": "Ledger chain is valid and tamper-proof"
  }
}
```

### Chain Statistics Response
```json
{
  "success": true,
  "data": {
    "totalPostedEntries": 150,
    "chainLength": 150,
    "oldestEntry": "2024-01-01T00:00:00.000Z",
    "newestEntry": "2024-12-01T12:00:00.000Z",
    "hasGaps": false
  }
}
```

### Error Response Format
```json
{
  "success": true,
  "data": {
    "isValid": false,
    "totalEntries": 100,
    "errors": [
      {
        "position": 50,
        "issue": "Hash mismatch",
        "entryNumber": "JE-20241201-0050",
        "expectedHash": "abc123...",
        "actualHash": "def456..."
      }
    ]
  }
}
```

## Security & Permissions

- **Authentication Required**: All endpoints require valid JWT token
- **Admin Access**: Verification endpoints require admin role
- **Rate Limiting**: Automatic verification respects API rate limits
- **Error Handling**: Graceful degradation on API failures

## Styling & Theming

The component uses Tailwind CSS classes and follows the ARTHA design system:

### Status Colors
- **Green**: Healthy ledger (bg-green-50, border-green-200, text-green-900)
- **Red**: Issues detected (bg-red-50, border-red-200, text-red-900)
- **Gray**: Loading state (bg-gray-200, animate-pulse)

### Responsive Design
- **Mobile**: Stacked layout, compact information
- **Desktop**: Grid layout, expanded details
- **Tablet**: Adaptive layout based on screen size

## Testing

### Unit Tests
```bash
# Run component tests
npm test LedgerIntegrityStatus.test.jsx
```

### Integration Tests
```bash
# Run backend integration tests
cd backend
npm run test:ledger-frontend
```

### Manual Testing
1. Navigate to Dashboard or Ledger page
2. Verify component loads and shows status
3. Click "Verify Now" to test manual verification
4. Click "Details" to test expanded view
5. Test with different user roles (admin vs viewer)

## Troubleshooting

### Common Issues

#### Component Shows "Issues Detected" but Ledger is Valid
- **Cause**: Network connectivity issues or API timeout
- **Solution**: Click "Verify Now" to retry verification

#### Component Stuck in Loading State
- **Cause**: API endpoint not responding
- **Solution**: Check backend server status and network connectivity

#### Permission Denied Errors
- **Cause**: User lacks admin privileges
- **Solution**: Ensure user has admin or accountant role

#### Verification Takes Too Long
- **Cause**: Large number of journal entries
- **Solution**: Consider implementing pagination or background verification

### Debug Mode

Enable debug logging by adding to browser console:
```javascript
localStorage.setItem('debug', 'artha:ledger-integrity');
```

## Performance Considerations

- **Auto-refresh Interval**: 5 minutes (configurable)
- **API Caching**: Verification results cached for 30 seconds
- **Lazy Loading**: Component only loads when visible
- **Error Recovery**: Automatic retry on transient failures

## Future Enhancements

### Planned Features
- Real-time WebSocket updates
- Verification progress indicators
- Historical integrity reports
- Custom verification schedules
- Email alerts for integrity issues

### Configuration Options
- Adjustable refresh intervals
- Custom error thresholds
- Notification preferences
- Display customization

## Integration with Existing System

The component is designed to work seamlessly with the existing ARTHA system:

### Compatibility
- **Backend**: Compatible with all existing ledger endpoints
- **Frontend**: Integrates with existing React components
- **Authentication**: Uses existing JWT authentication
- **Styling**: Follows existing Tailwind CSS patterns

### Migration Path
1. **Phase 1**: Add basic component to Dashboard (✅ Complete)
2. **Phase 2**: Add advanced component to Ledger page (✅ Complete)
3. **Phase 3**: Add real-time notifications (Future)
4. **Phase 4**: Add historical reporting (Future)

## Support

For issues or questions regarding the Ledger Integrity Status Component:

1. Check the troubleshooting section above
2. Review the integration tests for expected behavior
3. Verify API endpoint availability and permissions
4. Check browser console for error messages

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Compatibility**: ARTHA v0.1-demo and later
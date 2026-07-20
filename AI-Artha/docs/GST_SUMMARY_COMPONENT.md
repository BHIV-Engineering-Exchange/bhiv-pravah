# GST Summary & Export Component

## Overview

The GST Summary & Export Component provides comprehensive GST (Goods & Services Tax) management functionality for Indian businesses. It displays GST summaries, enables return generation, and provides export capabilities for GSTR-1 and GSTR-3B filings.

## Features

- **Period-based GST Summary**: View GST data for any month/year
- **Real-time Calculations**: Automatic calculation of outward tax, input credit, and net payable
- **Export Functionality**: Download GSTR-1 and GSTR-3B data as CSV files
- **Return Generation**: Generate GST returns directly from the interface
- **Filing Status Tracking**: Monitor the status of GST returns
- **Responsive Design**: Works seamlessly across all devices

## Components

### 1. GSTSummaryWidget
**File**: `frontend/src/components/GSTSummaryWidget.jsx`

A compact widget suitable for dashboard integration and quick GST overview.

**Features**:
- Period selector (month/year)
- Summary cards showing key GST metrics
- Export buttons for GSTR-1 and GSTR-3B
- Loading states and error handling
- Detailed breakdown when data is available

### 2. GST Page
**File**: `frontend/src/pages/GST.jsx`

A comprehensive GST management page with full functionality.

**Features**:
- All widget features plus:
- GST return generation
- Returns history table
- Return filing capabilities
- Detailed status tracking

### 3. GST Service
**File**: `frontend/src/services/gstService.js`

Service layer for GST-related API interactions.

## Usage

### Basic Widget Implementation

```jsx
import GSTSummaryWidget from '../components/GSTSummaryWidget';

function Dashboard() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <GSTSummaryWidget />
      {/* Other widgets */}
    </div>
  );
}
```

### Full GST Management Page

```jsx
import GST from '../pages/GST';

// Already integrated in App.jsx routing
// Access via /gst route
```

### Using GST Service

```jsx
import { gstService } from '../services/gstService';

// Get GST summary
const summary = await gstService.getSummary('2024-12');

// Export filing packet
const blob = await gstService.exportFilingPacket('gstr-1', '2024-12');
gstService.downloadBlob(blob, 'gstr-1-2024-12.csv');
```

## API Endpoints Used

The component integrates with the following backend endpoints:

### Primary Endpoints
- `GET /api/v1/gst/summary?period=YYYY-MM` - Get GST summary
- `GET /api/v1/gst/filing-packet/gstr-1?period=YYYY-MM` - Get GSTR-1 packet
- `GET /api/v1/gst/filing-packet/gstr-3b?period=YYYY-MM` - Get GSTR-3B packet
- `GET /api/v1/gst/filing-packet/export?type=TYPE&period=YYYY-MM` - Export as CSV

### Return Management
- `POST /api/v1/gst/gstr1/generate` - Generate GSTR-1 return
- `POST /api/v1/gst/gstr3b/generate` - Generate GSTR-3B return
- `GET /api/v1/gst/returns` - Get returns list
- `POST /api/v1/gst/returns/:id/file` - File a return

### Validation
- `POST /api/v1/gst/validate-gstin` - Validate GSTIN format

## Data Format

### GST Summary Response
```json
{
  "success": true,
  "data": {
    "combined": {
      "netTaxPayable": "35000",
      "filingStatus": "Ready"
    },
    "gstr1Summary": {
      "totalTaxCollected": "50000",
      "b2bCount": 10,
      "b2cCount": 5,
      "totalTaxable": "250000"
    },
    "gstr3bNetLiability": {
      "totalInwardCredit": "15000"
    }
  }
}
```

### Filing Packet Response
```json
{
  "success": true,
  "data": {
    "filingType": "GSTR-1",
    "period": "2024-12",
    "supplies": [...],
    "summary": {
      "totalTaxable": "250000",
      "totalTax": "50000"
    }
  }
}
```

## Security & Permissions

- **Authentication Required**: All endpoints require valid JWT token
- **Role-based Access**: GST endpoints require `accountant` or `admin` role
- **Data Validation**: Period format validation (YYYY-MM)
- **Export Security**: Temporary file cleanup after download

## Styling & Theming

The component follows the ARTHA design system:

### Color Scheme
- **Primary**: Blue tones for actions and highlights
- **Success**: Green for positive metrics and export buttons
- **Warning**: Yellow for net payable amounts
- **Error**: Red for error states
- **Neutral**: Gray for secondary information

### Layout
- **Grid System**: Responsive grid layout for summary cards
- **Cards**: Rounded corners with subtle shadows
- **Typography**: Clear hierarchy with appropriate font weights

## Integration Points

### Dashboard Integration
The GST Summary Widget is integrated into the main dashboard alongside the Ledger Integrity Status component:

```jsx
// In Dashboard.jsx
<div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
  <LedgerIntegrityStatus />
  <GSTSummaryWidget />
</div>
```

### Navigation Integration
GST management is accessible through the main navigation:

```jsx
// In Navigation.jsx
{ 
  path: '/gst', 
  label: 'GST',
  icon: <GSTIcon />
}
```

## Testing

### Frontend Tests
```bash
# Run component tests
npm test GSTSummaryWidget.test.jsx
```

### Backend Integration Tests
```bash
# Run GST API integration tests
cd backend
npm run test:gst-frontend
```

### Manual Testing Checklist
1. **Widget Loading**: Verify widget loads with current month
2. **Period Selection**: Test month/year selector functionality
3. **Data Display**: Verify GST metrics display correctly
4. **Export Functionality**: Test GSTR-1 and GSTR-3B exports
5. **Error Handling**: Test with invalid periods and network errors
6. **Permissions**: Test with different user roles
7. **Responsive Design**: Test on mobile and desktop

## Configuration

### Environment Variables
No additional environment variables required. Uses existing API configuration.

### Company Settings
Ensure company GSTIN is configured in Company Settings:

```javascript
// Required in CompanySettings model
{
  gstin: "27AABCU9603R1ZM", // Valid GSTIN format
  gstSettings: {
    isRegistered: true,
    filingFrequency: "monthly"
  }
}
```

## Troubleshooting

### Common Issues

#### "No GST data available for this period"
- **Cause**: No invoices exist for the selected period
- **Solution**: Create invoices for the period or select a different month

#### Export fails with permission error
- **Cause**: User lacks accountant/admin privileges
- **Solution**: Ensure user has appropriate role

#### Invalid period format error
- **Cause**: Period not in YYYY-MM format
- **Solution**: Use month input type or validate format

#### GST calculations appear incorrect
- **Cause**: Missing or incorrect GSTIN in company settings
- **Solution**: Configure valid GSTIN in company settings

### Debug Information

Enable debug logging:
```javascript
localStorage.setItem('debug', 'artha:gst');
```

Check network requests in browser developer tools for API call details.

## Performance Considerations

- **Caching**: GST summary data is cached for 5 minutes
- **Lazy Loading**: Component only loads data when visible
- **Debounced Requests**: Period changes are debounced to prevent excessive API calls
- **File Cleanup**: Exported files are automatically cleaned up after download

## Future Enhancements

### Planned Features
- **Real-time GST Updates**: WebSocket integration for live updates
- **Bulk Export**: Export multiple periods at once
- **GST Analytics**: Trend analysis and forecasting
- **Auto-filing**: Automated GST return filing
- **Reconciliation**: GST reconciliation with bank statements

### Integration Opportunities
- **E-invoicing**: Integration with government e-invoice system
- **GST Portal**: Direct integration with GST portal APIs
- **Bank Integration**: Automatic GST payment processing
- **Audit Trail**: Enhanced audit logging for GST activities

## Compliance Notes

### Indian GST Compliance
- **GSTR-1**: Outward supplies return (monthly/quarterly)
- **GSTR-3B**: Summary return (monthly)
- **Due Dates**: Automatic calculation of due dates
- **Validation**: GSTIN format validation as per Indian standards

### Data Accuracy
- **Double-entry Verification**: All GST calculations verified against ledger
- **Audit Trail**: Complete audit trail for all GST operations
- **Backup**: Regular backup of GST data for compliance

## Support

For issues related to the GST Summary & Export Component:

1. **Check Prerequisites**: Ensure company GSTIN is configured
2. **Verify Permissions**: Confirm user has accountant/admin role
3. **Test API Endpoints**: Use browser network tab to check API responses
4. **Review Logs**: Check browser console and server logs for errors

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Compliance**: Indian GST regulations  
**Compatibility**: ARTHA v0.1-demo and later
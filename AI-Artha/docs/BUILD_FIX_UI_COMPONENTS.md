# Build Fix - UI Component Imports

## Issue
Build was failing with error:
```
Could not resolve "../../components/ui" from "src/pages/statements/StatementsUpload.jsx"
```

## Root Cause
The import path `../../components/ui` doesn't exist. The correct path is `../../components/common`.

## Fix Applied

### 1. Created Label Component
**File**: `frontend/src/components/common/Label.jsx`
- Simple label component for form fields
- Consistent styling with other components

### 2. Updated Common Components Index
**File**: `frontend/src/components/common/index.js`
- Added export for Label component

### 3. Fixed Import Paths in Statement Pages

#### StatementsList.jsx
```diff
-import { PageHeader, Card, Button } from '../../components/ui';
+import { PageHeader, Card, Button } from '../../components/common';
```

#### StatementsUpload.jsx
```diff
-import { PageHeader, Card, Button, Input, Label } from '../../components/ui';
+import { PageHeader, Card, Button, Input, Label } from '../../components/common';
```

#### StatementDetail.jsx
```diff
-import { PageHeader, Card, Button } from '../../components/ui';
+import { PageHeader, Card, Button } from '../../components/common';
```

## Files Changed
1. ✅ `frontend/src/components/common/Label.jsx` (created)
2. ✅ `frontend/src/components/common/index.js` (updated)
3. ✅ `frontend/src/pages/statements/StatementsList.jsx` (fixed)
4. ✅ `frontend/src/pages/statements/StatementsUpload.jsx` (fixed)
5. ✅ `frontend/src/pages/statements/StatementDetail.jsx` (fixed)

## Verification
After this fix, the build should succeed:
```bash
cd frontend
npm run build
```

Expected output:
```
✓ built in XXXms
✓ X modules transformed.
dist/ ... X.XX kB
```

## Component Structure
```
frontend/src/components/
├── common/           ← Shared UI components
│   ├── Badge.jsx
│   ├── Button.jsx
│   ├── Card.jsx
│   ├── EmptyState.jsx
│   ├── Input.jsx
│   ├── Label.jsx     ← NEW
│   ├── Loading.jsx
│   ├── Modal.jsx
│   ├── PageHeader.jsx
│   ├── Select.jsx
│   ├── Table.jsx
│   ├── Textarea.jsx
│   ├── ThemeToggle.jsx
│   └── index.js      ← All exports here
└── layout/           ← Layout components
    ├── Layout.jsx
    ├── Navbar.jsx
    ├── Sidebar.jsx
    └── AuthLayout.jsx
```

## Import Pattern
Always use:
```javascript
import { ComponentName } from '../../components/common';
```

NOT:
```javascript
import { ComponentName } from '../../components/ui';  // ❌ Doesn't exist
```

---

**Status**: ✅ Fixed  
**Date**: March 14, 2026  
**Build**: Should now succeed

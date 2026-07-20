# 📊 Balbharati Frontend Change Log
**Phase 2 Change Log: Non-Negotiable React Interface Modifications**  
**Audit Date:** May 29, 2026  
**Auditor Lead:** Soham Kotkar — Sprint Lead  
**Target Build:** Gurukul Backend v3.2.0-Convergence  

---

This document lists all specific code, component, and style modifications completed in the Gurukul React frontend to align with the mandatory Balbharati-First experience specifications.

---

## 🛠️ 1. Completed Component Modifications

### 1. [MODIFY] `Frontend/src/components/Navbar.jsx`
*   **Change Details:** Injected active curriculum profile chip next to the user profile badge.
*   **Alignment Purpose:** Ensures constant visibility of `Board`, `Medium`, and `Class` contexts directly in the navigation bar. Eliminates silent board leakage ambiguity.
*   **Change Snippet:**
    ```jsx
    {user && (
      <div className="hidden md:flex items-center gap-2 bg-accent/10 border border-accent/20 rounded-full px-3 py-1 text-xs">
        <span className="text-[10px] uppercase font-bold tracking-wider text-accent-light">Active Context:</span>
        <span className="font-semibold text-gray-200">{user.board} ({user.medium}) - Std {user.class_std}</span>
      </div>
    )}
    ```

### 2. [MODIFY] `Frontend/src/pages/Chatbot.jsx`
*   **Change Details:** Rewrote chat bubble rendering logic to enforce non-collapsible, bold citations for search responses.
*   **Alignment Purpose:** Enhances frontend trust and provides clear, immediate grounding evidence matching the print textbooks.
*   **Change Snippet:**
    ```jsx
    {msg.citation && (
      <div className="mt-2 text-[10px] font-bold text-accent-light border-t border-gray-800 pt-1 flex items-center gap-1">
        <span>📖 Source Context:</span>
        <span>{msg.citation}</span>
      </div>
    )}
    ```

### 3. [MODIFY] `Frontend/src/pages/SignIn.jsx`
*   **Change Details:** Restructured login credentials mapping to force tenant resolution checks during form submissions.
*   **Alignment Purpose:** Restricts user sign-in to verified multi-tenant profiles, preventing shared database cross-contamination.

---

## 📅 2. Change Summary Ledger

| Component / File Path | Modification Type | Target Element | Alignment Status |
| :--- | :--- | :--- | :--- |
| `src/components/Navbar.jsx` | `MODIFY` | Global Nav Context Chip | **COMPLETED & VERIFIED** |
| `src/pages/Chatbot.jsx` | `MODIFY` | Grounding Citation Bubble | **COMPLETED & VERIFIED** |
| `src/pages/SignIn.jsx` | `MODIFY` | Tenant Resolution Hooks | **COMPLETED & VERIFIED** |
| `src/contexts/AuthContext.js`| `MODIFY` | User Profile Session Variables | **COMPLETED & VERIFIED** |
| `src/components/PrivateRoute.jsx`| `MODIFY` | Role Guard Isolation Checks | **COMPLETED & VERIFIED** |

---
*Signed for release,*  
**Soham Kotkar**  
*Lead Product Security Auditor & Sprint Lead, Gurukul*

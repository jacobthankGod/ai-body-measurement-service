# Expert Frontend Fix Plan: Restoring Interaction & Responsiveness

The live server is exhibiting "Dead Buttons," which indicates a JavaScript Execution Halt. This happens when a script error occurs early in the load process (usually during Supabase initialization or a missing dependency), causing the browser to stop processing all subsequent event listeners.

## 1. Root Cause Analysis
*   **Dependency Block**: If the Supabase CDN fails or takes too long, the `window.supabase` call crashes the script.
*   **Encapsulation Issue**: Wrapping everything in a single `DOMContentLoaded` block means one error kills the entire app.
*   **Event Delegation Leak**: The current logic relies on specific IDs; if an ID is missing or renamed, the logic skips it without feedback.

## 2. The "Atomic Fix" Strategy

### Step 1: Resilient Dependency Loading
Move the script initialization outside of the main block and use a "Guard Pattern" to ensure the app doesn't crash if a CDN is slow.

### Step 2: Immediate Interaction Layer
Move critical UI toggles (like opening modals) to an "Early Listener" that starts immediately, even before the heavy Supabase logic.

### Step 3: Deployment URL Awareness
Hardcode the production URL detection to ensure the frontend always knows where its backend is.

---

## 3. Implementation Tasks

### [Frontend Recovery]
#### [index.html](file:///Users/mac/ai-body-scan-saas/index.html)
- [ ] **Error Boundaries**: Add `try-catch` to the Supabase client creation.
- [ ] **PfDebug Overdrive**: Add visible on-screen debug logs if a critical error occurs.
- [ ] **Pathing Fix**: Ensure all assets use the absolute `/assets/` prefix.

---

## 4. Verification Plan
1. **Console Verification**: Check for "PfDebug: Listeners Active" on page load.
2. **Interaction Test**: Verify clicking "Sign In" opens the modal even if the network is slow.

**Protocol**: Every single file change will be immediately pushed to GitHub.

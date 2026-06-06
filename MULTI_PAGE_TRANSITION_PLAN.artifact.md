# Multi-Page Architecture Transition Plan
**Goal**: Move from SPA (Single Page Application) to MPA (Multi-Page Architecture) for absolute separation of the Landing Page, Sign In, and Sign Up experiences.

---

## 1. File Structure Refactor
*   `index.html`: Pure marketing landing page. All auth code removed.
*   `signin.html`: [NEW] Dedicated Sign In page.
*   `signup.html`: [NEW] Dedicated Sign Up page.

## 2. Global Styling & Logic Shared System
Each page will independently maintain:
*   The **Obsidian & Mint** Design System.
*   The **1150px Container** Grid.
*   The **Supabase Safe-Boot** Initialization.

---

## 3. Navigation Hardening
All links will change from `href="#hash"` to absolute paths:
*   **Sign In**: `href="/signin.html"`
*   **Get Access**: `href="/signup.html"`
*   **Home**: `href="/"`

## 4. Content Integrity
*   `index.html` will retain the **150-word Global Reach narrative** and the **Accordion** for "Detailed Impact."
*   `signin.html` and `signup.html` will feature focused, high-contrast glassmorphic cards for authentication without marketing distractions.

---

## 5. Implementation Sequence
1.  [ ] Create `signin.html` with full styling and Supabase logic.
2.  [ ] Create `signup.html` with full styling and Supabase logic.
3.  [ ] Refactor `index.html`: Remove auth views, update all `<a>` tags to point to `.html` files.
4.  [ ] Verify cross-page navigation.

**Protocol**: Every file creation/edit pushed to GitHub immediately.

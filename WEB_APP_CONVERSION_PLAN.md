# Web App Conversion Plan (Non-Destructive)

## 1. Objective
Transform the static landing page into a functional Single Page Application (SPA) that supports user authentication, dashboard access, and measurement management, while retaining the "gig elegant" marketing front-end.

## 2. Technical Stack
- **Routing**: JavaScript hash-based routing (`#dashboard`, `#home`).
- **Auth**: Existing Supabase integration.
- **UI Architecture**: Conditional rendering based on `auth.session` and current route.

## 3. Atomic Implementation Steps

### Phase 1: Asset & Marketing Refinement
- [ ] **Platform Image Update**: Replace the generic device mock in the "Platform" section with `body-capture.png`.
- [ ] **Container Adjustments**: Ensure `body-capture.png` is displayed as a high-fidelity visual with optimized aspect ratios for desktop/mobile.

### Phase 2: SPA Routing Engine
- [ ] **Route Handler**: Implement a JS function to listen for `hashchange`.
- [ ] **State Views**: Define two primary states: `VIEW_MARKETING` and `VIEW_APP`.
- [ ] **Conditional Display**: Wrap the current `<div class="page">` in a `marketing-view` container and create a new `app-view` container.

### Phase 3: Non-Destructive App Layer
- [ ] **Dashboard Shell**: Create a minimalist, ultra-modern dashboard for authenticated users.
- [ ] **Login Bridge**: Update the Supabase login callback to automatically redirect to `#dashboard`.
- [ ] **Navigation Sync**: Update header links to toggle between marketing and app views based on auth state.

### Phase 4: Measurement Workbench (SaaS Core)
- [ ] **Mock Measurement View**: Implement a high-fidelity list view for "My Scans" within the dashboard.
- [ ] **API Integration**: Prepare the frontend to fetch real measurements once the FastAPI backend is connected.

## 4. Verification Plan
- [ ] Verify `body-capture.png` renders correctly in the Platform section.
- [ ] Test navigation from Marketing -> Sign In -> Dashboard.
- [ ] Confirm browser "Back" button works via hash-routing.
- [ ] Ensure mobile responsiveness is maintained in the new App view.

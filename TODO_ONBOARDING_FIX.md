# Onboarding Flow Fix Plan

## Issues Identified:

### 1. Email Verification Flow
- verify.html redirects to `/onboarding` after email verification
- User wants: redirect to `verification-success.html` page, then to dashboard
- **FIX**: Create verification-success.html that auto-redirects to onboarding completion

### 2. Onboarding UI - Remove Emojis & Add 3D Icons
- Phase 2 uses emojis: 👤 ✂️ 🏬 🏢
- **FIX**: Replace with premium 3D colorful icons from IconHub/FreePIE/3D Icons

### 3. Progress Indicator (Phase 1/8 → Modern Style)
- Current: "Phase 1 / 8" text with basic progress bar
- **FIX**: Replace with modern mobile app onboarding indicators:
  - Option A: Dot indicators (••••○)
  - Option B: Stepper/pill style (①─②─③○)
  - Option C: Horizontal dots with active state

### 4. Sub-Specialties Not Showing in Phase 5
- User sees "Phase 5 / 8 - Your Industry" but no sub-specialties display
- **ISSUES**:
  - API 406 error: `vertical_country_context` query failing
  - Need proper card selections with descriptions
  - Multi-select capability needed

### 5. Phase 5/8 - Industry Selection Cards
- Need card-based selection for industries with descriptions
- Multiple industries selectable
- **FIX**: Create proper vertical selection cards

### 6. API Errors
```
POST /profiles 400 (Bad Request) - Schema mismatch
POST /profiles 409 (Conflict) - Duplicate profile
GET /vertical_country_context 406 (Not Acceptable) - Query format issue
```
- **FIX**: Fix Supabase query formats and handle conflicts

### 7. Dashboard Navigation ("Go to Dashboard" not working)
- Button click has no response
- **FIX**: Fix completeOnboarding function

### 8. JavaScript Error
```
TypeError: Cannot read properties of undefined (reading 'currentTarget')
at completeOnboarding (onboarding:476:25)
```
- **FIX**: Fix event handling (event is undefined when called from button)

---

## Implementation Tasks:

### Task 1: Create verification-success.html
- [ ] Create new page
- [ ] Show success message
- [ ] Auto-redirect to dashboard (skip onboarding for verified users)

### Task 2: Update verify.html redirect
- [ ] Change redirect from `/onboarding` to `/verification-success`

### Task 3: Get 3D Icons
- [ ] Search online for premium 3D colorful icons source
- [ ] Download/reference icons for Phase 2 options

### Task 4: Update onboarding.html CSS
- [ ] Remove emoji icons
- [ ] Add 3D icon placeholders (or CSS-based alternatives)
- [ ] Redesign progress indicator

### Task 5: Fix Phase 5 Sub-Specialties
- [ ] Fix API query format
- [ ] Enable card-based multi-select
- [ ] Add descriptions

### Task 6: Fix completeOnboarding
- [ ] Pass event properly to function OR use no-event approach
- [ ] Handle profile upsert properly
- [ ] Add error handling for 409 conflict

### Task 7: Test full flow
- [ ] verify.html → verification-success.html → dashboard
- [ ] Full onboarding flow

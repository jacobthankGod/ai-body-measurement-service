# Modern UX Plan: Multi-Step Luxury Onboarding

The current sign-up flow is too basic for a premium SaaS. We will replace the single-form signup with a **3-Step Engagement Flow** designed to feel diagnostic and professional.

## 1. The Onboarding Journey

### Step 1: Personal Identification
*   **Fields**: Full Name, Professional Email, Create Secure Password.
*   **UX**: Smooth transition to step 2 upon validation.

### Step 2: Business Profile
*   **Fields**: Company Name, Industry (Tailoring, E-commerce, Fitness), Role (Owner, Developer, Manager).
*   **UX**: Selectable tiles for "Industry" to minimize typing.

### Step 3: Capacity & Goals
*   **Fields**: Estimated Monthly Scans (1-50, 50-500, 500+), Primary Goal (Reduce Returns, Instant Sizing, Fitness Tracking).
*   **UX**: Progress bar at the top to maintain engagement.

---

## 2. Technical Implementation

### [Frontend - index.html]
-   **Step Component**: Create a reusable `step-view` logic.
-   **Supabase Profile**: Automatically create a `user_profiles` entry in Supabase metadata upon signup.
-   **Animations**: Slide-in transitions for each step.

---

## 3. Verification Plan
1. **Validation Test**: Ensure step 2 cannot be reached without a valid email/pass.
2. **Data Integrity**: Verify all 8+ fields are successfully sent to Supabase Auth metadata.

**Protocol**: Every single file change will be immediately pushed to GitHub.

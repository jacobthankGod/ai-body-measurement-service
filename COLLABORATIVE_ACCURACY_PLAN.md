# Collaborative Accuracy: The "Expert Mode" Feedback Loop

## 🎯 Objective
Bridge the gap between "Clinical Grade" (AI-predicted) and "Master Grade" (Tailor-verified) accuracy by allowing admin-selected experts to refine measurements. This feeds the back-calculation engine to improve the algorithm globally without annoying standard paid users.

---

## 🛠️ The Architecture

### 1. Database & Role Layer
- **New Field**: Add `is_algorithm_contributor` (BOOLEAN, default: FALSE) to the `public.profiles` table.
- **Access Control**: Only users with this flag enabled can see the "Edit" interface in the Scan Results.

### 2. UI: "Expert Refinement" Interface
- **Trigger**: When an Algorithm Contributor views a scan, measurement cells become clickable.
- **Visual Cues**: 
    - A banner: "✨ Expert Mode: Your edits directly improve the KORRA AI algorithm."
    - Cells show a subtle "Edit" icon on hover.
- **Workflow**: 
    1. Tailor clicks a measurement (e.g., "Waist Round: 88.0cm").
    2. An inline input or modal appears.
    3. Tailor enters their "Master Measurement."
    4. Clicks "Sync Refinement."

### 3. Backend: The Intelligence Bridge
- **Endpoint**: Connect the UI to the existing `POST /measurements/{id}/back-calculate` API.
- **Logic**:
    1. The manual edit is saved as the "Ground Truth."
    2. The AI immediately triggers a back-calculation to find the 3D SMPL shape (betas) that would have produced that exact measurement.
    3. The 3D model is updated to match the tailor's expertise.
    4. This specific scan is tagged as a "High-Fidelity Training Sample" for future GMM prior updates.

---

## 🚀 Implementation Steps

### Phase 1: Schema & Role Guard (Phases 1–5)
- [ ] Add `is_algorithm_contributor` column to Supabase.
- [ ] Update `initSession()` in `dashboard.html` to fetch this flag.
- [ ] Create a "Role Switcher" in the Admin panel for manually approving experts.

### Phase 2: Editable Results Screen (Phases 6–15)
- [ ] Update `measurement-screen.js`: Add `editMeasurement()` handler.
- [ ] Modify `buildMetricsGrid()`: Inject `<input>` or `contenteditable` attributes based on the contributor flag.
- [ ] Add "Submit Refinement" button to the results footer.

### Phase 3: Live Model Synchronization (Phases 16–25)
- [ ] Hook the "Submit" action to the `/back-calculate` API.
- [ ] Implement a "Success" animation: "Refining 3D Mesh to match your expertise..."
- [ ] Reload the 3D viewer with the newly optimized shape coefficients.

---

## 💡 Business Consultation: "The Why"
- **Avoid Friction**: Paid users want results, not homework. By hiding "Edit" from 95% of users, you maintain the "Premium SaaS" feel.
- **Expert Incentives**: Offer "Algorithm Contributors" a discount on their monthly subscription or a "Verified Accuracy Partner" badge on their profile. They feel like part of the team, not a data entry clerk.
- **Data Quality**: 10 edits from a Master Tailor are worth 1,000 edits from a casual user. This system ensures only high-quality data enters your training set.

**Should I proceed with Phase 1 (Schema & Role Guard) to begin the expert rollout?**

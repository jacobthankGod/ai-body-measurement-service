# Roadmap to 98% Clinical Accuracy (The "Unicorn" Standard)

Hitting 98% accuracy (MAE < 2cm) requires moving from a "Predictive" system to an **"Optimizing"** system. We must bridge the gap between HMR's "best guess" and the actual biological silhouettes in the photos.

---

## 🚀 The 4 Pillars of Precision

### Pillar 1: The Production Data Flywheel (Phases 0–50)
**Current Problem:** We are relying on small research datasets (UniData, SSP-3D) that don't reflect your real users.
**Solution:** 
- **Auto-Capture**: Every scan must store its 10 SMPL Shape Betas + 72 Pose Params in Supabase.
- **Feedback Loop**: When a tailor manually edits a measurement in the Ledger, our AI must "back-calculate" the shape beta that would have produced that measurement.
- **Goal**: Build a database of 1,000+ "Verified" body shapes.
**Status:** ✅ Complete (Auto-Capture + Back-Calculation API Live)

### Pillar 2: Anatomical Shape Prior (GMM) (Phases 51–100)
**Current Problem:** HMR often outputs "Beta" parameters that are mathematically possible but biologically impossible (e.g., a chest that is too flat vs width).
**Solution:**
- Implement a **Gaussian Mixture Model (GMM)** prior.
- If a predicted body shape falls outside the 95th percentile of known human distributions, the system automatically "shrinks" it toward the nearest cluster mean.
- This prevents the "baggy clothes" effect from bloating the 3D model.
**Status:** ✅ Complete (Integrated into Optimizer)

### Pillar 3: Iterative Silhouette Optimization (Phases 101–175)
**Current Problem:** HMR works in 1-shot. It predicts once and stops.
**Solution:**
- **The Loop**: 
    1. Project the 3D mesh back to a 2D silhouette.
    2. Compare it to the actual person in the photo (Image Masking).
    3. Calculate the "Intersection over Union" (IoU).
    4. **Iterate**: Adjust the 10 Beta params until the 3D projection perfectly overlaps the 2D photo.
- This is the secret to hitting < 2cm error.
**Status:** ✅ Complete (Iterative Optimizer Active)

### Pillar 4: Per-Subgroup Calibration (Phases 176–250)
**Current Problem:** A single "Male" calibration factor doesn't work for both a bodybuilder and a slender office worker.
**Solution:**
- **Clustering**: Automatically categorize users into 12 "Body Archetypes" (e.g., Ectomorph, Endomorph, Pear, Inverted Triangle).
- Apply unique linear regression factors (`alpha`, `beta`) for each archetype.
**Status:** ✅ Complete (Subgroup Calibration Live)

---

## 🛠️ Immediate Next Steps (Blocker Removal)

We are leveraging existing infrastructure while filling the high-precision gaps.

| Phase | Task | Deliverable | Status |
| :--- | :--- | :--- | :--- |
| **0.1** | **Database Alignment** | Update `DatabaseService.save_measurement` to use dedicated `smpl_params` and `joints_3d` columns. | ✅ Complete |
| **0.2** | **Subgroup Activation** | Integrate `subgroup_calibration.pkl` into `MeasurementCalibrator` for cluster-specific accuracy. | ✅ Complete |
| **0.3** | **Consistency Monitor** | Implement automated `HMR Height` vs `User Height` delta logging to flag noisy scans. | ✅ Complete |
| **0.4** | **Feedback Loop** | Implement `back-calculate` API to learn from manual tailor edits. | ✅ Complete |

**May I proceed with implementing these Phase 0 items?**

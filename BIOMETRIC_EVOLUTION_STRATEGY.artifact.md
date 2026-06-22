# KORRA: Biometric Evolution Strategy (Statistical Reshaping)
**Perspective:** Chief AI Architect
**Objective:** Implement a non-destructive "Scan-to-Mesh" engine using the ANSUR II dataset to refine 3D body shapes *strictly* from AI-scanned biometric parameters.

---

### **1. Strategic Assets Recognized**
*   **Kaggle Hub Access:** Secured API Token `KGAT_4ada61fb7668048f325fa249acbf744e` for future data synchronization.
*   **Dataset Integration:** **ANSUR II (Male & Female)** CSVs are physically present in `./ansur ii/`.
*   **Research Baseline:** "Feature-selection-based local mapping technique" for 3D body reshaping derived from scanned measurements.

---

### **2. Implementation Roadmap (Non-Destructive & Strict-Scan)**

#### **Phase A: The Imputation Engine (Scan-Driven)**
*   **Logic:** Use `ANSUR_II` data to train a lightweight regression model.
*   **Function:** AI-Scan Output {Height, Scanned Chest, Scanned Waist} → Output {40+ Refined Anthropometric Parameters}.
*   **Integrity:** All inputs are derived from the computer vision pipeline to ensure clinical validity.

#### **Phase B: Local Mapping (The Shape Transformer)**
*   **Logic:** Map the 40+ scanned/predicted parameters to specific vertex groups on the SMPL mesh.
*   **Math:** Apply "Relevance Masks" to ensure that the scanned "Chest Round" only deforms the torso vertices, ensuring 1:1 parity with the user's real-world scan data.
*   **Outcome:** Accurate 3D mesh deformation based on verified biometric evidence.

#### **Phase C: The Unified Biometric Handshake**
*   **Flow:**
    1. **AI Scan (Primary):** Captures physical measurements and skeleton/posture from photos.
    2. **ANSUR II Engine (Refinement):** Takes the top 3–5 *scanned* metrics to reconstruct the full 3D body volume with statistical precision.
    3. **Result:** A **Clinical-Grade Digital Twin** built entirely from verified scan data.

---

### **3. Technical Compatibility Matrix**
*   **Stack:** Python 3.11 / FastAPI / NumPy / Three.js.
*   **Strict Rule:** No manual user overrides. The system remains a purely automated, scan-based diagnostic tool.
*   **Non-Destructive Hook:** This logic will live as the final "Mesh Synthesis" stage inside `api/services/measurement_engine.py`.

---

**Status:** STRATEGY CORRECTED. The system is now locked to **Verified Scan Data only**.

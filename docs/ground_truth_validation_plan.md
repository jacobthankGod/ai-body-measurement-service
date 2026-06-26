# Ground Truth Validation Study Plan

**Goal:** Validate AI body measurement accuracy against tailor tape measurements on 50–100 real subjects.

**Why 50–100:** 
- 10–20 subjects gives anecdotal evidence but ±5cm error bars
- 50 subjects gives statistically significant MAE/RMSE per body part (95% CI ±1.5cm)
- 100 subjects captures shape diversity (short/tall, slim/plus, male/female) and lets you segment accuracy by demographic

---

## 1. Subject Recruitment (2–4 weeks)

### Who
- Friends, family, coworkers, gym members
- Offer **free measurement report + size recommendation** as incentive (zero cost to you, high perceived value)
- Partner with a local tailor / alteration shop — they get a new service to offer clients, you get foot traffic

### Diversity targets (per 100 subjects)
| Group | Target |
|---|---|
| Male | 40–50 |
| Female | 40–50 |
| Height <160cm | 15–20 |
| Height 160–180cm | 40–50 |
| Height >180cm | 15–20 |
| Waist >100cm | 15–20 |
| Age <30 | 20–30 |
| Age 30–50 | 30–40 |
| Age >50 | 15–20 |

### Logistics
- **Location:** Quiet room with plain wall (white/light grey), good overhead lighting, ~2m × 2m floor space
- **Duration per subject:** 15–20 minutes total
- **Schedule:** 4–6 subjects per session (batch them)
- **Kit:** DSLR or smartphone on tripod, tailor tape measure, consent forms, data sheets

---

## 2. Equipment & Setup (1 day)

### Camera Setup
- Smartphone (12MP+) on tripod at chest height, 2m from subject
- Front photo: subject faces camera, arms slightly away from body (~15°), feet shoulder-width apart
- Side photo: subject rotated 90°, same distance, arms in same position
- **Crucial:** Mark tape on floor so distance is identical for all subjects

### File naming convention
```
S001_front.jpg
S001_side.jpg
S002_front.jpg
S002_side.jpg
...
```

### Data sheet template

| Field | Example |
|---|---|
| Subject ID | S001 |
| Age | 34 |
| Gender | M |
| Height (cm) | 175 |
| Weight (kg, optional) | 72 |
| Chest (cm) | 96.5 |
| Waist (cm) | 81.0 |
| Hip (cm) | 93.0 |
| Neck (cm) | 37.5 |
| Shoulder width (cm) | 44.0 |
| Thigh (cm) | 54.0 |
| Ankle (cm) | 23.0 |
| Bicep (cm) | 32.0 |
| Notes | Tattoo on left arm |

## 3. Tape Measurement Protocol (Critical)

**You need one consistent person doing all tape measurements.** Inter-rater reliability on tailor tape is ±1–2cm. Same measurer = ±0.5cm.

### Landmark definitions

| Measurement | Protocol |
|---|---|
| **Height** | Barefoot, back to wall, look straight ahead. Mark top of head on wall, measure to floor. |
| **Chest** | Tape around torso at nipple level, horizontal, snug but not compressing skin. Subject breathes normally, measure at **mid-expiration**. |
| **Waist** | Narrowest point between ribs and hip bone. Ask subject to bend sideways — the crease is the natural waist. Tape horizontal, snug. |
| **Hip** | Widest point around hips/buttocks (typically 20cm below waist). Subject stands with feet together. |
| **Neck** | Just below Adam's apple / cricoid cartilage. Tape must be horizontal, one finger between tape and neck. |
| **Shoulder width** | Acromion bone to acromion bone (bony landmark at top-outside of shoulder). Use a **sliding caliper** or ask subject to hold a ruler between shoulders while you measure. This is the hardest measurement to get right with tape alone. |
| **Thigh** | Maximum circumference, typically 5cm below gluteal fold (where buttock meets thigh). |
| **Ankle** | Narrowest point above ankle bone (malleolus). |
| **Arm** | Maximum bicep circumference, arm relaxed at side. |
| **Inseam** | From crotch point (where inner leg seam would be) to floor, along inner leg. Subject stands. Hard to self-measure. |

### Common errors to avoid
- Tape not horizontal (especially waist and hip) → +2–5cm error
- Tape too loose or too tight → tape should contact skin but not indent it
- Subject changes posture between front/side photos and tape measurement
- Measuring over bulky clothing — **tight fitting clothes or minimal clothing**

## 4. Photo Capture Protocol

### Subject positioning
- **Front photo:**  
  - Stand on marked spot, 2m from camera  
  - Feet shoulder-width apart, weight evenly distributed  
  - Arms at ~15° from body (enough to see waist silhouette)  
  - Look straight at camera  
  - **Clothing:** Tight t-shirt + shorts / leggings (no loose fabric)

- **Side photo:**  
  - Rotate 90° (left side to camera is conventional)  
  - Same arm position, same foot stance  
  - Camera at same height and distance  

### Photo quality checklist
- [ ] Entire body visible (top of head to floor)  
- [ ] No shadows on body (overhead + fill light if needed)  
- [ ] Plain background (no clutter behind subject)  
- [ ] Camera is level (not tilted up/down)  
- [ ] Subject is in focus  
- [ ] No reflective surfaces / glasses glare  

## 5. Data Collection Workflow

### Per subject (20 min)
```
 0:00  Greet, explain process, consent form
 2:00  Change into tight clothes (if needed)
 4:00  Height measurement (wall mark + tape)
 5:00  Tape measurements (chest, waist, hip, neck, shoulder, thigh, ankle, arm)
12:00  Front photo (3 shots to be safe)
14:00  Side photo (3 shots)
16:00  Subject changes back, debrief, give measurement report
20:00  Done
```

### Per session (6 subjects = ~2.5 hours with buffer)
```
 9:00  Setup camera, lighting, test shot
 9:30  Subjects 1–3 (20 min each + 5 min buffer)
11:15  Break
11:30  Subjects 4–6
13:00  Pack up, label files
```

### File organization
```
ground_truth/
├── raw_photos/
│   ├── S001_front.jpg
│   ├── S001_side.jpg
│   ├── S002_front.jpg
│   ├── S002_side.jpg
│   └── ...
├── ground_truth.csv
│
└── processing/
    ├── S001_resized_front.jpg   (resized to 640px, ready for pipeline)
    ├── S001_resized_side.jpg
    └── ...
```

### ground_truth.csv format
```csv
subject_id,height_cm,gender,chest_cm,waist_cm,hip_cm,neck_cm,shoulder_cm,thigh_cm,ankle_cm,bicep_cm,inseam_cm,notes
S001,175,male,96.5,81.0,93.0,37.5,44.0,54.0,23.0,32.0,78.0,
S002,163,female,88.0,68.0,96.0,33.0,39.0,56.0,21.0,28.0,72.0,
```

---

## 6. Analysis Pipeline (after photos collected)

### Step 1: Run batch evaluation
```bash
python scripts/batch_evaluation.py \
  --input-dir ./ground_truth/raw_photos/ \
  --gt ./ground_truth/ground_truth.csv \
  --output ./ground_truth/results.csv
```

This produces:
- `results.csv` — one row per subject, all predicted measurements
- `results_details.csv` — one row per subject with `{measurement}_pred`, `{measurement}_gt`, `{measurement}_error` columns — lets you spot individual outliers

### Step 2: What the output tells you

The script computes per-measurement:

| Metric | What it means | Target |
|---|---|---|
| **MAE** | Mean Absolute Error — average error in cm | ≤ 2.0 cm |
| **RMSE** | Root Mean Squared Error — penalizes large outliers more | ≤ 3.0 cm |
| **Max Error** | Worst single subject error | ≤ 5.0 cm |
| **Std** | Consistency of errors | ≤ 2.0 cm |

### Step 3: Error analysis by subgroup
- Is the error larger for women than men?
- Is the error larger for subjects with BMI > 30?
- Does height calibration drift for very short/tall subjects?
- Which body part has the highest error? (Likely shoulder width and hip — these are the hardest to measure with tape too)

### Step 4: Iterate
- If MAE > 2cm on any torso measurement: revisit the vertex group definitions or plane-mesh intersection
- If shoulder width error > 3cm: the dynamic Y-offset `chest_y + 0.015` might need adjustment
- If ankle/thigh MAE is high: limb bounding-box ellipse needs to be replaced with body-part face segmentation

---

## 7. Timeline & Budget

| Phase | Time | Cost |
|---|---|---|
| Recruitment + scheduling | 2 weeks | $0 |
| Setup (tripod, tape measure, printer) | 1 day | $30–50 |
| Data collection (5 sessions of 10 subjects) | 2 weeks | $0–200 (incentives) |
| Photo processing + batch evaluation | 2 days | $0 |
| Analysis + report | 3 days | $0 |
| **Total** | **~5 weeks** | **$30–250** |

---

## 8. Quick-start (Do this tomorrow)

1. **Buy a tailor tape measure** ($3 at any sewing store)
2. **Find 1 friend** willing to be test subject #1
3. **Measure them with the protocol above** (20 min)
4. **Take front + side photos with your phone on a stack of books** (improvised tripod)
5. **Process through the pipeline:**
   ```bash
   # name your files S00X_front.jpg + S00X_side.jpg
   cp ~/Downloads/my_first_subject_front.jpg data/gt_subject_01/S001_front.jpg
   cp ~/Downloads/my_first_subject_side.jpg  data/gt_subject_01/S001_side.jpg
   python scripts/batch_evaluation.py \
     --input-dir data/gt_subject_01/ \
     --height 175 \
     --gender male
   ```
6. **Compare with tape measurements.** Is MAE under 5cm? If yes, scale to 50 subjects. If no, fix the pipeline first.

Do this for 1 subject before recruiting 100. One subject costs you 20 minutes and proves the workflow.

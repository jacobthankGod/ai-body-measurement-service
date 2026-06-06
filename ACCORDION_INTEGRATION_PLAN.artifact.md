# Accordion Content Integration Plan (Global Reach)
**Architect**: UI/UX Expert
**Goal**: Integrate the full 150+ word "Distance Factor" narrative without cluttering the UI, using a "View More" interactive pattern.

---

## 1. Content Audit (The Complete Text)
The user provided a dense, high-impact narrative that must not be cut:
> "Tailors in LMICs often work with customers who are far away — in another city, village, or country. Getting accurate body measurements becomes a guessing game through messages or old records. London Client. Lagos Tailor. Perfect Fit. No travel, no tape measure, no guesswork needed. Korra helps tailors in LMICs unlock access to customers beyond their immediate location. When measurements are shared through chats, photos, or outdated size records, fit becomes inconsistent, costly, and difficult to scale. Korra makes remote tailoring more reliable by helping customers capture and share accurate body measurements directly from their phone. This gives tailors a more consistent way to work with remote clients, reduce rework, improve fit confidence, and serve more customers across cities and borders. A customer in London can share measurements in minutes, while a tailor in Lagos delivers with greater accuracy — expanding access to opportunity without the limits of distance."

---

## 2. Technical Implementation Strategy

### Step 1: Component Refactor (The "Read More" Pattern)
*   **Visible Snippet**: Show the first 3 sentences ending at "No guesswork needed."
*   **Expansion Area**: Wrap the rest in a `max-height: 0` container with a smooth CSS transition.
*   **Trigger**: A Ghost button labeled **"View Detailed Impact"** with a Mint chevron icon.

### Step 2: Visual Polish
*   **Container**: Preserve the **1150px grid** and **1.5fr image grid**.
*   **Image Card**: Ensure the image card on the left remains large and authoritative while the text expands on the right.

### Step 3: Interaction Logic
*   Implement simple JS `toggle` function to handle the `active` state of the accordion.

---

## 3. Implementation Checklist
- [ ] Refactor HTML in the "Global Reach" section.
- [ ] Add CSS for `.accordion-content` and `.btn-view-more`.
- [ ] Add JS toggle listener.

**Protocol**: Push to GitHub after every edit.

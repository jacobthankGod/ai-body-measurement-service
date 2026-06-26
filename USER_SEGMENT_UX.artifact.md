# KORRA AI: Segmented UI/UX Strategy
**Perspective:** Senior UI/UX Lead
**Goal:** Transition from a "One-Size-Fits-All" dashboard to role-specific "Operating Systems."

---

## 1. The "Personal Wardrobe" (Individual)
**UX Personality:** Personal, Private, Simple.
*   **The Hero Metric:** "My Last Scan" (3D Model preview with date).
*   **The Narrative:** "How have my measurements changed since my last scan?"
*   **Primary Action (FAB):** "Update My Measurements."
*   **Key Features:**
    *   **Size Passport:** A QR code that the user can show at any physical shop to instantly share their data.
    *   **Fit History:** A simple line chart showing waist/weight fluctuations over time.
    *   **Brand Matching:** "Based on your scan, you are a size 'Large' at Nike and 'Medium' at Zara."

## 2. The "Command Center" (Tailor/Artisan)
**UX Personality:** Accurate, Efficient, Reliable.
*   **The Hero Metric:** "Active Client Orders" (Queue management).
*   **The Narrative:** "Who needs a fitting today and are their measurements ready?"
*   **Primary Action (FAB):** "Scan New Client."
*   **Key Features:**
    *   **The Ledger:** A fast, searchable database of client names, heights, and specific "Tailor Notes."
    *   **Export Center:** One-click "PDF Pattern Sheet" or "3D Mesh Export" for their design software.
    *   **Handshake Status:** Real-time indicator showing if the client has confirmed their photos are "private" or "shared."

## 3. The "Brand Studio" (Fashion Brands/Merchants)
**UX Personality:** Creative, Aesthetic, Conversion-Oriented.
*   **The Hero Metric:** "Return Rate Reduction" (Percentage saved by accurate sizing).
*   **The Narrative:** "How is the KORRA widget performing on my Shopify store?"
*   **Primary Action (FAB):** "Customize Widget."
*   **Key Features:**
    *   **Live Theme Editor:** Shopify-style split screen to adjust colors/logos for the "Get Measured" button.
    *   **Analytics:** Heatmap of where users drop off during the widget's scanning flow.
    *   **API Health:** "Active Sync" status showing data flowing to their inventory management.

## 4. The "Intelligence Hub" (Enterprise/Big Business)
**UX Personality:** Scalable, Data-Heavy, Secure.
*   **The Hero Metric:** "Total Global Scans" (Aggregated data).
*   **The Narrative:** "What is the average body shape of my customer base this quarter?"
*   **Primary Action (FAB):** "Bulk Import/Export Data."
*   **Key Features:**
    *   **Regional Statistics:** Maps showing body type distributions across different countries.
    *   **Role Management:** Permission levels for factory workers, designers, and regional managers.
    *   **Compliance Ledger:** Audit trails for data privacy (GDPR/CCPA) and "Delete Requests."

---

## Visual Implementation (The "Unicorn" Standard)
All four roles share the **Glassmorphism Design System**:
1.  **Surfaces:** Semi-transparent #171717 panels with `backdrop-filter: blur(20px)`.
2.  **Typography:** Inter (Bold) for data points, Inter (Light) for secondary labels.
3.  **Accents:** #C6FF00 (Teal) for success/action, #FFC247 (Orange) for "Low Credits" or "Scan Error."
4.  **Navigation:** Bottom-tab navigation for Mobile (Home, Clients, Scan, Settings).

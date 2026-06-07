# KORRA Smart Digital Body Measurement - Implementation Plan (10x Detail)

## Executive Summary
This plan details the industrialization of the KORRA platform through three strategic integration vectors: **Embeddable Widgets**, **In-Store QR Systems**, and **Remote SMS/Email Link Sharing**. It ensures merchant data authority while providing a "Unicorn-Grade" frictionless experience for customers.

---

## I. Database Schemas (Supabase/PostgreSQL)

### 1. `widget_configs` (Merchant UI Authority)
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Unique config ID. |
| `merchant_id` | UUID | FK -> profiles | Owner of the widget. |
| `domain_allowlist` | TEXT[] | | Security: Allowed hostnames. |
| `theme_primary` | TEXT | DEFAULT '#57D7C0' | Mint accent color. |
| `callback_url` | TEXT | | POST URL for measurement data. |

### 2. `scan_sessions` (Ephemeral Access Control)
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `token` | TEXT | PK | Secure session token (64 chars). |
| `merchant_id` | UUID | FK -> profiles | Context for the scan. |
| `expires_at` | TIMESTAMP | | TTL for QR/SMS links. |
| `status` | TEXT | `pending`, `active`, `completed` | Lifecycle state. |

---

## II. Detailed API Specifications

### 1. QR Code Engine (`POST /api/v2/qrcode/generate`)
*   **Purpose**: Create a printable, high-authority entry point for in-store customers.
*   **Parameters**:
    *   `merchant_id` (UUID): Mandatory.
    *   `expiry_minutes` (INT): Default 60.
    *   `client_name` (TEXT): Optional label.
*   **Payload**: `{"qr_code_base64": "...", "scan_url": "https://korra.work/scan/{token}"}`

### 2. Widget Extraction (`POST /api/v2/measurements/extract-widget`)
*   **Purpose**: Public-facing extraction optimized for speed and CORS safety.
*   **Headers**: `Origin`, `User-Agent`.
*   **Body**: Standard multipart/form (front, side, height, gender, merchant_id).
*   **Security**: Rate-limited by IP and Origin.

---

## III. Phase 1: Get Measured Widget Implementation

### 1. [NEW] `public/korra-widget.js` (Loader Engine)
```javascript
(function() {
  const script = document.currentScript;
  const merchantId = script.getAttribute('data-merchant');
  const theme = script.getAttribute('data-theme') || 'dark';

  window.KorraWidget = {
    open: function() {
      const iframe = document.createElement('iframe');
      iframe.src = `https://korra.work/widget?merchant=${merchantId}&theme=${theme}`;
      iframe.style = "position:fixed; inset:0; width:100%; height:100%; border:none; z-index:999999;";
      document.body.appendChild(iframe);
    }
  };
})();
```

### 2. [NEW] `widget.html` (The "Shadow" Interface)
-   Uses Obsidian & Mint theme.
-   Communicates with parent window via `postMessage`.
-   Triggers real-time quality validation (Vision Guard).

---

## IV. Phase 2: QR Code Generation Implementation

### 1. [NEW] `api/routes/qrcode.py`
```python
import qrcode
import io
import base64
from fastapi import APIRouter

@router.post("/generate")
async def generate_qr(merchant_id: str):
    token = generate_secure_token() # 64-char hex
    url = f"https://korra.work/scan/{token}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return {"qr_base64": base64.b64encode(buf.getvalue())}
```

---

## V. Phase 3: Measurement Link Sharing

### 1. SMS/Email Logic (`api/routes/sharing.py`)
-   **SMS**: Twilio REST Client integration.
-   **Email**: SendGrid transactional templates.
-   **Template**: `[Subject Name], get your digital body scan for [Merchant Name] here: [Link]`

---

## VI. Security & Error Handling

### 1. Security Protocols
-   **JWT Tokenization**: All shared links use one-time tokens with expiration.
-   **Domain Locking**: Widgets only execute on authorized merchant domains.
-   **PII Anonymization**: No user email is stored for widget scans unless explicitly shared.

### 2. Error Handling Matrices
| Error Code | UX Message | Technical Action |
| :--- | :--- | :--- |
| **TOKEN_EXPIRED** | "Link has expired. Ask merchant for new link." | Redirect to help page. |
| **BAD_LIGHTING** | "Lighting too low. Move to brighter area." | Block upload button. |
| **UPLOAD_FAIL** | "Handshake lost. Retrying connection..." | Auto-retry multipart stream. |

---

## VII. UI/UX Mockup Specification

### 1. The "Ghost Overlay" (Scanner UI)
-   **Obsidian Layer**: 60% opacity covering edges.
-   **Mint Frame**: 2px thick rectangle in center.
-   **Real-time Text**: "Center your shoulders inside the Mint box."

### 2. Result Grid
-   **Layout**: 2x2 grid for primary (Chest, Waist, Hip, Shoulder).
-   **Animation**: Numbers count up from 0 to clinical result.

---

## VIII. Deployment & Troubleshooting

### 1. Deployment Guide
1.  **Backend**: `git push origin main` (Render auto-builds).
2.  **CDN Assets**: Upload `korra-widget.js` to Vercel/S3.
3.  **Environment**: Add `TWILIO_SID`, `SENDGRID_KEY` to secrets.

### 2. Troubleshooting Matrix
-   **Widget not loading**: Check `domain_allowlist` in `widget_configs`.
-   **QR fails to render**: Verify `Pillow` version >= 10.0.0.
-   **Low Accuracy**: Check "Ghost Overlay" calibration in `widget.html`.

---

## IX. Performance Benchmarks
-   **Widget First-Paint**: < 1.2s.
-   **QR Generation**: < 150ms.
-   **3D Mesh Load**: < 500ms using DRACO compression.

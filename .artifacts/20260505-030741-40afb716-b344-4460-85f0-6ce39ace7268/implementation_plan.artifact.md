# KORRA Sovereign Artisan - Expert Implementation Plan

## Executive Summary
This document provides an expert-level blueprint for the **KORRA Smart Digital Body Measurement Solution**. It combines high-conversion merchant tools (Widget, QR, Sharing) with a **Zero-Touch Autonomous Infrastructure** that eliminates manual maintenance and optimizes AI efficiency out-of-the-box.

---

## I. Core Infrastructure: Autonomous "Brain" Restoration

### 1. The Expert Fix: On-Boot Atomic Handshake
Instead of manual admin triggers, KORRA will verify and restore its AI brain automatically during the server boot sequence.

**Implementation Logic (`api/main.py`):**
- **Trigger**: FastAPI `lifespan` context manager.
- **Action**: Check for `models/model.ckpt-667589.data-00000-of-00001` (347MB).
- **Resolution**: If missing, initiate a high-speed parallel stream from the KORRA High-Availability Mirror.
- **Efficiency**: The server will not accept `/measurements` calls until the `INTEGRITY` check is `true`.

### 2. Database Schema (Supabase/PostgreSQL)

#### `profiles` (Merchant Authority)
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Auth link. |
| `credits` | INT | DEFAULT 0 | Scan quota. |
| `widget_settings` | JSONB | | Custom colors/logo. |

#### `measurements` (Biometric Vault)
| Field | Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Scan ID. |
| `biometrics` | JSONB | | Chest, Waist, Hips, etc. |
| `mesh_url` | TEXT | | Path to `.obj` Digital Twin. |

---

## II. Part 1: Get Measured Widget (E-commerce)

### 1. Detailed API Specification
`POST /api/v2/measurements/extract-widget`

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `front` | FILE | YES | Image buffer. |
| `merchant_id` | UUID | YES | Target ledger. |
| `callback_url` | TEXT | NO | Redirect on success. |

### 2. Frontend Component: `korra-widget.js`
- **Weight**: < 15KB (Minified).
- **Security**: Domain-allowlist validation via `Referer` header.
- **Handshake**: Cross-domain communication using `Window.postMessage()`.

---

## III. Part 2: QR Code Generation (In-Store)

### 1. Detailed API Specification
`POST /api/v2/qrcode/generate`

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `merchant_id` | UUID | YES | Context. |
| `expiry` | INT | NO | TTL in seconds. |

**Response:**
```json
{
  "qr_base64": "data:image/png;base64...",
  "session_url": "https://korra.work/scan/ABC-123"
}
```

---

## IV. Part 3: Measurement Link Sharing (SMS/Email)

### 1. Technical Handshake
- **SMS Bridge**: Twilio Programmable Messaging API.
- **Email Bridge**: SendGrid Dynamic Templates.
- **Persistence**: Links expire automatically after 24 hours.

---

## V. Security, Performance & Deployment

### 1. Security Considerations
- **JWT Session Tokens**: For all shared links.
- **Atomic Rate Limiting**: Preventing AI resource exhaustion on public endpoints.
- **Vision Guard (Phase 14)**: Compulsory for all public scans to maintain data purity.

### 2. Performance Benchmarks
- **Boot Time**: < 45s (including 347MB model pull).
- **Inference Latency**: < 2.2s (Optimized CPU Path).
- **Widget First Paint**: < 500ms.

### 3. Deployment Guide (Zero-Touch)
1. Set `MIRROR_URL` in environment variables.
2. Push to branch `main`.
3. Server boots -> Checks `/models` -> **Self-Heals** -> Dashboard goes **Active**.

---

## VI. Troubleshooting Matrix

| Issue | Diagnosis | Fix |
| :--- | :--- | :--- |
| **Proxy Mesh Showing** | Brain Restoration in progress. | Check Admin -> Health -> Restoration Status. |
| **CORS Blocked** | Domain not in allowlist. | Add host to Merchant Settings. |
| **422 Rejection** | Vision Guard failure. | Ensure subject stands 2m away from camera. |

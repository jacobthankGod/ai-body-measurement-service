# UNICORN SYNC - 10 Phase Implementation Plan
## Two-Way Communication & Measurement Sync Architecture

---

## Phase 1: Database Schema Foundation
### Create database tables for sync infrastructure
- [ ] `webhook_configs` - Merchant webhook registration
- [ ] `measurement_links` - Client sharing with multiple merchants
- [ ] `scan_requests` - Merchant → Client re-scan requests
- [ ] `client_notifications` - In-app notifications

```sql
-- Create tables
CREATE TABLE IF NOT EXISTS webhook_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES profiles(id),
    webhook_url TEXT NOT NULL,
    secret_key TEXT,
    events TEXT[] DEFAULT ARRAY['scan_completed'],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS measurement_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    measurement_id UUID REFERENCES measurements(id),
    merchant_id UUID REFERENCES profiles(id),
    shared_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS scan_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID REFERENCES profiles(id),
    client_email TEXT NOT NULL,
    client_name TEXT,
    request_token TEXT UNIQUE NOT NULL,
    specialty TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS client_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Phase 2: Brevo Email Integration
### Extend email_service.py for scan notifications
- [ ] Add `send_scan_completed_email` - Notify merchant when scan completes
- [ ] Add `send_scan_request_email` - Send re-scan request to client
- [ ] Add `send_measurement_shared_email` - Notify client their measurement was shared

## Phase 3: Webhook Infrastructure
### Create webhook service and endpoints
- [ ] `api/services/webhook_service.py` - Webhook trigger logic
- [ ] POST `/webhooks/register` - Merchant registers webhook URL
- [ ] GET `/webhooks` - List merchant webhooks
- [ ] DELETE `/webhooks/{id}` - Remove webhook

## Phase 4: Background Task Triggers
### Integrate webhook + email triggers in measurement flow
- [ ] Trigger webhook on scan complete
- [ ] Trigger email notification on scan complete
- [ ] Retry logic with exponential backoff

## Phase 5: Notification System
### Create in-app notification center
- [ ] `api/services/notification_service.py` - Push notification logic
- [ ] GET `/notifications` - Get user notifications
- [ ] PUT `/notifications/{id}/read` - Mark as read
- [ ] Dashboard notification bell icon

## Phase 6: Client Dashboard
### Create sizepassport page for clients
- [ ] `sizepassport.html` - Client measurement history
- [ ] Allow client to view their own scans (via email/token auth)
- [ ] PDF export functionality

## Phase 7: Scan Request Flow
### Implement merchant → client re-scan requests
- [ ] POST `/scan-requests/create` - Create re-scan request
- [ ] GET `/scan-requests/verify/{token}` - Verify and process request
- [ ] Share page handles scan requests differently than invites

## Phase 8: Measurement Sharing
### Allow client to share with multiple merchants
- [ ] POST `/measurements/{id}/share` - Share with merchant(s)
- [ ] GET `/measurements/shared` - List clients shared measurements
- [ ] Dashboard shows shared measurements

## Phase 9: Real-time Updates Enhancement
### Improve polling → push notifications
- [ ] WebSocket connection for live updates (optional)
- [ ] Client-side notification toaster
- [ ] Dashboard live reload

## Phase 10: Dashboard UI Updates
### Add notification center UI
- [ ] Notification bell icon in header
- [ ] Message icon for communication
- [ ] Notification dropdown panel
- [ ] In-app messaging between client and merchant

---

## Execution Order
1. Phase 1: Database Schema (SQL)
2. Phase 2: Email Service (Python)
3. Phase 3: Webhook Service (Python)
4. Phase 4: Background Triggers (Python)
5. Phase 5: Notification System (Python)
6. Phase 6: Client Dashboard (HTML/JS)
7. Phase 7: Scan Request Flow (Python)
8. Phase 8: Measurement Sharing (Python)
9. Phase 9: Real-time Updates (JS)
10. Phase 10: Dashboard UI (HTML/CSS/JS)

---

## Technical Dependencies
- BREVO_API_KEY - Already configured
- Supabase Database - Already configured
- Background tasks - FastAPI BackgroundTasks
- Webhook retry - exponential backoff (3 retries)

---

## Files to Modify/Create
- `api/services/email_service.py` - Extend
- `api/services/webhook_service.py` - Create
- `api/services/notification_service.py` - Create
- `api/routes/webhooks.py` - Create
- `api/routes/notifications.py` - Create
- `api/routes/scan_requests.py` - Create
- `sizepassport.html` - Create/Enhance
- `dashboard.html` - Add notification UI
- Database tables (SQL)

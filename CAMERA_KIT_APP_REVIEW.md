# Snapchat Camera Kit - App Review Submission Notes

## App Information

| Field | Value |
|-------|-------|
| **Name** | Korra |
| **Category** | Shopping / Lifestyle |
| **Description** | KORRA is an AI-powered virtual try-on platform for tailors and fashion entrepreneurs. Users can virtually try on clothing using augmented reality, get precise body measurements, and connect with tailors for custom garments. |

---

## Privacy & Legal URLs

| Field | URL |
|-------|-----|
| **Privacy Policy** | https://korra.work/privacy |
| **Terms of Service** | https://korra.work/terms |
| **Learn More** | https://korra.work |

---

## OAuth Redirect URIs

| URI |
|-----|
| `https://korra.work` |
| `https://korra.work/camera-kit-tryon.html` |
| `https://korra.work/dashboard.html` |
| `http://localhost:5001` (development) |
| `http://localhost:3000` (development) |

---

## App Review Notes

### How does your integration work?

```
KORRA integrates Snapchat Camera Kit and Login Kit to provide a personalized 
virtual clothing try-on experience for tailors and fashion entrepreneurs.

INTEGRATION OVERVIEW:

1. LOGIN KIT INTEGRATION:
   - Users can sign in using their Snapchat account
   - Profile information (name, email, Bitmoji avatar) is retrieved
   - Bitmoji avatar is used as the user's profile picture in the app
   - Secure authentication via OAuth 2.0
   - No password storage - authentication handled by Snapchat

2. CAMERA KIT INTEGRATION:
   - Users grant camera permission for virtual try-on
   - Camera Kit Web SDK (v1.19.0) initializes
   - Body tracking lenses are loaded for clothing visualization
   - Real-time AR overlay shows garments on the user's body
   - Users can capture photos of the try-on experience
   - Captures are saved to the user's account

USER FLOW:
1. User visits https://korra.work/camera-kit-tryon.html
2. User clicks "Sign in with Snapchat" (Login Kit)
3. Snapchat authentication popup appears
4. User authorizes the app
5. User is redirected back with auth token
6. Profile info and Bitmoji are loaded
7. Camera permission is requested
8. Camera Kit session initializes
9. User selects an outfit from the carousel
10. AR lens applies the garment to user's body
11. User can capture and save photos
12. Captures are stored in user's account

USE CASES:
- Virtual fitting before placing custom tailoring orders
- Sharing try-on results with tailors for remote consultations
- Previewing garment styles before production
- Personalized shopping experience with Bitmoji integration

TECHNICAL DETAILS:
- Login Kit: OAuth 2.0 with PKCE flow
- Camera Kit: Web SDK v1.19.0
- Lens type: Clothing Try-On with body tracking
- Platform: Web (Chrome 95+, Safari 16+, Edge 79+)
- Backend: FastAPI (Python) with Supabase
- Authentication: Supabase Auth + Snapchat OAuth
```

---

## Demo Video Script (30-60 seconds)

```
[0:00-0:05] Show KORRA homepage with "Sign in with Snapchat" button

[0:05-0:10] Click sign in → Snapchat login popup appears

[0:10-0:15] User authorizes → Redirects back with Bitmoji loaded

[0:15-0:20] Show dashboard with user's Bitmoji as profile picture

[0:20-0:25] Navigate to Virtual Try-On page

[0:25-0:30] Camera permission request → Camera activates

[0:30-0:35] Select "Classic T-Shirt" from outfit carousel

[0:35-0:45] AR garment appears on user's body, user moves around

[0:45-0:50] Click capture button → Photo saved

[0:50-0:55] Show captured photo in gallery

[0:55-1:00] End with KORRA logo
```

---

## Camera Kit Portal Configuration

### Enable these features:

| Feature | Setting |
|---------|---------|
| **Camera Kit** | ✅ Enabled |
| **Login Kit** | ✅ Enabled |
| **Bitmoji Kit** | ✅ Enabled |
| **Lens Cloud** | ✅ Enabled |
| **Mirror Configuration** | ✅ On |
| **Age Restriction** | No (13+) |

### Bitmoji Permissions to Request:

| Permission | Purpose |
|------------|---------|
| `user.bitmoji.avatar` | Display user's Bitmoji as profile picture |
| `user.display_name` | Show user's display name in the app |
| `user.email` | Account identification (optional) |

---

## Attachment Link Domain

```
https://korra.work
```

---

## Checklist Before Submission

- [ ] Upload 1024x1024 app icon (KORRA logo)
- [ ] Add Privacy Policy URL: `https://korra.work/privacy`
- [ ] Add Terms of Service URL: `https://korra.work/terms`
- [ ] Add Learn More URL: `https://korra.work`
- [ ] Record and upload demo video
- [ ] Add all redirect URIs
- [ ] Enable Camera Kit
- [ ] Enable Login Kit
- [ ] Enable Bitmoji Kit
- [ ] Enable Lens Cloud
- [ ] Configure age restriction (13+)
- [ ] Test OAuth flow
- [ ] Test Camera Kit flow
- [ ] Review and submit

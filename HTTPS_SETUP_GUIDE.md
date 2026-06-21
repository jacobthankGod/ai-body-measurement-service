# Critical: Enabling HTTPS for Camera Access

Browsers (Chrome, Safari, etc.) **block the camera** (`getUserMedia`) and **clipboard** APIs on any website that does not use HTTPS. 

Since KORRA AI is currently on `http://13.60.215.88:8080`, you will see errors like:
- `TypeError: Cannot read properties of undefined (reading 'getUserMedia')`
- `TypeError: Cannot read properties of undefined (reading 'writeText')`

## Part 1: Permanent Fix (HTTPS via Nginx)

To fix this permanently, you must point your domain (`korra.work`) to the server and install an SSL certificate.

### 1. Point DNS
In your Domain Provider (GoDaddy, Namecheap, etc.), create an **A Record**:
- **Name**: `@`
- **Value**: `13.60.215.88`

### 2. Install Nginx & SSL on Server
Run these commands on your AWS EC2 instance:

```bash
# SSH into your server first
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx Config
sudo nano /etc/nginx/sites-available/korra
```

**Paste this into the file** (Replace `korra.work` with your actual domain):
```nginx
server {
    listen 80;
    server_name korra.work;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Save and exit (Ctrl+O, Enter, Ctrl+X).

```bash
# Enable the site and restart Nginx
sudo ln -s /etc/nginx/sites-available/korra /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL Certificate (HTTPS)
sudo certbot --nginx -d korra.work
```

---

## Part 2: Temporary Testing Workaround (Chrome Only)

If you want to test the camera **right now** without HTTPS:

1. Open Chrome on your laptop.
2. Go to this URL: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. **Enable** the flag.
4. In the text box, paste: `http://13.60.215.88:8080`
5. Click **Relaunch** at the bottom.

**Chrome will now allow the camera to work on that specific IP address.**

---

## Part 3: Fixed WhatsApp & Clipboard
I have already updated the code to include:
1. **Clipboard Fallback**: If HTTPS is missing, the app will now use a secondary method to copy links so the "Copy" buttons work.
2. **WhatsApp Encoding**: The WhatsApp message is now fully encoded so the link is recognized and clickable by WhatsApp.

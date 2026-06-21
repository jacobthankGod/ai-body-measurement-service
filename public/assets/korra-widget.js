/**
 * KORRA Get Measured Widget | V1.0
 * ================================
 * Embeddable loader for e-commerce integration.
 */

(function() {
    console.log("💎 KORRA: Widget Loader Initializing...");

    const KorraWidget = {
        config: {
            merchantId: null,
            theme: 'dark',
            host: 'https://korra-436814609100.us-central1.run.app'
        },

        init: function() {
            const script = document.currentScript || document.querySelector('script[data-merchant]');
            if (!script) return;

            this.config.merchantId = script.getAttribute('data-merchant');
            this.config.theme = script.getAttribute('data-theme') || 'dark';

            // Create Trigger Button if not exists
            if (!document.getElementById('korra-widget-trigger')) {
                this.createTrigger();
            }
        },

        createTrigger: function() {
            const btn = document.createElement('button');
            btn.id = 'korra-widget-trigger';
            btn.innerHTML = 'Get Measured with AI';
            btn.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: #57D7C0;
                color: #000;
                border: none;
                padding: 14px 24px;
                border-radius: 99px;
                font-family: Inter, sans-serif;
                font-weight: 800;
                font-size: 13px;
                cursor: pointer;
                box-shadow: 0 10px 30px rgba(87,215,192,0.3);
                z-index: 999999;
                transition: 0.3s cubic-bezier(0.2, 1, 0.3, 1);
            `;
            btn.onmouseover = () => btn.style.transform = 'translateY(-4px) scale(1.05)';
            btn.onmouseout = () => btn.style.transform = 'translateY(0) scale(1)';
            btn.onclick = () => this.open();
            document.body.appendChild(btn);
        },

        open: function() {
            if (!this.config.merchantId || this.config.merchantId === 'null') {
                console.error("❌ KORRA: Missing data-merchant attribute. Cannot open widget.");
                alert("KORRA Error: Widget missing merchant configuration.");
                return;
            }

            const overlay = document.createElement('div');
            overlay.id = 'korra-widget-overlay';
            overlay.style.cssText = `
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.95);
                backdrop-filter: blur(20px);
                z-index: 9999999;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: 0.3s ease;
            `;

            const iframe = document.createElement('iframe');
            iframe.src = `${this.config.host}/widget?merchant=${this.config.merchantId}`;
            iframe.allow = "camera; microphone; display-capture; autoplay;"; // CRITICAL: Grant Device Permissions
            iframe.style.cssText = `
                width: 95%;
                max-width: 900px;
                height: 90vh;
                max-height: 850px;
                border: none;
                border-radius: 32px;
                box-shadow: 0 40px 100px rgba(0,0,0,0.5);
            `;

            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 32px;
                right: 32px;
                background: none;
                border: none;
                color: #fff;
                font-size: 32px;
                cursor: pointer;
                opacity: 0.5;
            `;
            closeBtn.onclick = () => {
                overlay.style.opacity = '0';
                setTimeout(() => overlay.remove(), 300);
            };

            overlay.appendChild(closeBtn);
            overlay.appendChild(iframe);
            document.body.appendChild(overlay);

            requestAnimationFrame(() => overlay.style.opacity = '1');
        }
    };

    // Listen for biometric success from iframe
    window.addEventListener('message', (event) => {
        if (event.data.type === 'KORRA_RESULT') {
            console.log("💎 KORRA: Biometrics Received:", event.data.measurements);
            // Custom event for the host site to listen to
            const korraEvent = new CustomEvent('korra_measurements', { detail: event.data.measurements });
            document.dispatchEvent(korraEvent);
        }
    });

    KorraWidget.init();
    window.KorraWidget = KorraWidget;
    window.KORRA = KorraWidget; // Global Alias for simpler developer UX
})();

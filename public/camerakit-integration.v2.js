/**
 * Snapchat Camera Kit Integration - ES Module
 * AI Body Scan SaaS - Virtual Try-On Module
 *
 * Performance: Uses direct esm.sh import with modulepreload hint in HTML.
 * Lens is cached after first load to avoid re-downloading on outfit switch.
 */

import { bootstrapCameraKit, createMediaStreamSource, Transform2D } from 'https://esm.sh/@snap/camera-kit@1.19.0/es2022/camera-kit.bundle.mjs';

class CameraKitTryOn {
  constructor() {
    this.cameraKit = null;
    this.session = null;
    this.source = null;
    this.isLoading = false;
    this.error = null;
    this.currentLens = null;
    this.lensCache = {};
    this.currentFacing = 'user';

    this.canvas = null;
    this.statusEl = null;

    this.onCapture = null;
    this.onLensApplied = null;
    this.onError = null;
  }

  async initialize() {
    try {
      this.isLoading = true;
      this.updateStatus('Initializing Camera Kit...');

      const config = window.CameraKitConfig;
      this.cameraKit = await bootstrapCameraKit({
        apiToken: config.getApiToken(),
        logger: 'console'
      });

      this.updateStatus('Camera Kit initialized');
      this.isLoading = false;
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Error: ${err.message}`);
      this.isLoading = false;
      if (this.onError) this.onError(err);
      return false;
    }
  }

  async createSession(canvasId = 'tryon-canvas') {
    try {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) throw new Error(`Canvas element '${canvasId}' not found`);

      this.session = await this.cameraKit.createSession({
        liveRenderTarget: this.canvas
      });

      this.session.events.addEventListener('error', (event) => {
        console.error('[CameraKit] session error:', event.detail.error);
        this.error = event.detail.error.message;
        this.updateStatus(`Error: ${event.detail.error.message}`);
      });

      this.updateStatus('Session created');
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Error: ${err.message}`);
      return false;
    }
  }

  async startCamera(facingMode = 'user') {
    try {
      this.updateStatus('Requesting camera access...');

      if (this.source && this.source.stream) {
        this.source.stream.getTracks().forEach(function(t) { t.stop(); });
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      });

      this.source = createMediaStreamSource(stream, {
        transform: Transform2D.MirrorX,
        cameraType: facingMode === 'user' ? 'user' : 'environment'
      });

      await this.session.setSource(this.source);
      await this.session.play();

      this.updateStatus('Camera active');
      return true;
    } catch (err) {
      this.error = err.message;
      if (err.name === 'NotAllowedError') {
        this.updateStatus('Camera permission denied');
      } else {
        this.updateStatus(`Camera error: ${err.message}`);
      }
      return false;
    }
  }

  async applyLens(lensId, groupId) {
    try {
      if (!groupId || !lensId) throw new Error('Lens ID and Group ID are required');

      const cacheKey = `${lensId}:${groupId}`;
      this.updateStatus('Loading lens...');

      let lens;
      if (this.lensCache[cacheKey]) {
        lens = this.lensCache[cacheKey];
        this.updateStatus('Lens loaded (cached)');
      } else {
        lens = await this.cameraKit.lensRepository.loadLens(lensId, groupId);
        this.lensCache[cacheKey] = lens;
        this.updateStatus('Lens loaded');
      }

      await this.session.applyLens(lens);

      this.currentLens = { lensId, groupId };
      this.updateStatus('Lens applied');

      if (this.onLensApplied) this.onLensApplied(lens);
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Error loading lens: ${err.message}`);
      return false;
    }
  }

  async removeLens() {
    try {
      await this.session.removeLens();
      this.currentLens = null;
      this.updateStatus('Lens removed');
      return true;
    } catch (err) {
      this.error = err.message;
      return false;
    }
  }

  async capturePhoto() {
    try {
      if (!this.session) throw new Error('No active session');
      const canvas = this.session.output.live;

      return new Promise((resolve) => {
        canvas.toBlob((blob) => {
          if (blob) {
            this.updateStatus('Photo captured');
            if (this.onCapture) this.onCapture(blob);
            resolve(blob);
          } else {
            resolve(null);
          }
        }, 'image/png');
      });
    } catch (err) {
      this.error = err.message;
      return null;
    }
  }

  async saveCapture(blob, userId, outfitId) {
    try {
      const formData = new FormData();
      formData.append('photo', blob, `tryon_${Date.now()}.png`);
      formData.append('user_id', userId || 'anonymous');
      formData.append('outfit_id', outfitId || this.currentLens?.lensId || 'unknown');

      const response = await fetch('/api/v2/tryon/capture', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Failed to save capture');

      const result = await response.json();
      this.updateStatus('Capture saved');
      return result;
    } catch (err) {
      this.error = err.message;
      return null;
    }
  }

  async flipCamera() {
    try {
      const newFacing = this.currentFacing === 'user' ? 'environment' : 'user';
      await this.startCamera(newFacing);
      this.currentFacing = newFacing;
      this.updateStatus(`Camera flipped: ${newFacing}`);
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Flip failed: ${err.message}`);
      return false;
    }
  }

  pause() {
    if (this.session) {
      this.session.pause();
      this.updateStatus('Camera paused');
    }
  }

  resume() {
    if (this.session) {
      this.session.play();
      this.updateStatus('Camera resumed');
    }
  }

  destroy() {
    if (this.session) {
      this.session.pause();
      this.session = null;
    }
    if (this.source) {
      const stream = this.source.stream;
      if (stream) stream.getTracks().forEach(track => track.stop());
      this.source = null;
    }
    this.lensCache = {};
    this.cameraKit = null;
    this.updateStatus('Camera Kit destroyed');
  }

  updateStatus(message) {
    console.log('[CameraKit]', message);
    if (this.statusEl) this.statusEl.textContent = message;
    window.dispatchEvent(new CustomEvent('camerakit:status', { detail: { message } }));
  }
}

export { CameraKitTryOn };
window.CameraKitTryOn = CameraKitTryOn;

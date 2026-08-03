/**
 * Snapchat Camera Kit Integration
 * AI Body Scan SaaS - Virtual Try-On Module
 * 
 * Requirements:
 * - @snap/camera-kit SDK (loaded via CDN or npm)
 * - Camera permission from user
 * - Lens IDs from Lens Scheduler
 */

class CameraKitTryOn {
  constructor() {
    this.cameraKit = null;
    this.session = null;
    this.source = null;
    this.isLoading = false;
    this.error = null;
    this.currentLens = null;
    
    // DOM elements
    this.canvas = null;
    this.statusEl = null;
    this.outfitListEl = null;
    
    // Callbacks
    this.onCapture = null;
    this.onLensApplied = null;
    this.onError = null;
  }

  /**
   * Initialize Camera Kit SDK
   */
  async initialize() {
    try {
      this.isLoading = true;
      this.updateStatus('Initializing Camera Kit...');
      
      // Load Camera Kit SDK dynamically
      await this.loadSDK();
      
      // Bootstrap Camera Kit
      const config = window.CameraKitConfig;
      this.cameraKit = await bootstrapCameraKit({
        apiToken: config.getApiToken(),
        logger: 'console'  // Enable logging for development
      });
      
      this.updateStatus('Camera Kit initialized');
      this.isLoading = false;
      
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Error: ${err.message}`);
      this.isLoading = false;
      
      if (this.onError) {
        this.onError(err);
      }
      
      return false;
    }
  }

  /**
   * Load Camera Kit SDK from CDN
   */
  async loadSDK() {
    return new Promise((resolve, reject) => {
      // Check if already loaded
      if (window.bootstrapCameraKit) {
        resolve();
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cf-st.sc-cdn.net/als/camera-kit/1.19.0/camera-kit.js';
      script.async = true;
      
      script.onload = () => {
        // Wait for SDK to be available
        const checkSDK = setInterval(() => {
          if (window.bootstrapCameraKit) {
            clearInterval(checkSDK);
            resolve();
          }
        }, 100);
        
        // Timeout after 10 seconds
        setTimeout(() => {
          clearInterval(checkSDK);
          reject(new Error('Camera Kit SDK failed to load'));
        }, 10000);
      };
      
      script.onerror = () => {
        reject(new Error('Failed to load Camera Kit SDK'));
      };
      
      document.head.appendChild(script);
    });
  }

  /**
   * Create camera session and attach to canvas
   */
  async createSession(canvasId = 'tryon-canvas') {
    try {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) {
        throw new Error(`Canvas element '${canvasId}' not found`);
      }
      
      // Create session
      this.session = await this.cameraKit.createSession({
        liveRenderTarget: this.canvas
      });
      
      // Setup error handling
      this.session.events.addEventListener('error', (event) => {
        console.error('Camera Kit session error:', event.detail.error);
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

  /**
   * Start camera input
   */
  async startCamera(facingMode = 'user') {
    try {
      this.updateStatus('Requesting camera access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });
      
      this.source = createMediaStreamSource(stream, {
        transform: Transform2D.MirrorX,
        cameraType: facingMode === 'user' ? 'front' : 'back'
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

  /**
   * Apply a clothing try-on lens
   */
  async applyLens(lensId, groupId) {
    try {
      if (!groupId || !lensId) {
        throw new Error('Lens ID and Group ID are required');
      }
      
      this.updateStatus('Loading lens...');
      
      const lens = await this.cameraKit.lensRepository.loadLens(lensId, groupId);
      await this.session.applyLens(lens);
      
      this.currentLens = { lensId, groupId };
      this.updateStatus('Lens applied');
      
      if (this.onLensApplied) {
        this.onLensApplied(lens);
      }
      
      return true;
    } catch (err) {
      this.error = err.message;
      this.updateStatus(`Error loading lens: ${err.message}`);
      return false;
    }
  }

  /**
   * Remove current lens
   */
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

  /**
   * Capture photo from camera
   */
  async capturePhoto() {
    try {
      if (!this.session) {
        throw new Error('No active session');
      }
      
      // Get canvas content
      const canvas = this.session.output.live;
      
      return new Promise((resolve) => {
        canvas.toBlob((blob) => {
          if (blob) {
            this.updateStatus('Photo captured');
            
            if (this.onCapture) {
              this.onCapture(blob);
            }
            
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

  /**
   * Save capture to server
   */
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
      
      if (!response.ok) {
        throw new Error('Failed to save capture');
      }
      
      const result = await response.json();
      this.updateStatus('Capture saved');
      
      return result;
    } catch (err) {
      this.error = err.message;
      return null;
    }
  }

  /**
   * Pause camera
   */
  pause() {
    if (this.session) {
      this.session.pause();
      this.updateStatus('Camera paused');
    }
  }

  /**
   * Resume camera
   */
  resume() {
    if (this.session) {
      this.session.play();
      this.updateStatus('Camera resumed');
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    if (this.session) {
      this.session.pause();
      this.session = null;
    }
    
    if (this.source) {
      // Stop all tracks
      const stream = this.source.stream;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      this.source = null;
    }
    
    this.cameraKit = null;
    this.updateStatus('Camera Kit destroyed');
  }

  /**
   * Update status display
   */
  updateStatus(message) {
    console.log('[CameraKit]', message);
    
    if (this.statusEl) {
      this.statusEl.textContent = message;
    }
    
    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('camerakit:status', {
      detail: { message }
    }));
  }
}

// Export
window.CameraKitTryOn = CameraKitTryOn;

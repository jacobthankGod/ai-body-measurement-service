/**
 * Snapchat Login Kit Integration
 * AI Body Scan SaaS - Secure Snapchat Authentication
 */

class SnapLoginKit {
  constructor() {
    this.clientId = 'd6524989-00bd-4129-bbd1-b754ebb43b3b';
    this.redirectUri = window.location.origin + '/callback';
    this.scopes = [
      'https://auth.snapchat.com/oauth2/api/user.display_name',
      'https://auth.snapchat.com/oauth2/api/user.bitmoji.avatar',
      'https://auth.snapchat.com/oauth2/api/user.external_id'
    ];
    this.sdkLoaded = false;
    this.userInfo = null;
    this.accessToken = null;
  }

  /**
   * Load Login Kit SDK
   */
  async loadSDK() {
    return new Promise((resolve, reject) => {
      if (this.sdkLoaded || window.snap?.loginkit) {
        this.sdkLoaded = true;
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://sdk.snapkit.com/js/v1/login.js';
      // No crossOrigin - avoid CORS block if server doesn't send header
      
      script.onload = () => {
        const checkSDK = setInterval(() => {
          if (window.snap?.loginkit) {
            clearInterval(checkSDK);
            this.sdkLoaded = true;
            resolve();
          }
        }, 100);
        
        setTimeout(() => {
          clearInterval(checkSDK);
          reject(new Error('Login Kit SDK failed to load'));
        }, 10000);
      };
      
      script.onerror = () => reject(new Error('Failed to load Login Kit SDK'));
      document.head.appendChild(script);
    });
  }

  /**
   * Mount Login Kit button
   */
  mountButton(elementId, onSuccess) {
    if (!window.snap?.loginkit) {
      console.error('Login Kit SDK not loaded');
      return;
    }

    snap.loginkit.mountButton(elementId, {
      clientId: this.clientId,
      redirectURI: this.redirectUri,
      scopeList: this.scopes,
      handleResponseCallback: async () => {
        try {
          const result = await this.fetchUserInfo();
          if (onSuccess) onSuccess(result);
        } catch (err) {
          console.error('Login callback error:', err);
        }
      }
    });
  }

  /**
   * Fetch user info after login
   */
  async fetchUserInfo() {
    if (!window.snap?.loginkit) {
      throw new Error('Login Kit SDK not loaded');
    }

    const result = await snap.loginkit.fetchUserInfo();
    this.userInfo = result.data.me;
    this.accessToken = result.data.accessToken;
    
    // Store in localStorage
    localStorage.setItem('snap_user', JSON.stringify({
      displayName: this.userInfo.displayName,
      bitmoji: this.userInfo.bitmoji,
      externalId: this.userInfo.externalId
    }));
    
    // Sync with Supabase
    await this.syncWithSupabase();
    
    // Update UI
    this.updateUI();
    
    return this.userInfo;
  }

  /**
   * Sync Snapchat profile with Supabase
   */
  async syncWithSupabase() {
    try {
      // Get current Supabase user
      const user = window.KORRA_DB?.auth?.getUser ? await window.KORRA_DB.auth.getUser() : null;
      if (!user?.id) return;

      await fetch('/api/v2/auth/snap-sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          snap_external_id: this.userInfo.externalId,
          display_name: this.userInfo.displayName,
          bitmoji_url: this.userInfo.bitmoji?.avatar
        })
      });
    } catch (err) {
      console.warn('Failed to sync with Supabase:', err);
    }
  }

  /**
   * Update UI with Bitmoji
   */
  updateUI() {
    if (!this.userInfo) return;

    // Update header Bitmoji
    const profileImage = document.getElementById('profileImageHeader');
    if (profileImage && this.userInfo.bitmoji?.avatar) {
      profileImage.src = this.userInfo.bitmoji.avatar;
      profileImage.style.borderRadius = '50%';
    }

    // Update settings preview
    const settingsPreview = document.getElementById('settingsProfilePreview');
    if (settingsPreview && this.userInfo.bitmoji?.avatar) {
      settingsPreview.src = this.userInfo.bitmoji.avatar;
    }
  }

  /**
   * Get stored user info
   */
  getStoredUser() {
    const stored = localStorage.getItem('snap_user');
    return stored ? JSON.parse(stored) : null;
  }

  /**
   * Check if user is logged in with Snapchat
   */
  isLoggedIn() {
    return !!this.getStoredUser();
  }

  /**
   * Logout
   */
  logout() {
    localStorage.removeItem('snap_user');
    this.userInfo = null;
    this.accessToken = null;
    
    // Reset UI to default
    const profileImage = document.getElementById('profileImageHeader');
    if (profileImage) {
      profileImage.src = '/assets/user-profile-new.webp';
    }
  }
}

// Initialize global instance
window.SnapLoginKit = new SnapLoginKit();

// Auto-load SDK and update UI on page load
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await window.SnapLoginKit.loadSDK();
    
    // Check for stored user and update UI
    const storedUser = window.SnapLoginKit.getStoredUser();
    if (storedUser) {
      window.SnapLoginKit.userInfo = storedUser;
      window.SnapLoginKit.updateUI();
    }
  } catch (err) {
    console.warn('Login Kit initialization failed:', err);
  }
});

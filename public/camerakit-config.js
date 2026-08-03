/**
 * Snapchat Camera Kit Configuration
 * AI Body Scan SaaS - Virtual Try-On Integration
 */

const CameraKitConfig = {
  // API Tokens
  apiToken: {
    staging: 'eyJhbGciOiJIUzI1NiIsImtpZCI6IkNhbnZhc1MyU0hNQUNQcm9kIiwidHlwIjoiSldUIn0.eyJhdWQiOiJjYW52YXMtY2FudmFzYXBpIiwiaXNzIjoiY2FudmFzLXMyc3Rva2VuIiwibmJmIjoxNzg1NzM4MTYzLCJzdWIiOiI2N2EzNDhiYS1hYTU1LTQxNTgtOTQ1MS05NGZmMjc3ZTk2Yzd-U1RBR0lOR35mOTEzNGFjZC04ZTZiLTQ4MjEtYWJkOS1lMjVjN2RlNTFiZGUifQ.Pf4p8r5z5Dcz7IH_W3kFRS2zy_UQgpFvRVQlkIaflPY',
    production: 'eyJhbGciOiJIUzI1NiIsImtpZCI6IkNhbnZhc1MyU0hNQUNQcm9kIiwidHlwIjoiSldUIn0.eyJhdWQiOiJjYW52YXMtY2FudmFzYXBpIiwiaXNzIjoiY2FudmFzLXMyc3Rva2VuIiwibmJmIjoxNzg1NzM4MTYzLCJzdWIiOiI2N2EzNDhiYS1hYTU1LTQxNTgtOTQ1MS05NGZmMjc3ZTk2Yzd-UFJPRFVDVElPTn5mMjE4MGY3Mi0xOWVhLTRlZDEtYTdjMC1jMDA4MDQxM2I5MDkifQ.Sd2D8tVHzAPgvrT5HLthEcIoet_zh3Dxgx9culi5grI'
  },
  
  // OAuth Client IDs
  clientId: {
    public: 'd6524989-00bd-4129-bbd1-b754ebb43b3b',
    confidential: process.env.SNAP_CONFIDENTIAL_CLIENT_ID || ''
  },
  
  // Lens Configuration
  lens: {
    groupId: '6af97e7a-6e80-4d9e-86b7-8ffe3a6bd150',
    clothingTryOnId: 'ccc9d825-d8ec-41ca-910a-7fd372065026'
  },
  
  // Environment
  environment: window.location.hostname === 'localhost' ? 'staging' : 'production',
  
  // Get active API token
  getApiToken() {
    return this.apiToken[this.environment];
  }
};

// Export for use in other scripts
window.CameraKitConfig = CameraKitConfig;

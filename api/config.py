"""
Environment Configuration for AWS EC2
========================================
Handles environment-specific configuration for Docker-based EC2 deployment.
"""

import os

# Deployment platform: always Docker on EC2
# API Keys storage - use Supabase in production
def get_api_keys_storage():
    """Get appropriate storage for API keys based on environment."""
    return {
        'type': 'env',
        'prefix': 'PRECISIONFIT_API_KEY_'
    }

# Usage log storage - use Supabase in production
def get_usage_log_storage():
    """Get appropriate storage for usage logs based on environment."""
    return {
        'type': 'env',
        'prefix': 'PRECISIONFIT_USAGE_'
    }

# Subscription quotas
SUBSCRIPTION_QUOTAS = {
    'tailor_basic': 0,
    'tailor_pro': 10,
    'tailor_elite': 50,
    'enterprise': 200,
}

# Feature flags
FEATURES = {
    'enable_health_check': True,
    'enable_measurements': True,
    'enable_subscriptions': True,
    'enable_payments': True,
    'enable_admin': True,
    'enable_auth': True,
}

# CORS settings
CORS_ORIGINS = os.environ.get(
    'CORS_ORIGINS',
    'http://localhost:3000,http://localhost:5001,https://korra.work'
).split(',')

# Brevo (formerly Sendinblue) Configuration
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_FROM_EMAIL = os.environ.get('BREVO_FROM_EMAIL', 'hello@korra.work')
BREVO_FROM_NAME = os.environ.get('BREVO_FROM_NAME', 'KORRA AI')

# Maximum function duration (seconds)
MAX_FUNCTION_DURATION = int(os.environ.get('MAX_FUNCTION_DURATION', '300'))

# Timeout settings
FUNCTION_TIMEOUT = int(os.environ.get('FUNCTION_TIMEOUT', '30'))

def get_storage_config():
    """Get storage configuration summary."""
    return {
        'api_keys': get_api_keys_storage(),
        'usage_log': get_usage_log_storage(),
    }

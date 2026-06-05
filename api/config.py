"""
Environment Configuration for Vercel Serverless
============================================
Handles environment-specific configuration for serverless deployment.
"""
import os

# Serverless environment detection
IS_VERCEL = os.environ.get('VERCEL', '0') == '1'
IS_AWS_LAMBDA = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '') != ''
IS_SERVERLESS = IS_VERCEL or IS_AWS_LAMBDA

# API Keys storage - use environment variables in serverless
def get_api_keys_storage():
    """Get appropriate storage for API keys based on environment."""
    if IS_SERVERLESS:
        # Use environment variables in serverless (more reliable)
        return {
            'type': 'env',
            'prefix': 'PRECISIONFIT_API_KEY_'
        }
    else:
        # Use file system in local development
        return {
            'type': 'file',
            'path': 'data/api_keys.json'
        }

# Usage log storage - use environment variables in serverless
def get_usage_log_storage():
    """Get appropriate storage for usage logs based on environment."""
    if IS_SERVERLESS:
        # Use environment variables in serverless
        return {
            'type': 'env',
            'prefix': 'PRECISIONFIT_USAGE_'
        }
    else:
        # Use file system in local development
        return {
            'type': 'file',
            'path': 'data/usage_log.json'
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
    'http://localhost:3000,http://localhost:5001'
).split(',')

# Maximum function duration (Vercel Pro limit)
MAX_FUNCTION_DURATION = int(os.environ.get('MAX_FUNCTION_DURATION', '60'))

# Memory limit (Vercel Hobby is 1024MB, Pro is 3008MB)
FUNCTION_MEMORY = int(os.environ.get('FUNCTION_MEMORY', '1024'))

# Timeout settings
FUNCTION_TIMEOUT = int(os.environ.get('FUNCTION_TIMEOUT', '10'))

def get_storage_config():
    """Get storage configuration summary."""
    return {
        'serverless': IS_SERVERLESS,
        'vercel': IS_VERCEL,
        'aws_lambda': IS_AWS_LAMBDA,
        'api_keys': get_api_keys_storage(),
        'usage_log': get_usage_log_storage(),
    }

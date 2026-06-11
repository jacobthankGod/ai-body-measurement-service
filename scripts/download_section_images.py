#!/usr/bin/env python3
"""Download relevant stock images for industry page sections from Unsplash"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time
import ssl

# Create SSL context that doesn't verify certificates (for compatibility)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Section keywords mapping - search terms mapped to section filenames
SECTION_IMAGES = {
    # luxury-mtm.html
    'digital-savile-row': ['tailor shop london', 'bespoke suit fitting', 'measurement scanner'],
    'zero-error-patterns': ['fashion designer tablet', 'pattern making', 'digital design'],
    'global-bespoke': ['video call fashion', 'international business', 'smartphone measurement'],
    'consistent-standards': ['tailor team', 'professional fitting', 'bespoke workshop'],
    
    # manufacturing.html
    'automated-workflows': ['factory automation', 'industrial robot', 'smart factory'],
    'sustainable-scale': ['sustainable manufacturing', 'fabric cutting', 'eco factory'],
    'factory-integration': ['cad cam', 'pattern cutting machine', 'industrial technology'],
    'mass-personalization': ['warehouse fulfillment', 'package sorting', 'custom packaging'],
    
    # rtw.html
    'reduce-returns': ['fitting room', 'clothes fitting', 'retail mirror'],
    'size-confidence': ['shopping together', 'fashion advice', 'clothing store'],
    'inventory-analytics': ['retail analytics', 'data dashboard', 'business analytics'],
    'seamless-integration': ['pos system', 'retail checkout', 'barcode scanner'],
    
    # bridal.html
    'reduce-rework': ['wedding dress fitting', 'bridal boutique', 'tailor bride'],
    'global-bridal': ['international wedding', 'video call dress', 'global bride'],
    'stress-free-sync': ['bridesmaids group', 'wedding planning', 'phone notification'],
    'party-coordination': ['bridal party', 'bridesmaids dresses', 'wedding group'],
    
    # custom.html
    'fit-first-design': ['virtual try on', '3d fashion', 'augmented reality shopping'],
    'artisan-velocity': ['fast measurement', 'mobile scan', 'self service'], 
    'digital-pattern-sync': ['digital patterns', 'fashion technology', 'design history'],
    'serve-anyone-anywhere': ['global shipping', 'online tailor', 'digital measurement'],
    
    # uniforms.html
    'mass-enrollment': ['corporate event', 'team building', 'employee photos'],
    'deployment-logistics': ['warehouse shipping', 'logistics distribution', 'delivery'],
    'reduced-exchange-costs': ['uniform employee', 'professional corporate', 'company attire'],
    'persistent-sizing': ['repeat order', 'online shopping', 'easy checkout'],
}

OUTPUT_DIR = '/Users/mac/ai-body-scan-saas/public/assets/sections'

def download_unsplash_image(query, filename, orientation='landscape'):
    """Download an image from Unsplash Source (free, no API key needed)"""
    
    # Use Unsplash Source API (deprecated but still works for some images)
    # Alternative: use picsum.photos for reliable free images
    base_url = f"https://picsum.photos/seed/{urllib.parse.quote(query)}/800/450"
    
    output_path = os.path.join(OUTPUT_DIR, f"{filename}.jpg")
    
    # Skip if already exists
    if os.path.exists(output_path):
        print(f"Skipping {filename} - already exists")
        return True
    
    try:
        print(f"Downloading {filename} for: {query}")
        
        # Create request with headers to mimic browser
        req = urllib.request.Request(
            base_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        # Download with SSL context
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            image_data = response.read()
        
        # Save the image
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"  Saved: {output_path}")
        time.sleep(1)  # Rate limiting
        return True
        
    except Exception as e:
        print(f"  Error downloading {filename}: {e}")
        return False

def generate_section_images():
    """Download images for all sections"""
    
    print(f"Creating output directory: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Track results
    results = {}
    
    for section_key, search_terms in SECTION_IMAGES.items():
        # Use first search term as the image seed
        primary_term = search_terms[0]
        success = download_unsplash_image(primary_term, section_key)
        results[section_key] = success
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Downloaded {sum(results.values())}/{len(results)} images")
    print(f"{'='*50}")
    
    return results

if __name__ == '__main__':
    generate_section_images()
    print("\nDone! Images saved to public/assets/sections/")

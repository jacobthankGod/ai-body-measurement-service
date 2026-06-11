#!/usr/bin/env python3
"""Add Get Started buttons to industry pages"""

import os
import re

# Pages to update
PAGES = [
    'luxury-mtm.html',
    'manufacturing.html', 
    'rtw.html',
    'bridal.html',
    'custom.html',
    'uniforms.html',
]

# Add this CSS if not present
HERO_CSS = '''
    .btn-large { height: 56px; padding: 0 40px; font-size: 14px; }
'''

# Add this after hero description
GET_STARTED_HTML = '''
        <a href="/signup.html" class="btn btn-primary btn-large">Get Started</a>
'''

def update_page(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has Get Started in hero
    if 'class="btn btn-primary btn-large"' in content:
        print(f"  Get Started already in hero for {filepath}")
        return False
    
    # Find hero buttons area and add Get Started after existing button
    # Pattern: existing anchor tag in hero
    match = re.search(r'(<a href="/signup\.html" class="btn btn-[^"]+">[^<]+</a>\s*)', content)
    if match:
        # Add another Get Started button
        insert_pos = match.end()
        new_content = content[:insert_pos] + GET_STARTED_HTML + content[insert_pos:]
        
        # Add btn-large CSS if needed
        if '.btn-large' not in content:
            new_content = new_content.replace('.btn-primary {', '.btn-large { height: 56px; padding: 0 40px; font-size: 14px; }\n    .btn-primary {')
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  Added Get Started to {filepath}")
        return True
    
    print(f"  Could not find insertion point in {filepath}")
    return False

def main():
    print("Adding Get Started buttons to industry pages...\n")
    
    for filename in PAGES:
        filepath = os.path.join('/Users/mac/ai-body-scan-saas', filename)
        
        if not os.path.exists(filepath):
            print(f"Skipping {filename} - not found")
            continue
        
        print(f"Processing {filename}...")
        update_page(filepath)
    
    print("\nDone!")

if __name__ == '__main__':
    main()

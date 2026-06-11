#!/usr/bin/env python3
"""Add Global Reach section with accordion to all industry pages"""

import os
import re

# The Global Reach section template to add before the final-banner
GLOBAL_REACH_SECTION = '''
    <!-- GLOBAL REACH SECTION -->
    <section class="block" style="background:rgba(255,255,255,0.01)">
      <div class="container">
        <div class="grid-impact">
          <div>
            <div class="section-eyebrow">Global Reach</div>
            <h2 class="section-title">Bridging the Distance Factor.</h2>
            <p class="section-desc">Korra helps tailors in LMICs unlock access to customers beyond their immediate location. When measurements are shared through chats, photos, or outdated size records, fit becomes inconsistent, costly, and difficult to scale.</p>
            
            <button class="btn-view-more" onclick="document.getElementById('impactAccordionLuxury').classList.toggle('active'); this.textContent = document.getElementById('impactAccordionLuxury').classList.contains('active') ? 'View Less ↑' : 'View Detailed Impact ↓'">View Detailed Impact ↓</button>
            
            <div class="accordion-content" id="impactAccordionLuxury">
              <p style="font-size:16px; color:var(--Neutral-400); line-height:1.6">
                Korra makes remote tailoring more reliable by helping customers capture and share accurate body measurements directly from their phone. This gives tailors a more consistent way to work with remote clients, reduce rework, improve fit confidence, and serve more customers across cities and borders.
                <br><br>
                A customer in London can share measurements in minutes, while a tailor in Lagos delivers with greater accuracy — expanding access to opportunity without the limits of distance.
              </p>
            </div>
          </div>
          <div class="glass-card image-card">
            <img src="/assets/homepage_image.png" alt="Global Reach">
          </div>
        </div>
      </div>
    </section>
'''

# Pages to update with their Get Started URLs
PAGES = {
    'luxury-mtm.html': ('/signup.html', 'Request Private Access'),
    'manufacturing.html': ('/signup.html', 'Start Manufacturing'),
    'rtw.html': ('/signup.html', 'Start Selling'),
    'bridal.html': ('/signup.html', 'Start Fitting'),
    'custom.html': ('/signup.html', 'Start Creating'),
    'uniforms.html': ('/signup.html', 'Start Fitting'),
}

# Additional CSS to add
ADDITIONAL_CSS = '''
    .btn-view-more { background: none; border: none; color: var(--Mint); font-size: 12px; font-weight: 700; cursor: pointer; margin-top: 24px; display: inline-flex; align-items: center; gap: 8px; transition: 0.2s; text-transform: uppercase; letter-spacing: 0.1em; }
    .btn-view-more:hover { opacity: 0.8; }
    .accordion-content { display: none; margin-top: 24px; padding: 24px; background: var(--Glass); border-radius: 16px; border: 1px solid var(--Glass-Border); }
    .accordion-content.active { display: block; animation: fadeIn 0.3s ease-out; }
'''

def add_css_to_file(filepath):
    """Add additional CSS to file if not already present"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if CSS already added
    if '.btn-view-more' in content:
        print(f"  CSS already present in {filepath}")
        return False
    
    # Find position to insert CSS - after .hero p rule
    match = re.search(r'(\.hero p \{[^}]+\})', content)
    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + ADDITIONAL_CSS + content[insert_pos:]
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"  Added CSS to {filepath}")
        return True
    
    print(f"  Could not find CSS insertion point in {filepath}")
    return False

def add_global_reach_section(filepath):
    """Add Global Reach section before final-banner"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already added
    if 'Bridging the Distance Factor' in content:
        print(f"  Global Reach already in {filepath}")
        return False
    
    # Find final-banner section to insert before
    if '<div class="final-banner">' in content:
        content = content.replace('<div class="final-banner">', GLOBAL_REACH_SECTION + '<div class="final-banner">')
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  Added Global Reach to {filepath}")
        return True
    
    print(f"  Could not find final-banner in {filepath}")
    return False

def main():
    print("Adding Global Reach sections to industry pages...\n")
    
    for filename, (signup_url, cta_text) in PAGES.items():
        filepath = os.path.join('/Users/mac/ai-body-scan-saas', filename)
        
        if not os.path.exists(filepath):
            print(f"Skipping {filename} - not found")
            continue
        
        print(f"Processing {filename}...")
        
        # Add CSS
        add_css_to_file(filepath)
        
        # Add Global Reach section
        add_global_reach_section(filepath)
    
    print("\nDone!")

if __name__ == '__main__':
    main()

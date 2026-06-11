#!/usr/bin/env python3
"""Add accordion expand functionality to existing sections on all industry pages"""

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

# CSS for accordion - add after .section-desc
ACCORDION_CSS = '''
    .accordion-toggle { background: none; border: none; color: var(--Neutral-400); font-size: 11px; font-weight: 700; cursor: pointer; margin-top: 16px; display: inline-flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.1em; transition: 0.2s; }
    .accordion-toggle:hover { color: var(--Mint); }
    .accordion-expand { display: none; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--Glass-Border); }
    .accordion-expand.active { display: block; animation: fadeIn 0.3s ease-out; }
'''

# Detailed content for each section by page type
# Each section gets expanded content - these are placeholders that elaborate on the section title
SECTION_CONTENT = {
    'luxury-mtm.html': {
        'Digital Savile Row': 'Leverage computer vision to capture 50+ body measurements in under 60 seconds. Each scan produces a precision-fitted digital twin that retains measurements for future reference, enabling pattern adjustments without re-measuring.',
        'Zero-Error Patterns': 'Our AI-driven regression model achieves ±0.5cm accuracy across all body types. Combined with your craftsmanship, this eliminates the guesswork that leads to costly returns and fabric waste.',
        'Global Bespoke': 'Share digital measurements instantly via chat or email. Clients receive a downloadable size passport they can use anywhere. Expand your clientele beyond geographic boundaries.',
        'Consistent Standards': 'Every scan uses the same calibrated algorithm. Maintain your brand\'s reputation for precision regardless of which team member conducts the measurement session.',
    },
    'manufacturing.html': {
        'Mass Personalization': 'Enable B2B buyers to capture their measurements once and reuse across multiple orders. Reduce returns by up to 40% with precise size data.',
        'Size Intelligence': 'Aggregate anonymized size data across your entire customer base. Identify sizing trends and adjust production to match actual demand patterns.',
        'Digital Integration': 'Export measurements directly to your CAD/CAM systems. Seamless API integration with major PLM platforms for automated pattern scaling.',
        'Quality Assurance': 'Compare finished garment measurements against original scan data. Verify fit before shipping and reduce costly rework logistics.',
    },
    'rtw.html': {
        'Reduce Returns': 'Help customers find their perfect fit with accurate measurements. Reduce return rates by providing size guidance based on actual body data rather than generic size charts.',
        'Size Confidence': 'Build customer trust with personalized size recommendations. AI-powered suggestions consider body measurements, style preferences, and fabric stretch.',
        'Inventory Analytics': 'Aggregate anonymized size data to identify trends. Make smarter purchasing decisions based on actual customer body type distribution.',
        'Seamless Integration': 'Connect with your existing POS and e-commerce systems. Enable barcode scanning and size lookup for faster checkout experiences.',
    },
    'bridal.html': {
        'Bridal Precision': 'Capture intricate measurements for complex gown designs. Document every detail for future alterations or reorder requests.',
        'Alteration Records': 'Maintain digital records of all alterations made post-delivery. Enable faster turnaround for future wedding party orders.',
        'Group Coordination': 'Efficiently manage measurements for entire bridal parties. Track progress and ensure consistent sizing across all members.',
        'Memory Preservation': 'Store measurements as part of the wedding memory digital archive. Enable dress re-creation for anniversary celebrations.',
    },
    'custom.html': {
        'Design Verification': 'Show customers how their custom designs will fit their body type before production. Reduce expensive misalignments.',
        'Pattern Archive': 'Save custom patterns linked to customer measurements. Enable quick modifications or re-orders without starting from scratch.',
        'Client Library': 'Build a comprehensive measurement database of all clients. Improve turnaround on repeat orders and custom projects.',
        'Design Freedom': 'Expand your design capabilities knowing measurements will be precise. Take on complex custom projects with confidence.',
    },
    'uniforms.html': {
        'Team Sizing': 'Efficiently coordinate measurements for entire teams or organizations. Track completion status and ensure consistent sizing.',
        'Role-Based Fit': 'Document fit requirements by role. Adjust sizing standards for different body types associated with specific positions.',
        'Reorder Automation': 'Streamline reorder processes with stored measurements. Simplify annual uniform refresh cycles.',
        'Compliance Records': 'Maintain measurement records for uniform compliance. Quickly produce documentation when required.',
    },
}

def add_accordion_css(filepath):
    """Add accordion CSS to file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    if '.accordion-toggle' in content:
        return False
    
    # Add after .section-desc
    new_content = content.replace(
        '.section-desc { font-size: 18px; color: var(--Neutral-400); line-height: 1.6; margin-top: var(--S-24); max-width: 550px; font-weight: 500; }',
        '.section-desc { font-size: 18px; color: var(--Neutral-400); line-height: 1.6; margin-top: var(--S-24); max-width: 550px; font-weight: 500; }' + ACCORDION_CSS
    )
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    return True

def add_accordion_to_sections(filepath, page_content):
    """Add accordion expand buttons to each section"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    sections_added = 0
    
    for title, expanded_text in page_content.items():
        # Skip if already has accordion for this section
        accordion_id = f"accordion-{title.lower().replace(' ', '-')}"
        if accordion_id in content:
            continue
        
        # Find the section with this title and add accordion after the description
        pattern = rf'(<h2 class="section-title">{re.escape(title)}</h2>\s*<p class="section-desc">[^<]+</p>\s*)'
        
        if re.search(pattern, content):
            replacement = rf'''\1
            <button class="accordion-toggle" onclick="this.nextElementSibling.classList.toggle('active'); this.textContent = this.nextElementSibling.classList.contains('active') ? 'Show Less ↑' : 'View Details ↓'">View Details ↓</button>
            <div class="accordion-expand" id="{accordion_id}">
              <p style="font-size:14px; color:var(--Neutral-400); line-height:1.6">{expanded_text}</p>
            </div>'''
            
            content = re.sub(pattern, replacement, content)
            sections_added += 1
    
    if sections_added > 0:
        with open(filepath, 'w') as f:
            f.write(content)
    
    return sections_added

def main():
    print("Adding accordion expand to existing sections on all industry pages...\n")
    
    for filename in PAGES:
        filepath = os.path.join('/Users/mac/ai-body-scan-saas', filename)
        
        if not os.path.exists(filepath):
            print(f"Skipping {filename} - not found")
            continue
        
        print(f"Processing {filename}...")
        
        # Add CSS
        add_accordion_css(filepath)
        
        # Get page-specific content
        page_content = SECTION_CONTENT.get(filename, {})
        sections = add_accordion_to_sections(filepath, page_content)
        print(f"  Added {sections} accordion sections")
    
    print("\nDone!")

if __name__ == '__main__':
    main()

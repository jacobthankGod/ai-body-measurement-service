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
    .accordion-toggle { background: none; border: none; color: var(--Mint); font-size: 11px; font-weight: 700; cursor: pointer; margin-top: 16px; display: inline-flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.1em; transition: 0.2s; }
    .accordion-toggle:hover { color: var(--White); }
    .accordion-expand { display: none; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--Glass-Border); }
    .accordion-expand.active { display: block; animation: fadeIn 0.3s ease-out; }
'''

# Detailed content for each section by page type
# Each section gets expanded content - these are placeholders that elaborate on the section title
# NOTE: Section titles must exactly match what's in each HTML page
SECTION_CONTENT = {
    'luxury-mtm.html': {
        'Digital Savile Row': 'Leverage computer vision to capture 50+ body measurements in under 60 seconds. Each scan produces a precision-fitted digital twin that retains measurements for future reference, enabling pattern adjustments without re-measuring. Our proprietary algorithm calibrates automatically to account for posture, lighting conditions, and camera angle variations, ensuring consistent accuracy across all capture environments.',
        'Zero-Error Patterns': 'Our AI-driven regression model achieves ±0.5cm accuracy across all body types. Combined with your craftsmanship, this eliminates the guesswork that leads to costly returns and fabric waste. The system learns from your specific client base and adjusts pattern drafting recommendations based on historical fit feedback, creating a continuously improving fit prediction engine.',
        'Global Bespoke': 'Share digital measurements instantly via chat or email. Clients receive a downloadable size profile they can use anywhere. Expand your clientele beyond geographic boundaries. Measurement packages include 3D mesh exports compatible with major CAD systems including CLO, Browzwear, and OptiTex for seamless pattern integration.',
        'Consistent Standards': 'Every scan uses the same calibrated algorithm. Maintain your brand\'s reputation for precision regardless of which team member conducts the measurement session. Eliminates inter-measurer variance that typically accounts for 2-3cm discrepancies between different fittings.',
    },
    'manufacturing.html': {
        'Automated Workflows': 'Automate measurement capture across your supply chain. Integrate with existing ERP systems for seamless data flow. Our REST API enables bidirectional sync with SAP, Oracle, and custom ERPs, automatically triggering pattern generation workflows when new measurements arrive.',
        'Sustainable Scale': 'Reduce fabric waste by up to 30% with accurate sizing. Meet sustainability goals while scaling production. Precise measurement data enables fabric optimization algorithms that calculate optimal cut layouts, reducing material costs while maintaining perfect fit across all sizes.',
        'Factory Integration': 'Export precise body measurements directly to pattern cutting machines. Reduce manual adjustments and rework. Direct CAD integration with Gerber, Lectra, and Bullmer systems eliminates manual data entry and ensures pattern markers reflect actual client measurements.',
        'Mass Personalization': 'Enable B2B buyers to capture measurements once and reuse across multiple orders. Reduce returns by up to 40%. Persistent measurement profiles store complete biometric data that updates automatically with each new scan, enabling repeat orders without re-measuring.',
    },
    'rtw.html': {
        'Reduce Returns': 'Help customers find their perfect fit with accurate measurements. Reduce return rates by providing size guidance based on actual body data rather than generic size charts. Integration with Shopify, Magento, and custom e-commerce platforms displays personalized size recommendations at checkout.',
        'Size Confidence': 'Build customer trust with personalized size recommendations. AI-powered suggestions consider body measurements, style preferences, and fabric stretch. Machine learning models continuously improve recommendations based on actual return data, learning which fit preferences correlate with lower return rates.',
        'Inventory Analytics': 'Aggregate anonymized size data to identify trends. Make smarter purchasing decisions based on actual customer body type distribution. Dashboard visualizations reveal size demand patterns by region, season, and style, enabling data-driven inventory planning.',
        'Seamless Integration': 'Connect with your existing POS and e-commerce systems. Enable barcode scanning and size lookup for faster checkout experiences. Works with Square, Shopify POS, and major retail systems to display customer size profiles instantly at point of sale.',
    },
    # bridal.html sections - 4 section titles: Reduce Rework, Global Bridal, Stress-Free Sync, Party Coordination
    'bridal.html': {
        'Reduce Rework': 'Capture precise measurements for complex gown designs. Minimize costly alterations and rework. Multi-angle capture technology ensures Bride measurement data is accurate within ±0.5cm, even for intricate measuring points that traditional tape methods miss.',
        'Global Bridal': 'Manage bridal parties anywhere in the world. Coordinate measurements across time zones. Cloud-based collaboration tools enable overseas bridesmaids to capture their measurements independently while the lead tailor monitors progress centrally.',
        'Stress-Free Sync': 'Keep all parties informed with automated fit status updates. Eliminate miscommunication. Customized notification system alerts relevant parties when measurement milestones are reached, fitting deadlines approach, or alterations are needed.',
        'Party Coordination': 'Efficiently manage measurements for entire bridal parties. Track progress and sizing consistency. Batch processing tools enable rapid overview of entire party measurement status, highlighting at-risk sizes requiring immediate attention.',
    },
    # custom.html sections - 4 section titles: Fit-First Design, Artisan Velocity, Digital Pattern Sync, Serve Anyone, Anywhere
    'custom.html': {
        'Fit-First Design': 'Validate custom designs against customer body data before production. Reduce expensive misalignments. Virtual try-on technology displays proposed garment proportions on customer digital twin, enabling design adjustments before fabric is cut.',
        'Artisan Velocity': 'Speed up the custom measurement process. Capture measurements in minutes, not hours. Guided capture interface walks customers through self-measurement process with real-time feedback, reducing appointment duration while improving accuracy.',
        'Digital Pattern Sync': 'Save patterns linked to customer measurements. Enable quick modifications for repeat orders. Pattern versioning system maintains complete measurement history alongside corresponding pattern adjustments, enabling precise reproduction of previous commissions.',
        'Serve Anyone, Anywhere': 'Work with customers globally. Measurements travel with the customer, not just the order. Our profile system enables recurring customers to share their measurement profile with any connected tailor, eliminating re-measuring for every commission.',
    },
    # uniforms.html sections - 4 section titles: Mass Enrollment, Deployment Logistics, Reduced Exchange Costs, Persistent Sizing
    'uniforms.html': {
        'Mass Enrollment': 'Coordinate measurements for entire organizations efficiently. Batch process large teams. Self-service capture links enable distributed workforce to measure independently, with admin dashboards tracking organizational-wide enrollment progress.',
        'Deployment Logistics': 'Streamline uniform distribution across locations. Track shipments by size and role. Integrated logistics dashboard connects measurement profiles with distribution networks, ensuring correct sizes arrive at correct locations.',
        'Reduced Exchange Costs': 'Get sizing right the first time. Minimize costly exchanges and re-shipments. Pre-distribution size validation against employee measurement profiles catches ordering errors before uniforms ship.',
        'Persistent Sizing': 'Store measurements for future orders. Simplify annual uniform refresh cycles. Employee measurement profiles persist across ordering cycles, enabling one-click reordering with automatic size verification against previous orders.',
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

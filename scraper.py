import requests
import bs4
import json
import os
from datetime import datetime

# --- Configuration ---
DATA_FILE = 'companies.json'
TEMPLATE_FILE = 'template.html'
OUTPUT_FILE = 'index.html'
KLB_URL = "https://keurmerkleegstandbeheer.nl/gecertificeerden/"

def get_current_companies():
    """Scrapes the live list of companies from the KLB website."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(KLB_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        
        # CORRECTED SELECTOR: The website changed its class name for company blocks.
        company_blocks = soup.find_all('div', class_='jet-listing-grid__item')
        
        if not company_blocks:
            print("Warning: No company blocks found with the selector. The website structure may have changed again.")
            return None, "stale"

        live_companies = {}
        for block in company_blocks:
            # The link is now the main container for the content
            link_tag = block.find('a', class_='jet-listing-grid__item-instance')
            img_tag = link_tag.find('img') if link_tag else None

            if link_tag and img_tag:
                website = link_tag.get('href', '').strip()
                name = img_tag.get('alt', 'Unknown Name').strip()
                if name and website:
                    live_companies[website] = name
        
        if not live_companies:
             print("Warning: Company blocks were found, but no company data could be extracted.")
             return None, "stale"

        return live_companies, "success"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching KLB website: {e}")
        return None, "stale"

def load_previous_data():
    """Loads the last known company data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {'companies': {}} # Return empty if file is corrupt
    return {'companies': {}} # Return empty structure if no file

def generate_html(data):
    """Generates the final index.html from the template and data."""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: {TEMPLATE_FILE} not found!")
        return
        
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()

    # --- Status Indicator ---
    status_class = "stale"
    status_text = "Stale"
    if data.get('update_status') == 'success':
        status_class = "fresh"
        status_text = "Fresh"
        
    last_update_utc_str = "Never"
    if 'last_update_utc' in data:
        last_update_utc = datetime.fromisoformat(data['last_update_utc'])
        last_update_utc_str = last_update_utc.strftime('%d-%m-%Y %H:%M:%S UTC')

    status_html = f'<span class="status-indicator {status_class}">●</span> {status_text} (Last updated: {last_update_utc_str})'
    
    # --- Company Cards ---
    cards_html = ""
    # Check if 'companies' key exists and is a dictionary
    company_dict = data.get('companies', {})
    if isinstance(company_dict, dict):
        sorted_companies = sorted(company_dict.values(), key=lambda x: x.get('name', ''))
        
        for company in sorted_companies:
            status_dot_class = "accredited" if company.get('status') == 'accredited' else "unlisted"
            status_text_val = "Accredited" if company.get('status') == 'accredited' else "Accreditation Lost"

            cards_html += f"""
            <div class="card">
                <h3>{company.get('name', 'No Name')}</h3>
                <p><span class="status-indicator {status_dot_class}">●</span> {status_text_val}</p>
                <a href="{company.get('website', '#')}" target="_blank">{company.get('website', 'No Website')}</a>
            </div>
            """
    
    if not cards_html:
        cards_html = "<p>No company data to display. The scraper might need an update.</p>"

    # --- Replace placeholders and write file ---
    final_html = template.replace('{{STATUS_HTML}}', status_html)
    final_html = final_html.replace('{{COMPANY_CARDS}}', cards_html)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(final_html)
    print(f"Successfully generated {OUTPUT_FILE}.")

def main():
    """Main execution function."""
    previous_data = load_previous_data()
    previous_companies = previous_data.get('companies', {})
    
    live_companies, status = get_current_companies()
    
    now_utc_iso = datetime.utcnow().isoformat()

    if status == "stale":
        # Scrape failed, use old data but update status
        previous_data['update_status'] = 'stale'
        previous_data['last_update_utc'] = now_utc_iso
        final_data = previous_data
    else:
        # Scrape succeeded, compare and update data
        updated_companies = {}
        
        # Process live companies
        for website, name in live_companies.items():
            if website in previous_companies:
                # Company persists
                updated_companies[website] = previous_companies[website]
                updated_companies[website]['status'] = 'accredited'
                updated_companies[website]['name'] = name # Update name in case it changed
            else:
                # New company found
                updated_companies[website] = {
                    'name': name,
                    'website': website,
                    'status': 'accredited',
                    'first_seen_utc': now_utc_iso,
                }
        
        # Process old companies to find unlisted ones
        for website, data in previous_companies.items():
            if website not in live_companies:
                unlisted_company = data
                unlisted_company['status'] = 'unlisted'
                updated_companies[website] = unlisted_company

        final_data = {
            'last_update_utc': now_utc_iso,
            'update_status': 'success',
            'companies': updated_companies
        }

    with open(DATA_FILE, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    generate_html(final_data)

if __name__ == "__main__":
    main()

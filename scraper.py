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
    """Scrapes the live list of companies from the raw HTML."""
    print(f"Fetching {KLB_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(KLB_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        # Find the h2 heading to anchor our search
        heading = soup.find('h2', string='BEHEERDERS MET HET KEURMERK')
        if not heading:
            print("Error: Could not find the main heading 'BEHEERDERS MET HET KEURMERK'.")
            return None, "stale"

        # Find the first <ul> that comes after the heading
        company_list_ul = heading.find_next('ul')
        if not company_list_ul:
            print("Error: Could not find the company list (<ul>) after the heading.")
            return None, "stale"
        
        live_companies = {}
        # Find all list items within that specific list
        for li in company_list_ul.find_all('li'):
            link_tag = li.find('a')
            if link_tag and link_tag.get('href') and not '.pdf' in link_tag.get('href'):
                website = link_tag.get('href').strip()
                name = link_tag.text.strip()
                if name and website:
                    live_companies[website] = name

        if not live_companies:
             print("Warning: Found the list but could not extract any company data.")
             return None, "stale"

        print(f"Successfully scraped {len(live_companies)} companies.")
        return live_companies, "success"

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None, "stale"

def load_previous_data():
    """Loads the last known company data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {'companies': {}}
    return {'companies': {}}

def generate_html(data):
    """Generates the final index.html from the template and data."""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: {TEMPLATE_FILE} not found!")
        return
        
    with open(TEMPLATE_FILE, 'r') as f:
        template = f.read()

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
    
    cards_html = ""
    company_dict = data.get('companies', {})
    if isinstance(company_dict, dict) and company_dict:
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
        cards_html = "<p>No company data to display.</p>"

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
        previous_data['update_status'] = 'stale'
        previous_data['last_update_utc'] = now_utc_iso
        final_data = previous_data
    else:
        updated_companies = {}
        for website, name in live_companies.items():
            if website in previous_companies:
                updated_companies[website] = previous_companies[website]
                updated_companies[website]['status'] = 'accredited'
                updated_companies[website]['name'] = name
            else:
                updated_companies[website] = { 'name': name, 'website': website, 'status': 'accredited', 'first_seen_utc': now_utc_iso }
        
        for website, data in previous_companies.items():
            if website not in live_companies:
                unlisted_company = data
                unlisted_company['status'] = 'unlisted'
                updated_companies[website] = unlisted_company

        final_data = { 'last_update_utc': now_utc_iso, 'update_status': 'success', 'companies': updated_companies }

    with open(DATA_FILE, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    generate_html(final_data)

if __name__ == "__main__":
    main()

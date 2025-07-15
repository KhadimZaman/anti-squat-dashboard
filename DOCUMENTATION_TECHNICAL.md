# Technical Specification

**Project:** Automated Anti-Squat Company Dashboard

### 1. System Architecture
The system is built on a "serverless" static site generator architecture. It uses free-tier services provided by GitHub.
- **Hosting:** The final dashboard is a static HTML page hosted on **GitHub Pages**.
- **Automation:** The data scraping and page generation logic is executed on a schedule by **GitHub Actions**.
- **Data Storage:** The application state (the list of companies) is stored in a `companies.json` file directly within the GitHub repository, acting as a simple, file-based database.

### 2. Key Components (Files)
- **`.github/workflows/scrape.yml`**: The automation engine. This YAML file defines a GitHub Actions workflow that:
    - Triggers on a daily schedule (`cron`) or when manually dispatched.
    - Sets up a Linux runner environment with Python.
    - Installs the required Python libraries.
    - Executes the `scraper.py` script.
    - Commits the resulting `index.html` and `companies.json` files back to the repository.
- **`scraper.py`**: The core application logic written in Python. Its responsibilities are:
    1.  Fetch the raw HTML from the target URL using the `requests` library.
    2.  Parse the HTML using `BeautifulSoup` to find a specific `<ul>` list containing the company data.
    3.  Load the previous company list from `companies.json`.
    4.  Compare the new list with the old list to determine the status of each company ('accredited', 'unlisted').
    5.  Save the updated, comprehensive list back to `companies.json`.
    6.  Read the `template.html` file, inject the company data into it, and write the final `index.html` file.
- **`companies.json`**: A JSON file that acts as the system's database. It stores a dictionary of all companies ever seen, along with their name, website, status, and the date they were first seen. It also contains metadata about the last update.
- **`template.html`**: A static HTML file that serves as the visual template for the dashboard. It contains CSS for styling and placeholders (e.g., `{{STATUS_HTML}}`, `{{COMPANY_CARDS}}`) that are replaced by the `scraper.py` script.
- **`requirements.txt`**: A simple text file listing the Python dependencies (`requests`, `beautifulsoup4`) required for the project.

### 3. Data Flow (On a Scheduled Run)
1.  GitHub Actions triggers the workflow based on the schedule in `scrape.yml`.
2.  The script `scraper.py` is executed.
3.  The script scrapes the KLB website.
4.  The script reads the old `companies.json`.
5.  The script generates a new, updated `companies.json` with the latest data and statuses.
6.  The script generates a new `index.html` file by populating `template.html` with the new data.
7.  The GitHub Action commits these two updated files back to the repository.
8.  GitHub Pages automatically serves the new `index.html` to the public URL.

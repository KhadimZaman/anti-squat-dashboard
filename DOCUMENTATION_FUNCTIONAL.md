# Functional & Requirements Specification

**Project:** Automated Anti-Squat Company Dashboard

### 1. Project Goal
The primary goal of this system is to automate the process of finding and monitoring certified anti-squat (antikraak) organizations in the Netherlands. It aims to save the user significant manual effort by providing a centralized, auto-updating dashboard of all trustworthy companies.

### 2. Key Features & Requirements
- **R1: Automated Data Fetching:** The system must automatically fetch the list of all companies officially certified by the Keurmerk Leegstandbeheer (KLB) from their website.
- **R2: Public Dashboard:** The fetched list of companies must be displayed on a clean, publicly accessible webpage (dashboard).
- **R3: Serverless Operation:** The system must run entirely in the cloud, requiring no local computer to be running for processing or hosting. The user only needs a web browser to view the result.
- **R4: Change Tracking:** The system must track changes to the certified list over time.
    - **R4.1:** Companies newly added to the KLB list must appear on the dashboard.
    - **R4.2:** Companies removed from the KLB list must not be deleted from the dashboard but instead be visually marked as "Accreditation Lost".
- **R5: Health Status:** The dashboard must display a clear status indicator ("Fresh" / "Stale") and a timestamp to show the health and recency of the last data scrape.

### 3. User Interaction
- The primary interaction is for the user to visit the public GitHub Pages URL to view the dashboard.
- The user can check the status indicator to verify that the data is recent and the last automated run was successful.
- The system is designed to be "view-only" with no buttons or inputs on the final webpage.

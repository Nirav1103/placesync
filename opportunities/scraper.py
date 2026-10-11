import requests
from bs4 import BeautifulSoup
import re

def scrape_career_opportunities(url):
    """
    Scrapes job postings from a target URL.
    Returns a list of dictionaries with scraped fields:
    - company_name
    - role
    - package
    - location
    - deadline
    - source
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        postings = []
        
        # Look for elements with card-like classes
        cards = soup.select('.job-card, .job-item, .career-item, tr.job-row')
        
        if not cards:
            # Fallback: search for list items or divs that look like jobs
            cards = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'job|career|vacancy|posting', re.I))
            
        for card in cards:
            company = ""
            role = ""
            package = ""
            location = ""
            deadline = ""
            source = url
            
            # 1. Company Name
            comp_el = card.find(class_=re.compile(r'company|employer|brand', re.I))
            if comp_el:
                company = comp_el.get_text().strip()
                
            # 2. Role / Title
            role_el = card.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile(r'title|role|position|heading', re.I))
            if role_el:
                role = role_el.get_text().strip()
            elif not role:
                link_el = card.find('a')
                if link_el:
                    role = link_el.get_text().strip()
                    if link_el.has_attr('href'):
                        href = link_el['href']
                        if href.startswith('http'):
                            source = href
                        elif href.startswith('/'):
                            from urllib.parse import urljoin
                            source = urljoin(url, href)
            
            # 3. Location
            loc_el = card.find(class_=re.compile(r'location|loc|city|address', re.I))
            if loc_el:
                location = loc_el.get_text().strip()
                
            # 4. Package / Salary
            pkg_el = card.find(class_=re.compile(r'salary|package|pay|compensation|ctc', re.I))
            if pkg_el:
                package = pkg_el.get_text().strip()
                
            # 5. Deadline
            dead_el = card.find(class_=re.compile(r'deadline|expiry|date|date-end|expire', re.I))
            if dead_el:
                deadline = dead_el.get_text().strip()
                deadline = re.sub(r'^(deadline|apply by|expires|date)\s*:?\s*', '', deadline, flags=re.I).strip()
                
            if company or role:
                postings.append({
                    'company_name': company or "Unknown Company",
                    'role': role or "Unknown Position",
                    'package': package,
                    'location': location,
                    'deadline': deadline,
                    'source': source
                })
                
        return postings
    except Exception as e:
        print(f"Scraping error: {e}")
        return []

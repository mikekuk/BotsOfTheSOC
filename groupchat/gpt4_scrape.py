# filename: gpt4_scrape.py

import requests
from bs4 import BeautifulSoup
import re

# Constants for the arxiv API
BASE_URL = 'http://export.arxiv.org/api/query?'

# Query parameters
query_params = {
    'search_query': 'all:gpt-4',
    'start': 0,
    'max_results': 1,
    'sortBy': 'submittedDate',
    'sortOrder': 'descending'
}

# Perform the GET request
response = requests.get(BASE_URL, params=query_params)

# Parse the response
soup = BeautifulSoup(response.text, 'lxml')

# Extract the first (latest) entry
entry = soup.find('entry')

if entry is None:
    print("No paper found on GPT-4")
else:
    # Extract and print the title, author, submitted date, and abstract
    title = entry.title.string
    authors = ', '.join(author.find('name').string for author in entry.find_all('author'))
    submitted_date = entry.published.string
    abstract = entry.summary.string

    print(f"Title: {title}")
    print(f"Authors: {authors}")
    print(f"Submitted Date: {submitted_date}")

    # Search for potential software applications
    software_applications = re.findall(r'\bsoftware\b', abstract, re.IGNORECASE)

    if software_applications:
        print("Potential software applications found in the abstract:\n", abstract)
    else:
        print("No explicit mention of software applications in the given abstract.")
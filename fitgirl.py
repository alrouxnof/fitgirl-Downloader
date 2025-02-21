import requests
from bs4 import BeautifulSoup
import runpy
import os
from urllib.parse import urlparse

def is_valid_url(url):
    """Check if the provided URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def extract_links_from_div(url, div_class, site=1):
    """Extract links from the specified div based on site selection."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to retrieve webpage: {e}")

    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div', class_=div_class)
    
    if len(divs) < site + 1:
        raise Exception(f"Not enough divs found (required: {site + 1}, found: {len(divs)}).")
    if site > 5 or site < 0:
        raise Exception("Invalid site selection (0-5).")

    selected_div = divs[site]
    links = [a['href'] for a in selected_div.find_all('a', href=True) if a['href']]
    
    if not links:
        raise Exception(f"No links found in div index {site}.")
    
    return links

def main():
    """Main function to extract links and trigger the downloader."""
    url = input("Enter FitGirl Game URL: ").strip()
    if not is_valid_url(url):
        print("Error: Invalid URL. Use format https://example.com.")
        return

    try:
        site = int(input("Site (0-DataNodes, 1-FuckingFast, 0-5, default 1): ") or 1)
    except ValueError:
        print("Invalid site input. Defaulting to 1 (FuckingFast).")
        site = 1

    div_class = "su-spoiler-content su-u-clearfix su-u-trim"
    script_path = "Downloader.py"
    file_path = "links.txt"

    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found.")
        return

    try:
        print(f"Fetching links from site {site}...")
        links = extract_links_from_div(url, div_class, site=site)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(links))
        print(f"Found {len(links)} links.")

        if input(f"Download {len(links)} files? (y/N): ").lower().strip() != 'y':
            print("Download cancelled.")
            return

        print("Starting downloads...")
        runpy.run_path(script_path, run_name="__main__")
        with open(file_path, 'w', encoding='utf-8'):
            pass
        print("Done.")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Keeping links.txt intact.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
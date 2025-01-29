import requests
from bs4 import BeautifulSoup
import runpy

def extract_links_from_div(url, div_class, a_href_class=None, site=1):
    # Send a GET request to the URL
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve the webpage. Status code: {response.status_code}")

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all divs with the specified class
    divs = soup.find_all('div', class_=div_class)
    
    # Check if at least second div exists
    if len(divs) < 2:
        raise Exception("Could not find a second div with the specified class.")
    
    if site > 5:
        raise Exception("invalid site: please select between 0-Data nodes and 1-Fucking fast or other sites between 0-4.")

    # Select the second div
    second_div = divs[site]
    
    # Find all <a> tags within this div
    links = []
    for a in second_div.find_all('a', href=True):
        if a_href_class is None or a_href_class in a.get('class', []):
            links.append(a['href'])

    return links

def main():
    url = input("Enter your fitgirl Game Url:  ")  # Replace with the actual URL
    div_class = "su-spoiler-content su-u-clearfix su-u-trim"  # Replace with the class of the div
    # a_href_class = "your_a_class"  # Uncomment and set if the <a> tag has a specific class
    site = int(input("Enter the site to download: 0-datanodes, 1-fuckingfast (0-1, default is 1): ") or 1)
    script_path = "Downloader.py"
    file_path = "links.txt"

    # Check if links.txt exists, if not, create it
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass
        print(f"Created {file_path} because it did not exist.")

    try:
        hrefs = extract_links_from_div(url, div_class)  # , a_href_class)
        
        # Write links to a temporary text file
        with open("links.txt", "w") as file:
            for link in hrefs:
                file.write(f"{link}\n")
        
        print(f"Links have been written to links.txt. Total links found: {len(hrefs)}")
        runpy.run_path(script_path, run_name="__main__")
        # Clean up the links.txt file after successful download
        with open(file_path, 'w'):
            pass  # This will clear the file by opening it in write mode and not writing anything
        print(f"Cleaned up {file_path} after download.")


    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

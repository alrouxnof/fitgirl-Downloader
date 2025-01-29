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
    file_path = "/home/alrouxnof/programming/python/projects/fitgirl-Downloader/links.txt"

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



# import requests
# from bs4 import BeautifulSoup
# import tempfile

# # Function to fetch and process the URL
# def extract_links(url, target_class, index=1):
#     try:
#         # Fetch the HTML content of the webpage
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an error for HTTP issues

#         # Parse the HTML using BeautifulSoup
#         soup = BeautifulSoup(response.text, 'html.parser')

#         # Find the target div with the specified class
#         target_div = soup.find('div', class_=target_class)
#         if not target_div:
#             print(f"No <div> with class '{target_class}' found.")
#             return

#         # Get the first four <div> elements inside the target div
#         inner_divs = target_div.find_all('div', limit=4)
#         # if len(inner_divs) < 4:
#         #     print("Less than  <div> elements found inside the target div.")
#         #     return

#         # Choose the specific inner <div> based on the index
#         selected_div = inner_divs[index] if 0 <= index < len(inner_divs) else inner_divs[1]

#         # Extract all <a> tags and their href attributes from the selected div
#         links = [a['href'] for a in selected_div.find_all('a', href=True)]

#         if not links:
#             print("No links found in the selected <div>.")
#             return

#         # Write links to a temporary text file
#         with open("links.txt", "a") as linkfile:
#             for link in links:
#                 linkfile.write(link + '\n')
#             print(f"Links written to: {linkfile.name}")

#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching URL: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")

# # Example usage
# url = input("Enter the URL: ")
# target_class = "su-spoiler-content su-u-clearfix su-u-trim"
# index = int(input("Enter the site to download: 0-datanodes, 1-fuckingfast (0-1, default is 1): ") or 1)
# extract_links(url, target_class, index)




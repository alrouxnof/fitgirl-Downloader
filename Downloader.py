import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import re
from tqdm.asyncio import tqdm

async def fetch_html(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.text()
        else:
            raise Exception(f"Failed to fetch HTML from {url}. Status: {response.status}")

def extract_download_url(html, div_class):
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find('div', class_=div_class)
    if not div:
        raise Exception(f"No div with class '{div_class}' found.")
    
    script = div.find('script')
    if not script:
        raise Exception("No script element found within the specified div.")
    
    # Look for the download() function and extract the URL
    match = re.search(r'window\.open\([\'"](.*?)[\'"]\)', script.text)
    if match:
        return match.group(1)
    else:
        raise Exception("No download URL found in script's download() function.")

async def process_url(session, page_url, dest_path, div_class, overall_pbar, base_name):
    try:
        # Split the page_url to get both the URL and the text
        page_url, link_text = page_url.split('|', 1)
        html = await fetch_html(session, page_url)
        download_url = extract_download_url(html, div_class)
        
        # Use the text from the <a> tag in the filename
        filename = f"{base_name}_{download_url.split('/')[-1]}"
        file_path = os.path.join(dest_path, filename)
        
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            raise
        
        # Initialize the progress bar with a constant description
        file_pbar = tqdm(desc=f"Downloading {filename}", unit='B', unit_scale=True, position=1, leave=True, bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]')
        
        await download_file(session, download_url, file_path, file_pbar)
        file_pbar.close()
    except Exception as e:
        print(f"Error processing {page_url}: {e}")
    finally:
        overall_pbar.update(1)

async def download_file(session, url, dest_path, pbar):
    filename = url.split('/')[-1]
    file_path = os.path.join(dest_path, filename)

    max_length = 255  # Example limit, adjust as needed
    if len(filename) > max_length:
        filename = filename[:max_length - len(os.path.splitext(filename)[1])] + os.path.splitext(filename)[1]

    async with session.get(url) as response:
        if response.status == 200:
            total_size = int(response.headers.get('Content-Length', 0))
            pbar.total = total_size if total_size > 0 else None
            
            with open(file_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
                    pbar.update(len(chunk))
        else:
            print(f"Failed to download {url}. Status: {response.status}")
            pbar.close()
            
async def main(links_file, dest_path, div_class, max_concurrent=3, base_name=None):
    tasks = []
    async with aiohttp.ClientSession() as session:
        try:
            with open(links_file, 'r') as file:
                urls = [line.strip() for line in file if line.strip()]
                overall_pbar = tqdm(total=len(urls), desc="Total Progress", position=0)
                
                for url in urls:
                    tasks.append(process_url(session, url, dest_path, div_class, overall_pbar, base_name))
                    if len(tasks) >= max_concurrent:
                        await asyncio.gather(*tasks)
                        tasks = []
                
                if tasks:
                    await asyncio.gather(*tasks)
                
                overall_pbar.close()
            
            with open(links_file, 'w'):
                pass
            print(f"Cleaned up {links_file} after download.")
        
        except KeyboardInterrupt:
            print("\nDownload interrupted by user. Exiting...")
        except Exception as e:
            print(f"An error occurred during download: {e}")
        finally:
            if 'overall_pbar' in locals():
                overall_pbar.close()
            for task in tasks:
                if hasattr(task, 'pbar'):
                    task.pbar.close()

if __name__ == "__main__":
    links_file = "links.txt"
    download_directory = "downloads"
    div_class = "mx-auto max-w-[60rem]"
    max_concurrent_downloads = 3
    
    base_name = globals().get('base_name', 'unknown')

    os.makedirs(download_directory, exist_ok=True)
    
    try:
        asyncio.run(main(links_file, download_directory, div_class, max_concurrent_downloads, base_name))
    except KeyboardInterrupt:
        print("\nDownload interrupted by user. Exiting...")

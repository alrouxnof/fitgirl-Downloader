import requests
from bs4 import BeautifulSoup
import re
import os
import concurrent.futures
from tqdm import tqdm
import magic
import rarfile
import sys
import threading

# Global exit flag
exit_flag = threading.Event()

def signal_handler(sig, frame):
    """Handle SIGINT and set exit flag."""
    print("\nInterrupted by user. Exiting...")
    exit_flag.set()
    # Force exit after setting flag to ensure threads stop
    sys.exit(0)

import signal
signal.signal(signal.SIGINT, signal_handler)

def extract_download_url(script_content):
    """Extract the download URL from the script."""
    match = re.search(r'window\.open\("([^"]+)"', script_content)
    return match.group(1) if match else None

def get_filename_from_html(soup):
    """Extract filename from span element."""
    outer_div = soup.find('div', class_='mx-auto max-w-[60rem]')
    if outer_div and (inner_div := outer_div.find('div', class_='max-w-2xl mx-auto text-center')):
        if span := inner_div.find('span', class_='text-xl'):
            return span.text.strip()
    return None

def sanitize_filename(filename):
    """Sanitize filename and avoid duplicate .rar."""
    sanitized = ''.join(c for c in filename if c.isalnum() or c in '._- ')
    return sanitized[:-4] if sanitized.lower().endswith('.rar') else sanitized

def download_file(url, filename, output_dir="downloads", position=None, retries=3):
    """Download file with progress bar and retries."""
    if exit_flag.is_set():
        return None

    base_filename = sanitize_filename(filename)
    file_path = os.path.join(output_dir, f"{base_filename}.rar")
    os.makedirs(output_dir, exist_ok=True)

    for attempt in range(retries):
        if exit_flag.is_set():
            return None
        try:
            # Use a shorter timeout to allow interrupt checking
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            display_name = (base_filename[:17] + '...') if len(base_filename) > 20 else base_filename

            with open(file_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=display_name, 
                                                 bar_format='{desc}: {percentage:3.0f}%|█{bar:10}| {n_fmt}/{total_fmt}',
                                                 position=position, leave=False) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if exit_flag.is_set():
                        return None
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            return file_path
        except (requests.RequestException, TimeoutError) as e:
            print(f"Attempt {attempt + 1}/{retries} failed for {filename}: {e}")
            if attempt == retries - 1:
                print(f"Failed to download {filename} after {retries} attempts.")
                return None
            continue

def check_multi_volume_integrity(file_paths, base_name):
    """Check integrity of multi-volume RAR files."""
    if exit_flag.is_set():
        return False
    try:
        file_paths.sort()
        first_volume = next((f for f in file_paths if 'part1' in f.lower()), file_paths[0])
        with rarfile.RarFile(first_volume) as rf:
            if rf.testrar() is None:
                return True
            print(f"Corrupted multi-volume archive: {base_name}")
            return False
    except rarfile.BadRarFile as e:
        print(f"Integrity check failed for {base_name}: {e}")
        return False
    except Exception as e:
        print(f"Error verifying {base_name}: {e}")
        return False

def process_link(link, position, all_files):
    """Process a single link and download its file."""
    if exit_flag.is_set():
        return None, None

    try:
        response = requests.get(link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        filename = get_filename_from_html(soup) or "unknown_file"
        target_div = soup.find('div', class_='mx-auto max-w-[60rem]')
        if not target_div or not (script_tag := target_div.find('script')):
            print(f"Invalid page structure for {filename}")
            return filename, None

        download_url = extract_download_url(script_tag.string)
        if not download_url:
            print(f"No download URL found for {filename}")
            return filename, None

        file_path = download_file(download_url, filename, position=position)
        all_files[filename] = file_path
        return filename, file_path

    except requests.RequestException as e:
        print(f"Failed to fetch {link}: {e}")
        return filename, None

def process_links():
    """Read links from links.txt and download files."""
    try:
        with open('links.txt', 'r') as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: links.txt not found")
        return

    if not links:
        print("No links to process")
        return

    default_threads = 1
    try:
        max_threads = int(input(f"Simultaneous downloads (default {default_threads}): ") or default_threads)
        max_threads = max(1, min(max_threads, len(links)))
    except ValueError:
        print(f"Invalid input, using {default_threads}")
        max_threads = default_threads

    print(f"Downloading {len(links)} files with {max_threads} threads...")
    all_files = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        try:
            results = executor.map(lambda x: process_link(*x, all_files), [(link, i) for i, link in enumerate(links)])
            downloaded_files = {filename: file_path for filename, file_path in results if file_path and not exit_flag.is_set()}
        except KeyboardInterrupt:
            exit_flag.set()
            executor.shutdown(wait=False, cancel_futures=True)
            return

        if exit_flag.is_set():
            return

        if downloaded_files:
            base_name = min(downloaded_files.keys(), key=len)
            if any('part' in fname.lower() for fname in downloaded_files):
                file_paths = [fp for fp in downloaded_files.values() if fp]
                if check_multi_volume_integrity(file_paths, base_name):
                    print(f"{base_name} (multi-volume): Downloaded and verified")
                else:
                    print(f"{base_name} (multi-volume): Failed verification, removing files")
                    for fp in file_paths:
                        if os.path.exists(fp):
                            os.remove(fp)
            else:
                for filename, file_path in downloaded_files.items():
                    file_type = magic.from_file(file_path, mime=True)
                    if 'rar' not in file_type.lower() or check_multi_volume_integrity([file_path], filename):
                        print(f"{filename}: Downloaded and verified")
                    else:
                        print(f"{filename}: Failed verification, removed")
                        os.remove(file_path)

if __name__ == "__main__":
    process_links()
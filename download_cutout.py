
import requests
import sys
import os

url = "https://zenodo.org/records/15349674/files/europe-2013-sarah3-era5.nc"
dest_folder = "data/cutout/archive/v0.8"
dest_file = os.path.join(dest_folder, "europe-2013-sarah3-era5.nc")

if os.path.exists(dest_file):
    print(f"File already exists at {dest_file}")
    sys.exit(0)

# Ensure directory exists
os.makedirs(dest_folder, exist_ok=True)

print(f"Downloading {url} to {dest_file}...")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        total_length = r.headers.get('content-length')
        
        with open(dest_file, 'wb') as f:
            if total_length is None: # no content length header
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB")
                    sys.stdout.flush()
    print("\nDownload complete.")
except Exception as e:
    print(f"\nFailed to download: {e}")
    sys.exit(1)


import requests
import sys
import os

files_to_download = [
    {
        "url": "https://zenodo.org/records/15349674/files/europe-2013-sarah3-era5.nc",
        "name": "europe-2013-sarah3-era5.nc"
    },
    {
        "url": "https://zenodo.org/records/15349674/files/europe-2020-sarah3-era5.nc",
        "name": "europe-2020-sarah3-era5.nc"
    }
]

dest_folder = "data/cutout/archive/v0.8"
os.makedirs(dest_folder, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for item in files_to_download:
    url = item["url"]
    filename = item["name"]
    dest_file = os.path.join(dest_folder, filename)

    if os.path.exists(dest_file):
        print(f"File already exists: {dest_file}")
        continue

    print(f"Downloading {filename}...")
    
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            total_length = r.headers.get('content-length')
            
            with open(dest_file, 'wb') as f:
                if total_length is None:
                    f.write(r.content)
                else:
                    dl = 0
                    total = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB")
                        sys.stdout.flush()
        print(f"\nCompleted: {filename}")
    except Exception as e:
        print(f"\nFailed to download {filename}: {e}")

print("\nAll downloads processed.")

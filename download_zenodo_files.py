
import requests
import sys
import os
import time

files = [
    {
        "url": "https://zenodo.org/records/15349674/files/europe-2013-sarah3-era5.nc",
        "dest": "data/cutout/archive/v0.8/europe-2013-sarah3-era5.nc"
    },
    {
        "url": "https://zenodo.org/records/15879466/files/LUISA_basemap_020321_50m.tif",
        "dest": "data/luisa_land_cover/archive/2021-03-02/LUISA_basemap_020321_50m.tif"
    },
    {
        "url": "https://zenodo.org/records/16894236/files/shipdensity_global.zip",
        "dest": "data/ship_raster/archive/v5/shipdensity_global.zip"
    }
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def download_file(url, dest_file):
    if os.path.exists(dest_file):
        print(f"File already exists: {dest_file}")
        return

    folder = os.path.dirname(dest_file)
    os.makedirs(folder, exist_ok=True)
    
    print(f"Downloading {url} to {dest_file}...")
    
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, headers=headers) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                
                with open(dest_file, 'wb') as f:
                    if total_length is None:
                        f.write(r.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in r.iter_content(chunk_size=8192):
                            dl += len(data)
                            f.write(data)
                            done = int(50 * dl / total_length)
                            sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB")
                            sys.stdout.flush()
            print(f"\nSuccess: {dest_file}")
            return
        except Exception as e:
            print(f"\nError (attempt {attempt+1}): {e}")
            time.sleep(2)
            
    print(f"\nFailed to download {dest_file} after 3 attempts.")
    # Don't exit, try next file

for f in files:
    download_file(f["url"], f["dest"])

print("\nAll downloads attempted.")


import requests

url = "https://zenodo.org/records/15349674/files/europe-2020-sarah3-era5.nc"
try:
    r = requests.head(url)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(e)

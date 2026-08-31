import os
import requests
from pathlib import Path

def download_high_quality_test_faces():
    samples_dir = Path("./data/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    # Real public high-quality portrait faces (Unsplash free CC0 images)
    sample_urls = {
        "sample_sataboris.jpg": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=640&auto=format&fit=crop&q=80",
        "sample_elena.jpg": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=640&auto=format&fit=crop&q=80",
        "sample_alex.jpg": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=640&auto=format&fit=crop&q=80",
    }

    for filename, url in sample_urls.items():
        dest = samples_dir / filename
        try:
            print(f"Downloading real test face portrait: {filename}...")
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(res.content)
                print(f"Saved {dest} ({len(res.content)} bytes)")
            else:
                print(f"Failed to download {filename}: HTTP {res.status_code}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

if __name__ == "__main__":
    download_high_quality_test_faces()

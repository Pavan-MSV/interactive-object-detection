import urllib.request
import os

url = "https://huggingface.co/keremberke/yolov8m-hard-hat-detection/resolve/main/best.pt"
output_path = "yolov8m_hardhat.pt"

print(f"Downloading model from {url}...")
try:
    urllib.request.urlretrieve(url, output_path)
    print(f"Download complete: {output_path}")
except Exception as e:
    print(f"Download failed: {e}")

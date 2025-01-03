import os
import requests
import zipfile
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def get_chrome_version():
    try:
        # For Windows
        stream = os.popen('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version')
        output = stream.read()
        version = output.strip().split()[-1]
        return version
    except:
        return None

def download_chromedriver(version):
    # Get major version
    major_version = version.split('.')[0]
    
    # URL for ChromeDriver
    url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
    response = requests.get(url)
    driver_version = response.text.strip()
    
    # Download URL
    download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
    
    # Download the file
    response = requests.get(download_url)
    
    # Save to zip file
    with open("chromedriver.zip", "wb") as f:
        f.write(response.content)
    
    # Extract the zip file
    with zipfile.ZipFile("chromedriver.zip", "r") as zip_ref:
        zip_ref.extractall()
    
    # Clean up
    os.remove("chromedriver.zip")
    
    # Add to PATH
    driver_path = os.path.abspath("chromedriver.exe")
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.path.dirname(driver_path)
    
    return driver_path

def main():
    print("Getting Chrome version...")
    chrome_version = get_chrome_version()
    
    if not chrome_version:
        print("Could not detect Chrome version. Please make sure Google Chrome is installed.")
        sys.exit(1)
    
    print(f"Chrome version: {chrome_version}")
    print("Downloading matching ChromeDriver...")
    
    try:
        driver_path = download_chromedriver(chrome_version)
        print(f"ChromeDriver downloaded to: {driver_path}")
        print("Testing ChromeDriver...")
        
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        driver.quit()
        
        print("ChromeDriver setup successful!")
        
    except Exception as e:
        print(f"Error setting up ChromeDriver: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import random
from urllib.parse import urljoin
import requests
import os

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    
    # Add user agent to appear more like a regular browser
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    return webdriver.Chrome(options=chrome_options)

def random_delay(min_seconds=1, max_seconds=3):
    """Add a random delay between actions to mimic human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def scrape_content(driver, url):
    time.sleep(1)  # 等待頁面加載
    data = []
    try:
        driver.get(url)
        product_links = driver.find_elements(By.CSS_SELECTOR, "a#lnk_Insurance-ProductList_PageLink")
    
        for link in product_links:
            product_name = link.find_element(By.CSS_SELECTOR, "h2.c-prodcard-title").get_attribute("ori-text") or link.text.strip()
            product_url = link.get_attribute("href")
            data.append({"product_name": product_name, "product_url": product_url})
            print(f"product_name: {product_name}")
            print(f"product_url: {product_url}")
            print("-" * 40)
        df = pd.DataFrame(data)
        return df
    finally:
        pass

def scrape_pdf(driver, df, pdf_dir="./pdf_files"):
    for i, row in df.iterrows():
        product_name = row["product_name"]
        product_url = row["product_url"]
        print(f"Processing: {product_name}")
        
        try:
            driver.get(product_url)
            wait = WebDriverWait(driver, 2)  
        
            try:
                pdf_link_element = wait.until(EC.presence_of_element_located((By.XPATH, '//a[span[text()="商品條款"]]')))
                relative_pdf_url = pdf_link_element.get_attribute("href")
                pdf_url = urljoin(product_url, relative_pdf_url)
                print(f"PDF link: {pdf_url}")
                download_pdf(pdf_url, pdf_dir, product_name + "條款")
            except Exception as e:
                print(f"無法找到或下載商品條款 PDF: {e}")
        
            try:
                pdf_link_element_dm = wait.until(EC.presence_of_element_located((By.XPATH, '//a[span[text()="商品DM"]]')))
                relative_pdf_url_dm = pdf_link_element_dm.get_attribute("href")
                pdf_url_dm = urljoin(product_url, relative_pdf_url_dm)
                print(f"PDF link: {pdf_url_dm}")
                pdf_dir_dm = './pdf_dm_files'
                download_pdf(pdf_url_dm, pdf_dir_dm, product_name + "DM")
            except Exception as e:
                print(f"無法找到或下載商品DM PDF: {e}")
        
        except Exception as e:
            print(f"處理 {product_name} 時出錯: {e}")

def download_pdf(pdf_url, pdf_dir, product_name):
    """
    下載PDF文件並保存到指定目錄。

    :param pdf_url: PDF文件的URL
    :param pdf_dir: 存儲PDF文件的目標目錄
    :param product_name: 產品名稱，用於生成PDF文件名
    """
    response = requests.get(pdf_url)
    
    if response.status_code == 200:
        # 確保存儲目錄存在，如果不存在則創建它
        os.makedirs(pdf_dir, exist_ok=True)
        
        pdf_path = os.path.join(pdf_dir, f"{product_name}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        print(f"已下载: {pdf_path}")
    else:
        print(f"无法下载 PDF，状态码: {response.status_code}")
    
    print("-" * 40)

if __name__ == "__main__":
    start_time = time.time()
    url = "https://www.cathaylife.com.tw/cathaylife/products/life-caring"

    driver = setup_driver()
    web_df = scrape_content(driver, url)
    scrape_pdf(driver, web_df)
    driver.quit()
    end_time = time.time()
    print(f"耗費時間：{end_time - start_time} s.")

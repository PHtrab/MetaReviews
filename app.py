import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import os

def get_review_urls(driver, metacritic_url):
    driver.get(metacritic_url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "c-siteReview_externalLink"))
    )
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    review_links = soup.find_all('a', class_='c-siteReview_externalLink')
    return [urljoin(metacritic_url, link['href']) for link in review_links]

def scrape_reviews(driver, url, min_word_count=30):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "p"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        main_content = soup.find('article', class_='article') or soup.find('div', class_='content') or soup.find('div', class_='article-body')
        
        if not main_content:
            paragraphs = soup.find_all('p')
        else:
            paragraphs = main_content.find_all('p')
        
        seen_content = set()
        review_texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text.split()) >= min_word_count and text not in seen_content:
                review_texts.append(text)
                seen_content.add(text)
        
        return review_texts
    except Exception as e:
        st.error(f"Error scraping {url}: {str(e)}")
        return []

# Streamlit app
st.title("Metacritic Review Scraper")
metacritic_url = st.text_input("Enter the Metacritic URL:")

if metacritic_url:
    # Set up the Chrome driver
    service = Service(os.path.join(os.getcwd(), 'chromedriver'))  # Update this path if necessary
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    st.write(f"Fetching review URLs from {metacritic_url}")
    urls = get_review_urls(driver, metacritic_url)
    st.write(f"Found {len(urls)} review URLs")
    
    all_reviews = ""
    for i, url in enumerate(urls, 1):
        st.write(f"Processing URL {i} of {len(urls)}: {url}")
        website_name = urlparse(url).netloc.replace('www.', '')
        game_reviews = scrape_reviews(driver, url)
        
        if game_reviews:
            all_reviews += f"Review from {website_name}:\n\n"
            for review in game_reviews:
                all_reviews += f"{review}\n\n"
            all_reviews += "\n" + "="*50 + "\n\n"
        else:
            st.write(f"No content scraped from {website_name}")
        
        time.sleep(2)
    
    # Save to file
    with open('scraped_reviews.txt', 'w', encoding='utf-8') as f:
        f.write(all_reviews)
    
    st.success("All reviews have been saved to 'scraped_reviews.txt'")
    driver.quit()

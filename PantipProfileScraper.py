import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from tqdm import tqdm 
import re

class PantipProfileScraper:
    def __init__(self):
        self.user_profile_information = {}
        
    def scrape_pantip_profile(self, user_id):
        """ Scrape Pantip user profile information

        Args:
            user_id (str): Pantip user id

        Returns:
            dict : dict: User profile information, includes user_name, user_avatar, user_desc, user_bio, follower, following, and profile_feed
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        url = f'http://www.pantip.com/profile/{user_id}#topics'
        driver.get(url)
        time.sleep(1)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        user_profile_information = {}
        
        # Extract user profile information
        user_profile_information = {
            'user_name': (soup.find('div', class_='b-block-title').find('h3').get_text(strip=True) 
                        if soup.find('div', class_='b-block-title') else None),
            'user_avatar': (soup.find('div', class_='big_avatar').find('img')['src'] 
                            if soup.find('div', class_='b-block-content') 
                            and soup.find('div', class_='big_avatar') else None),
            'user_desc': (soup.find('div', class_='profile-desc').get_text(strip=True) 
                        if soup.find('div', class_='profile-desc') else None),
            'user_bio': [span.get_text(strip=True) for span in soup.find('div', class_='profile-bio small-txt-fixed').find_all('span')] 
                        if soup.find('div', class_='profile-bio small-txt-fixed') else [],
            'follower': re.search(r'(กำลังติดตาม)(\d+)', soup.find('div', class_='profile-stat').get_text(strip=True)).group(2) 
                        if soup.find('div', class_='profile-stat') 
                        and re.search(r'(กำลังติดตาม)(\d+)', soup.find('div', class_='profile-stat').get_text(strip=True)) else '0',
            'following': re.search(r'(ติดตาม)(\d+)', soup.find('div', class_='profile-stat').get_text(strip=True)).group(2) 
                        if soup.find('div', class_='profile-stat') 
                        and re.search(r'(ติดตาม)(\d+)', soup.find('div', class_='profile-stat').get_text(strip=True)) else '0'
        }
        
        def extract_topic_index(url):
            match = re.search(r'/topic/(\d+)', url)
            return match.group(1) if match else None
        
        profile_extracted_data = {}
        
        # Extract User Profile Feed (Posts)
        wrapper = soup.find('div', class_='post-list-wrapper')
    
        if wrapper:
            post_items = wrapper.find_all('div', class_='post-item')
            for post in tqdm(post_items, desc="Processing posts"):
                title_div = post.find('div', class_='post-item-title')
                if title_div:
                    title_element = title_div.find('a')
                    title = title_element.get_text(strip=True) if title_element else None
                    post_url = title_element['href'] if title_element else None
                    title_id = extract_topic_index(post_url) if post_url else None
                    
                    owner_tag = post.find('div', class_='post-item-by')
                    owner_text = owner_tag.find('span', class_='by-name').get_text(strip=True) if owner_tag else None
                    timestamp_text = owner_tag.find('abbr', class_='timeago')['data-utime'] if owner_tag and owner_tag.find('span', class_='timestamp') else None
                    
                    comment_status = post.find('div', class_='post-item-status-i')
                    comment_text = comment_status.get_text(strip=True) if comment_status and 'ความคิดเห็น' in comment_status.get('title', '') else '0'
                    
                    tags_data = post.find('div', class_='post-item-footer')
                    tag_list = tags_data.find('div', class_='post-item-taglist') if tags_data else None
                    tag_element = tag_list.find('a', class_='tag-title') if tag_list else None
                    tag_title = tag_element.get('data-tag') if tag_element else None
                    tag_title_2 = tag_element.get('href') if tag_element else None
                    
                    if title_id:
                        profile_extracted_data[title_id] = {
                            'title': title,
                            'url': post_url,
                            'owner': owner_text,
                            'timestamp': timestamp_text,
                            'comment_count': comment_text,
                            'tag': tag_title,
                            'tag_url': tag_title_2
                        }

        # Add the profile feed to the user profile information
        user_profile_information['profile_feed'] = profile_extracted_data
            
        self.user_profile_information = user_profile_information
        
        return user_profile_information
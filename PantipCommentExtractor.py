import requests
import time
import json
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from json import JSONDecodeError
import concurrent.futures

class PantipCommentExtractor:
    def __init__(self, keyword_data):
        self.keyword_id_dict = self.extract_keyword_id(keyword_data)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        self.base_url = "http://pantip.com/forum/topic/render_comments"

    def extract_keyword_id(self, combine_dict):
        """ Extracit keywords and ids from dictionary

        Args:
            combine_dict (dict): a dictionary containing keyword data, key = keyword, val= list of ids

        Returns:
            keyword_id_dict: a dictionary containing keyword IDs and their corresponding search keywords
        """
        keyword_id_dict = {}
        for keyword_index, keyword_data in combine_dict.items():
            #Get the search Keyword
            search_keyword = keyword_data.get('search_keyword', '')
            keyword_ids = []
            #Check if keyword_data is a dictionary and contains pages, and data
            if isinstance(keyword_data, dict):
                for page_key, page_value in keyword_data.items():
                    # Only process the pages that contain data prevent confusion, this will skip pages that are containing 'error' or no data
                    if isinstance(page_value, dict) and 'data' in page_value:
                        data_list = page_value['data']
                        #if 'id' is in the item, extract the id from 'data' list
                        page_ids = [item['id'] for item in data_list if isinstance(item, dict) and 'id' in item]
                        keyword_ids.extend(page_ids)
                if search_keyword:
                    keyword_id_dict[search_keyword] = keyword_ids
        
        return keyword_id_dict

    def fetch_comments(self, key, comment_ids):
        """ Fetches comments from topic ids(Topic id)

        Args:
            key (keyword): a keyword as a dictionary key
            comment_ids (list): a value containing a list of topic ids

        Returns:
            key, all_comment: a dictionary containing comments for each topic id
        """
        all_comments = {}
        for comment_id in comment_ids:
            params = {'tid': comment_id, "type": "3"}
            try:
                r = self.session.get(self.base_url, params=params, headers=self.headers)
                r.raise_for_status()
                if r.status_code == 200:
                    try:
                        comment_data = r.json()
                        all_comments[comment_id] = comment_data
                    except requests.JSONDecodeError as json_error:
                        print(f"JSON decoding error for {key}: {json_error}")
                else:
                    print(f"Unexpected status code {r.status_code} for {key}")
            except requests.RequestException as e:
                print(f"Request error for {key}: {e}")
        return key, all_comments

    def get_comment_ids(self, max_workers):
        """ Fetches comments for each keyword id

        Args:
            max_workers (params): a number of workers to use for concurrent requests

        Returns:
            comment_dict: a dictionary containning keyword search, and comments for each keyword id by pages
        """
        comment_dict = {}
        batch_size = 600

        #ThreadPool multiprocessing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for key, value in self.keyword_id_dict.items():
                if isinstance(value, list):
                    batches = [value[i:i+batch_size] for i in range(0, len(value), batch_size)]
                    for batch in batches:
                        future = executor.submit(self.fetch_comments, key, batch)
                        futures.append(future)

            #Print to check the number of futures(num of workers that are running)
            print(f"Number of futures: {len(futures)}")
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
                key, result = future.result()
                if result:
                    if key not in comment_dict:
                        comment_dict[key] = {}
                    comment_dict[key].update(result)

        return comment_dict
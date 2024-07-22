
import requests
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class PantipSearchQuery:
    def __init__(self, keyword, page_number, num_workers):
        """ Pantip Search Query by keyword

        Args:
            keyword (str): a keyword to search
            page_number (int): number of pages to search
            num_workers (int): number of workers to use
            
        Returns:
            dict: a dictionary of search results, key = page number, value = search results
        """
        self.keyword = keyword
        self.page_number = page_number
        self.num_workers = num_workers
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://pantip.com',
            'priority': 'u=1, i',
            'ptauthorize': 'Basic dGVzdGVyOnRlc3Rlcg==',
            'referer': 'https://pantip.com/search?q=cat',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

    def fetch_page(self, i):
        """ Fetch a page by page number

        Args:
            i (int): a page number to fetch

        Returns:
            tuple: (page number, response json data or None)
        """
        json_data = {
            'keyword': self.keyword,
            'page': i,
            'type': 'all',
            'show_btn_search': 'true',
            'room_search': None,
        }

        response = requests.post(
            'https://pantip.com/api/search-service/search/getresult',
            headers=self.headers,
            json=json_data,
        )

        if response.status_code == 200:
            return i, response.json()
        else:
            return i, None

    def fetch_all_pages(self):
        results_dict = {}
        total_results = None  # Initialize variable to store total number of results

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(self.fetch_page, i): i for i in range(self.page_number + 1)}

            for future in tqdm(as_completed(futures), total=self.page_number + 1):
                try:
                    i, data = future.result()
                    if data:
                        print(f"Page {i} processed successfully.")
                        results_dict[i] = data

                        # Extract 'total' from the first page of results
                        if i == 1 and 'total' in data:  # Assuming page 1 is where 'total' is present
                            total_results = data['total']
                            print(f"Total results found: {total_results}")

                        if 'data' in data and not data['data']:
                            print(f"Page {i} has no data. Stopping the loop.")
                            break
                    else:
                        print(f"Failed to process page {i}.")

                except Exception as e:
                    print(f"Failed to process page {i}. Error: {e}")

                # Add delay to avoid server rate limits
                time.sleep(0.1)

        # Sort the results by page number
        sorted_results = {k: results_dict[k] for k in sorted([k for k in results_dict.keys() if isinstance(k, int)])}
        
        # Add keyword and total results and update the sorted results(that ordered by page number)
        final_results = {
            'search_keyword': self.keyword,
            'total_results': total_results,
        }
        final_results.update(sorted_results)

        return final_results
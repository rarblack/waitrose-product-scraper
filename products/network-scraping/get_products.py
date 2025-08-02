from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from queue import Queue
import threading
import pandas as pd
from pathlib import Path
import pickle, json, time
from enum import Enum
from urllib3.exceptions import ProtocolError
import logging
import datetime


logger = logging.getLogger(__name__)

type Page = dict[str, str | list]

class PageAssets(Enum):
    CATEGORY = 'CATEGORY'
    PRODUCT =  'PRODUCT'

BASE_URL = "https://www.waitrose.com"
SEARCH_PATH = "ecom/shop/browse"

INITIAL_CATEGORIES: dict[str, str] = {
    # 'groceries/summer': 'SUMMER',
    # 'groceries/fresh_and_chilled': 'Fresh & Chilled',
    # 'groceries/frozen': 'Frozen',
    'groceries/beer_wine_and_spirits':'Beer, Wine & Spirits',
    # 'groceries/bakery': 'Bakery',
    # 'offers': 'Offers'
}

BASE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper"

CATEGORIES_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/categories/database.csv"
CATEGORIES:pd.DataFrame = None

CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/cache.pkl"
CACHE: dict[str, int | None] = None

TASK_CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/task_cache.pkl"
TASK_CACHE: list[str] = None

THRESHOLD = 1

TASK_QUEUE = Queue()
DRIVER = webdriver.Chrome(seleniumwire_options={'disable_encoding': True})

def write_cache(cache: dict = CACHE, path: str = CACHE_PATH):
    with open(path, 'wb') as file:
        pickle.dump(cache, file)

def read_cache(path: str = CACHE_PATH) -> dict:
    with open(path, 'rb') as file:
        try:
            cache = pickle.load(file)
        except:
            cache = {}
    
    return cache

def write_pickle(data: dict, path: str):
    with open(path, 'wb') as file:
        pickle.dump(data, file)

def read_pickle(path: str) -> dict:
    data = {}
    with open(path, 'rb') as file:
        try:
            data = pickle.load(file)
        except:
            pass
    
    return data

def write_json(data: dict | list, path: str) -> None:
    with open(path, 'w') as file:
        json.dump(data, file)
    
def read_json(path: str) -> dict | list:
    with open(path, 'r') as file:
        data: dict | list = json.load(file)
    return data

def reject_cookies():
    try:
        DRIVER.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']").send_keys(Keys.RETURN)
        time.sleep(1)

    except NoSuchElementException as error:
        print(error)
    except Exception as error:
        raise error

def clean_url(url: str) -> str:
    return url.split("?")[0]

def clean_data(data: dict) -> list[dict]:
    items = []
    try:
        data = data['data']
        data = data['getProductListPage']
        data = data['productGridData']
        data = data['componentsAndProducts']
        items.extend(data)
    except KeyError as error:
        print(error)

    return items

def crawl(url: str) -> tuple[str, list[dict]]:
    def sort_a2z():
        try:
            DRIVER.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[2]/div[1]/button").click()
            DRIVER.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
            time.sleep(1)
        except NoSuchElementException:
            DRIVER.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[1]/div[1]/button").click()
            DRIVER.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
            time.sleep(1)

    def load_data() -> int:
        cnt: int = 0
        while (True):
            try:
                load_more_button = DRIVER.find_element(By.XPATH, "//button[@aria-label='Load more']").click()
                # load_more_button.send_keys(Keys.RETURN)

                cnt += 1

                print(f'    Loading {cnt}', end='\r')

                time.sleep(.5)

            except NoSuchElementException as error:
                # log error as info
                print(f'    Loading {cnt}')
                return cnt
            
    def crawl_category() -> list[dict[str, str]]: 
        category: str = None
        for request in DRIVER.requests:
            if request.response and request.method == 'POST':
                if request.url.endswith("live?clientType=WEB_APP&tag=browse"):
                    try:
                        body = json.loads(request.body.decode('utf-8'))
                        category = body['variables']['category']
                        break

                    except Exception as error:
                        print(error)

        return category
    
    def crawl_data() -> list[dict[str, str]]:         
        data = []
        for request in DRIVER.requests:
            if request.response and request.method == 'POST':
                if request.url.endswith("live?clientType=WEB_APP&tag=browse"):
                    try:
                        body = json.loads(request.response.body.decode('utf-8'))
                        items = clean_data(body)
                        data.extend(items)

                    except Exception as error:
                        print(error)

        return data

    def crawl_tasks() -> list[dict[str, str]]:
        elements = DRIVER.find_elements(By.XPATH, './/ul[@data-testid="category-list-links"]/li')

        categories = []
        for element in elements:
            try:
                href = element.find_element(By.XPATH, './/a').get_attribute("href")
                text = element.find_element(By.XPATH, './/a/span').text

                url = clean_url(href)

                category = url.split('/')[-1]
                badge = text

                categories.append({"url": url, "path": category, "badge": badge})

            except NoSuchElementException:
                pass # add logger
            except Exception as error:
                print(error)

        return categories

    DRIVER.get(url)

    sort_a2z()

    data_bulk_count: int = load_data()
    CACHE[url] = data_bulk_count
    
    category = crawl_category()
    print(category)

    data = crawl_data()

    tasks = crawl_tasks()
    for task in tasks:
        if not CACHE.get(task['url'], False):
            TASK_QUEUE.put(task['url'])

    return {
        "url": url,
        "category": category, 
        "tasks": tasks, 
        "data": data
    }

def worker() -> None:
    results = []
    while not TASK_QUEUE.empty():
        url_raw = TASK_QUEUE.get()

        url = clean_url(url_raw)
        logger.info(f"TASK: {url}")
        print(f"TASK: {url}")

        try:
            result = crawl(url)
            results.append(result)

            if len(results) >= THRESHOLD:
                timestamp = time.time()

                write_json(results, path=f'{BASE_PATH}/products/network-scraping/data/{timestamp}.json')
                
                results.clear()

                write_cache()
            
        except Exception as error: # TODO: separate exception to handle errors better
            logger.error(error)
            print(CACHE)
            print(url)

            CACHE[url] = None
            TASK_QUEUE.put(url)

            while not TASK_QUEUE.empty():
                TASK_CACHE.append(TASK_QUEUE.get(False))

            write_cache(CACHE, CACHE_PATH)
            write_pickle(TASK_CACHE, TASK_CACHE_PATH)
        
        TASK_QUEUE.task_done()

def load_cache() -> None:
    if Path(CACHE_PATH).exists(): # cache file
        logger.info("Cache read")
        return read_pickle(CACHE_PATH)
    
    return {}

def load_tasks() -> None:
    if Path(TASK_CACHE_PATH).exists(): # tasks file
        logger.info("Task cache read")
        return read_pickle(TASK_CACHE_PATH)

    return []

def main() -> None:
    today = datetime.date.today()
    logging.basicConfig(filename=f'{BASE_PATH}/products/network-scraping/logs/{today}.log', level=logging.INFO)

    CACHE = load_cache()
    TASK_CACHE = load_tasks()

    if TASK_CACHE:
        logging.info(f'Starting from cache')
        print(f'Starting from cache')

        for url in TASK_CACHE:
            if not CACHE.get(url, False):
                TASK_QUEUE.put(url)
    else:
        logging.info(f'Starting from scratch')
        print(f'Starting from scratch')
        for category, badge in INITIAL_CATEGORIES.items():
            url = f'{BASE_URL}/{SEARCH_PATH}/{category}'

            if not CACHE.get(url, False):
                TASK_QUEUE.put(url)

    if not TASK_QUEUE.empty():
        DRIVER.get(f'{BASE_URL}')
        reject_cookies()

        threading.Thread(target=worker, daemon=True).start()
        TASK_QUEUE.join()


if __name__ == "__main__":
    try:
        main()
        DRIVER.quit()

    except Exception as error:
        DRIVER.quit()    

    



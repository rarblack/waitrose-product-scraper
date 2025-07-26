from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from queue import Queue
import threading
import pandas as pd
from pathlib import Path
import pickle, json, time
from enum import Enum

type Page = dict[str, str | list]

class PageAssets(Enum):
    CATEGORY = 'CATEGORY'
    PRODUCT =  'PRODUCT'

BASE_URL = "https://www.waitrose.com"
SEARCH_PATH = "ecom/shop/browse"

INITIAL_CATEGORIES: dict[str, str] = {
    'groceries/summer': 'SUMMER',
    'groceries/fresh_and_chilled': 'Fresh & Chilled',
    'groceries/frozen': 'Frozen',
    'groceries/beer_wine_and_spirits':'Beer, Wine & Spirits',
    'groceries/bakery': 'Bakery',
    'offers': 'Offers'
}

BASE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper"

CATEGORIES_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/categories/database.csv"
CATEGORIES:pd.DataFrame = None

CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/cache.pkl"
CACHE: dict[str, bool] = {}

TASK_CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/task_cache.pkl"
TASK_CACHE: list[str] = []

THRESHOLD = 10

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

def sort_a2z():
    try:
        DRIVER.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[2]/div[1]/button").click()
        DRIVER.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
        time.sleep(1)
    except NoSuchElementException:
        DRIVER.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[1]/div[1]/button").click()
        DRIVER.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
        time.sleep(1)
    
def load_all_data():
    while (True):
        try:
            load_more_button = DRIVER.find_element(By.XPATH, "//button[@aria-label='Load more']")
            load_more_button.send_keys(Keys.RETURN)
            time.sleep(.5)

        except Exception as e:
            break

    time.sleep(.5)

def crawl() -> tuple[str, list[dict]]:
    def crawl_category() -> list[dict[str, str]]: 
        category = None
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
        load_all_data()
        
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

    def crawl_tasks():
        elements = DRIVER.find_elements(By.XPATH, './/ul[@data-testid="category-list-links"]/li')

        categories = []
        for element in elements:
            try:
                href = element.find_element(By.XPATH, './/a').get_attribute("href")
                text = element.find_element(By.XPATH, './/a/span').text

                url = clean_url(href)

                category = url.split('/')[-1]
                badge = text

                categories.append({"url": url, "category": category, "badge": badge})

            except NoSuchElementException:
                pass # add logger
            except Exception as e:
                print(e)

        return categories

    category = crawl_category()
    data = crawl_data()

    tasks = crawl_tasks()
    for task in tasks:
        TASK_QUEUE.put(task['url'])

    return {
        "category": category, 
        "tasks": tasks, 
        "data": data
    }

def worker() -> None:
    results = []
    while not TASK_QUEUE.empty():
        url_raw = TASK_QUEUE.get()

        url = clean_url(url_raw)

        try:
            DRIVER.get(url)

            sort_a2z()
            
            result = crawl()
            result['url'] = url

            # print(result)
            # write_json(result, path=f'{BASE_PATH}/products/network-scraping/data/{time.time()}.json')
            # break

            results.append(result)

            CACHE[url] = True
            if len(results) >= THRESHOLD:
                timestamp = time.time()
                write_json(results, path=f'{BASE_PATH}/products/network-scraping/data/{timestamp}.json')
                
                results.clear()

                write_cache()

        except NoSuchElementException as error:
            print(error)
            print(url)

        except Exception as error: # TODO: separate exception to handle errors better
            print(error)
            print(url)
            CACHE[url] = False
            TASK_QUEUE.put(url)

            while not TASK_QUEUE.empty():
                TASK_CACHE.append(TASK_QUEUE.get(False))
            write_pickle(TASK_CACHE, TASK_CACHE_PATH)
            write_cache(CACHE, CACHE_PATH)
        
        TASK_QUEUE.task_done()

if __name__ == "__main__":
    # cache file
    if Path(CACHE_PATH).exists():
        CACHE = read_pickle(CACHE_PATH)

    # tasks file
    if Path(TASK_CACHE_PATH).exists():
        TASK_CACHE = read_pickle(TASK_CACHE_PATH)

    if TASK_CACHE:
        for url in TASK_CACHE:
            TASK_QUEUE.put(url)
    else:
        for category, badge in INITIAL_CATEGORIES.items():
            url = f'{BASE_URL}/{SEARCH_PATH}/{category}'

            if not CACHE.get(url, False):
                TASK_QUEUE.put(url)

    # TASK_QUEUE.put("https://www.waitrose.com/ecom/shop/browse/offers")

    if not TASK_QUEUE.empty():
        DRIVER.get(f'{BASE_URL}')
        reject_cookies()

        threading.Thread(target=worker, daemon=True).start()
        TASK_QUEUE.join()

    DRIVER.quit()

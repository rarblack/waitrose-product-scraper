from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from queue import Queue
import threading
import pandas as pd
from pathlib import Path
import pickle, json, time


BASE_URL = "https://www.waitrose.com"
SEARCH_PATH = "ecom/shop/browse/groceries"

INITIAL_CATEGORIES: dict[str, str] = {
    'summer': 'SUMMER',
    'fresh_and_chilled': 'Fresh & Chilled',
    'frozen': 'Frozen',
    'beer_wine_and_spirits':'Beer, Wine & Spirits',
    'bakery': 'Bakery',
    'offers': 'Offers'
}

BASE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper"

CATEGORIES_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/categories/database.csv"
CATEGORIES:pd.DataFrame = None

CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/cache.pkl"
CACHE: dict[str, bool] = None

COUNTER, THRESHOLD = 0, 100

DATABASE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/database.csv"
DATABASE_COLUMNS = [
    'url',
    'badge',
    'name',
    'size',
    'price',
    'rating',
    'offer_description',
    'was_price_description', 
]
DATABASE: pd.DataFrame = None
DATA = []

TASKS = Queue()
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
    
def worker() -> None:
    results = []
    while not TASKS.empty():
        url = TASKS.get()

        try:
            data: list[dict[str, str]] | dict[str, str] = crawl(url)
            CACHE[url] = True

            if COUNTER >= THRESHOLD:
                if results:
                    write_json(data, path=f'{BASE_PATH}/products/network-scraping/database_{time.time()}.json')

                    results.clear()

                write_cache()
                COUNTER = 0
            else:
                COUNTER += 1

        except Exception as error: # TODO: separate exception to handle errors better
            CACHE[url] = False
            TASKS.put(url)
        
        TASKS.task_done()

def load_all_data():
    while (True):
        try:
            load_more_button = DRIVER.find_element(By.XPATH, "//button[@aria-label='Load more']")
            load_more_button.send_keys(Keys.RETURN)
            time.sleep(.5)

        except Exception as e:
            break

    time.sleep(.5)

def crawl(url: str) -> list[dict[str, str]]:
    DRIVER.get(f'{url}')

    load_all_data()
    
    data = []
    for request in DRIVER.requests:
        if request.response and request.method == 'POST':
            if request.url.endswith("live?clientType=WEB_APP&tag=browse"):
                try:
                    body = json.loads(request.response.body.decode('utf-8'))
                    data.append(body)
                except Exception as error:
                    print(error)

    return data


if __name__ == "__main__":
    CATEGORIES = pd.read_csv(CATEGORIES_PATH)

    if CATEGORIES.empty:
        raise Exception("CATEGORIES is empty")
    

    if Path(DATABASE_PATH).exists():
        DATABASE = pd.read_csv(DATABASE_PATH)
    else: 
        DATABASE = pd.DataFrame(columns=DATABASE_COLUMNS)

    # cache file
    if Path(CACHE_PATH).exists():
        CACHE = read_cache(CACHE_PATH)
    else: 
        CACHE = {}

    # create tasks
    for url in CATEGORIES.url:
        if not CACHE.get(url, False):
            TASKS.put(url)


    if not TASKS.empty():
        DRIVER.get(f'{BASE_URL}')
        reject_cookies()

        threading.Thread(target=worker, daemon=True).start()
        TASKS.join()

    DRIVER.quit()

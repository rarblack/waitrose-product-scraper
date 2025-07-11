from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from queue import Queue
import threading
import pandas as pd
from pathlib import Path
import time
import pickle


BASE_URL = "https://www.waitrose.com"

CATEGORIES_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/categories/database.csv"
CATEGORIES:pd.DataFrame = None

CACHE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/cache.pkl"
CACHE: dict[str, bool] = None

THRESHOLD = 1000

DATABASE_PATH = "/Users/rarblack/.dev/organizations/rarblack/waitrose-product-scraper/products/database.pkl"
DATABASE_COLUMNS = [
    'url',
    'badge',
    'name',
    'price',
    'rating',
    'offer_description',
    'was_price_description', 
]
DATABASE: pd.DataFrame = None

TASKS = Queue()
DRIVER = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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

def worker() -> None:

    # reject cookies
    DRIVER.get(f'{BASE_URL}')
    DRIVER.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']").send_keys(Keys.RETURN)

    while not TASKS.empty():
        url = TASKS.get()

        try:
            data: list[dict[str, str]] = crawl(url)
            DATABASE.append(data, ignore_index=True)

            CACHE[url] = True
        except Exception as error:
            CACHE[url] = False
            print(error)

            # re-add the url
            TASKS.put(url)

        TASKS.task_done()

        if DATABASE.size() >= THRESHOLD:
            DATABASE.to_pickle(DATABASE_PATH)
    

def crawl(url: str) -> list[dict[str, str]]:
    DRIVER.get(f'{url}')

    while (True):
        try:
            load_more_button = DRIVER.find_element(By.XPATH, "//button[@aria-label='Load more']")
            load_more_button.send_keys(Keys.RETURN)
            time.sleep(.5)

        except Exception as e:
            break

    time.sleep(.5)
    
    results = DRIVER.find_elements(By.XPATH, './/article[@data-testid="product-pod"]')

    data = []
    for product in results:
        try:
            badge = product.find_element(By.XPATH, './/span[@data-testid="product-badge"]/span').text
        except NoSuchElementException:
            badge = ""
        except Exception as e:
            print(e)

        try:
            name = product.find_element(By.XPATH, './/h2[@data-testid="product-pod-name"]/span').text
        except NoSuchElementException:
            name = ""
        except Exception as e:
            print(e)

        try:
            price = product.find_element(By.XPATH, './/span[@data-test="product-pod-price"]/span').text
        except NoSuchElementException:
            price = ""
        except Exception as e:
            print(e)

        try:
            rating = product.find_element(By.XPATH, './/a[@aria-label="Product Rating"]/div/span').text
        except NoSuchElementException:
            rating = ""
        except Exception as e:
            print(e)

        try:
            offer_description = product.find_element(By.XPATH, './/span[@data-testid="offer-description"]/span').text
        except NoSuchElementException:
            offer_description = ""
        except Exception as e:
            print(e)

        try:
            was_price_description = product.find_element(By.XPATH, './/em[@data-testid="was-price-description"]').text
        except NoSuchElementException:
            was_price_description = price
        except Exception as e:
            print(e)

        data.append(
            {
                "url": url,
                "badge": badge,
                'name': name, 
                'price': price, 
                "rating": rating,
                'offer_description': offer_description, 
                'was_price_description': was_price_description, 
            }
        )

    return data



if __name__ == "__main__":
    CATEGORIES = pd.read_csv(CATEGORIES_PATH)

    if CATEGORIES.empty:
        raise Exception("CATEGORIES is empty")
    

    if Path(DATABASE_PATH).exist():
        DATABASE = pd.read_pickle(DATABASE_PATH)
    else: 
        DATABASE = pd.DataFrame(columns=DATABASE_COLUMNS)

    # cache file
    if Path(CACHE_PATH).exist():
        CACHE = read_cache(CACHE_PATH)
    else: 
        CACHE = {}

    # create tasks
    for url in CATEGORIES.url:
        if not CACHE.get(url, False):
            TASKS.put(url)

    if not TASKS.empty():
        threading.Thread(target=worker, daemon=True).start()

        TASKS.join()

    DRIVER.quit()

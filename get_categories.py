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
import csv

DATABASE = 'database.csv'
BASE_URL = "https://www.waitrose.com"
BASE_CATEGORIES = [
    {
        "url": "/ecom/shop/browse/groceries/fresh_and_chilled",
        "badge": "fresh_and_chilled",
    },
    {
        "url": "/ecom/shop/browse/groceries/bakery",
        "badge": "bakery",
    },
    {
        "url": "/ecom/shop/browse/groceries/beer_wine_and_spirits",
        "badge": "beer_wine_and_spirits",
    },
    {
        "url": "/ecom/shop/browse/groceries/frozen",
        "badge": "frozen",
    },
    {
        "url": "/ecom/shop/browse/groceries/summer",
        "badge": "summer",
    },
    {
        "url": "/ecom/shop/browse/offers",
        "badge": "offers",
    }
]

df = pd.DataFrame(columns=['url', 'badge'])

tasks = Queue()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# url:badge -> string:int
cache = {f'{BASE_URL}{category['url']}': True for category in BASE_CATEGORIES}
results = []

def worker():
    # reject cookies
    driver.get(f'{BASE_URL}')
    reject_all_button = driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']")
    reject_all_button.send_keys(Keys.RETURN)

    while not tasks.empty():
        size = tasks.qsize()

        while size > 0:
            url = tasks.get()

            crawl(url)
            
            tasks.task_done()

            size -= 1

        if results:
            df = pd.DataFrame(results, columns=['url', 'badge'])
            df.to_csv(DATABASE, mode='a', index=False, header=False)
            
            results.clear()

def crawl(url):
    driver.get(f'{url}')
    
    elements = driver.find_elements(By.XPATH, './/ul[@data-testid="category-list-links"]/li')

    categories = []
    for element in elements:
        try:
            url = element.find_element(By.XPATH, './/a').get_attribute("href")
            badge = element.find_element(By.XPATH, './/a/span').text

            if not cache.get(url, False):
                tasks.put(url)
                cache[url] = True

                results.append(
                    {
                        "url": url,
                        "badge": badge,
                    }
                )

        except NoSuchElementException:
            pass
        except Exception as e:
            print(e)

    return categories


if __name__ == "__main__":
    file = Path('database.csv')
    if not file.exists():
        df.to_csv(DATABASE)

    # restore cache
    reader = csv.reader(open(DATABASE, 'r'))
    next(reader, None) # skip header
    
    for row in reader:
        key = row[0]
        if not cache.get(key):
            cache[key] = True

    print("Cache is loaded")

    for category in BASE_CATEGORIES:
        url = f'{BASE_URL}{category["url"]}'
        tasks.put(url)

    print("Tasks are loaded")

    threading.Thread(target=worker, daemon=True).start()
    tasks.join()
    driver.quit()

from cmath import sqrt
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
import time

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
        url = tasks.get()

        crawl(url)
        
        tasks.task_done()

def crawl(url):
    driver.get(f'{url}')

    while (True):
        try:
            load_more_button = driver.find_element(By.XPATH, "//button[@aria-label='Load more']")
            load_more_button.send_keys(Keys.RETURN)
            time.sleep(2)

        except Exception as e:
            break

    time.sleep(.5)
    
    results = driver.find_elements(By.XPATH, './/article[@data-testid="product-pod"]')

    products = []
    for product in results:
        try:
            product_badge = product.find_element(By.XPATH, './/span[@data-testid="product-badge"]/span').text
        except NoSuchElementException:
            product_badge = ""
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
            product_rating = product.find_element(By.XPATH, './/a[@aria-label="Product Rating"]/div/span').text
        except NoSuchElementException:
            product_rating = ""
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

        products.append(
            {
                "product_badge": product_badge,
                'name': name, 
                'price': price, 
                "product_rating": product_rating,
                'offer_description': offer_description, 
                'was_price_description': was_price_description, 
            }
        )

    print(products)

    return products

if __name__ == "__main__":
    file = Path('database.csv')
    if not file.exists():
        exit(0)

    # restore cache
    reader = csv.reader(open(DATABASE, 'r'))
    next(reader, None) # skip header
    
    # for row in reader:
    #     url = row[0]
    #     tasks.put(url)

    tasks.put("https://www.waitrose.com/ecom/shop/browse/offers/fresh_and_chilled_offers/food_to_go_offers?categoryId=301147")

    threading.Thread(target=worker, daemon=True).start()
    tasks.join()
    driver.quit()
    
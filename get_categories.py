from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from queue import Queue
import threading
import pandas as pd


BASE_URL = "https://www.waitrose.com"
BASE_CATEGORIES = [
    {
        "badge": "fresh_and_chilled",
        "url": "/ecom/shop/browse/groceries/fresh_and_chilled",
    },
    {
        "badge": "bakery",
        "url": "/ecom/shop/browse/groceries/bakery",
    },
    {
        "badge": "beer_wine_and_spirits",
        "url": "/ecom/shop/browse/groceries/beer_wine_and_spirits",
    },
    {
        "badge": "frozen",
        "url": "/ecom/shop/browse/groceries/frozen",
    },
    {
        "badge": "summer",
        "url": "/ecom/shop/browse/groceries/summer",
    },
    {
        "badge": "offers",
        "url": "/ecom/shop/browse/offers",
    }
]

tasks = Queue()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

checkup_table = {f'{BASE_URL}{category.url}': True for category in BASE_CATEGORIES}
results = {*BASE_CATEGORIES}

def worker():
    # reject cookies
    driver.get(f'{BASE_URL}')
    reject_all_button = driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']")
    reject_all_button.send_keys(Keys.RETURN)

    while not tasks.empty():
        url = tasks.get()

        crawl(url)
        print(tasks)

        tasks.task_done()

def crawl(url):
    driver.get(f'{url}')
    
    elements = driver.find_elements(By.XPATH, './/ul[@data-testid="category-list-links"]/li')

    categories = []
    for element in elements:
        try:
            url = element.find_element(By.XPATH, './/a').get_attribute("href")
            badge = element.find_element(By.XPATH, './/a/span').text

            # tasks.put(url)

            results.append(
            {
                "badge": badge,
                "url": url,
            }
        )
        except NoSuchElementException:
            pass
        except Exception as e:
            print(e)

    return categories


if __name__ == "__main__":

    for category in BASE_CATEGORIES:
        tasks.put(f'{BASE_URL}{category["url"]}')
        break

    threading.Thread(target=worker, daemon=True).start()
    tasks.join()
    driver.quit()

    print('All tasks are completed')

    df = pd.DataFrame(results)
    df.to_csv()
    

# add url from the imtem to differentiate the same and different
# improve savings
# apply dfs
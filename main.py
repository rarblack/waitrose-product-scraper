from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

import time


def crawl(search_term):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    url = f'https://www.waitrose.com/ecom/shop/search?searchTerm={search_term}'
    url2 = f'https://www.waitrose.com/ecom/shop/browse/groceries'
    driver.get(url2)

    reject_all_button = driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']")
    reject_all_button.send_keys(Keys.RETURN)

    time.sleep(2)

    assert "Load more" in driver.page_source

    while (True):
        try:
            load_more_button = driver.find_element(By.XPATH, "//button[@aria-label='Load more']")
            load_more_button.send_keys(Keys.RETURN)
            time.sleep(2)

        except Exception as e:
            break

    time.sleep(2)
    
    results = driver.find_elements(By.XPATH, './/article[@data-testid="product-pod"]')

    products = []
    for results in results:
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

    driver.quit()

    return products


if __name__ == "__main__":
    products = crawl("coffee")

    for product in products:
        print(product)


import json, time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from pprint import pprint


driver = webdriver.Chrome(seleniumwire_options={'disable_encoding': True})
driver.get("https://www.waitrose.com/ecom/shop/browse/groceries/fresh_and_chilled/fresh_fruit")

# reject cookies
try:
    driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']").send_keys(Keys.RETURN)
    time.sleep(1)

except NoSuchElementException as error:
    print(error)
except Exception as error:
    raise error

# sort
try:
    driver.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[2]/div[1]/button").click()
    driver.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
    time.sleep(1)
except NoSuchElementException as error:
    print(error)
except Exception as error:
    raise error

# load all products
while (True):
    try:
        load_more_button = driver.find_element(By.XPATH, "//button[@aria-label='Load more']")
        load_more_button.send_keys(Keys.RETURN)

        time.sleep(1)

    except NoSuchElementException as error:
        print(error)
        break
    except Exception as error:
        raise error

time.sleep(1)

results = []
for request in driver.requests:
    if request.response and request.method == 'POST':
        if request.url.endswith("live?clientType=WEB_APP&tag=browse"):
            
            try:
                body = json.loads(request.response.body.decode('utf-8'))
                results.append(body)
            except Exception as error:
                print(error)

driver.quit()

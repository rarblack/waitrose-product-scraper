from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json, time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pprint import pprint
from seleniumwire import webdriver as wiredwebdriver 


wire_driver = wiredwebdriver.Chrome(seleniumwire_options={'disable_encoding': True})
wire_driver.get("https://www.waitrose.com/ecom/shop/browse/groceries/fresh_and_chilled/fresh_fruit")
try:
    el = wire_driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']").send_keys(Keys.RETURN)
    time.sleep(2)

except Exception as e:
    print(e)

while (True):
    try:
        load_more_button = wire_driver.find_element(By.XPATH, "//button[@aria-label='Load more']")
        load_more_button.send_keys(Keys.RETURN)
        time.sleep(0.5)

    except Exception as e:
        print(e)
        break

time.sleep(0.5)


for request in wire_driver.requests:
    if request.response and request.method == 'POST':
        if request.url.endswith("live?clientType=WEB_APP&tag=browse"):
            # print(f"\n[Request] {request.method} {request.url}")
            # print(f"Status code: {request.response.status_code}")
            # print("Headers:", request.response.headers)
            
            try:
                body = request.response.body.decode('utf-8')
            except:
                body = "<binary or undecodable>"
            
            pprint(body)

wire_driver.quit()

# # Setup Chrome with CDP
# options = Options()
# options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
# driver = webdriver.Chrome(options=options)

# driver.get("https://www.waitrose.com/ecom/shop/browse/groceries/fresh_and_chilled/fresh_fruit")
# driver.find_element(By.XPATH, "//button[@data-webviewid='reject-cookies']").send_keys(Keys.RETURN)

# try:
#     driver.find_element(By.XPATH, "//div[@id='product-refinements']/div[2]/section[2]/div[1]/button").click()
#     driver.find_element(By.XPATH, "//input[@name='A_2_Z']").click()
#     time.sleep(2)

# except Exception as e:
#     print(e)
#     raise e

# while (True):
#     try:
#         load_more_button = driver.find_element(By.XPATH, "//button[@aria-label='Load more']")
#         load_more_button.send_keys(Keys.RETURN)
#         time.sleep(0.5)

#     except Exception as e:
#         print(e)
#         break

# time.sleep(0.5)

# # Access performance logs
# logs = driver.get_log("performance")

# cnt = 0
# for entry in logs:
#     message = json.loads(entry["message"])
#     message = message["message"]

#     if message["method"] == "Network.responseReceived":
#         response = message["params"]["response"]
#         print(f"\nURL: {response['url']}")
#         print(f"Status: {response['status']}")
#         print(f"Response Headers: {response['headers']}")

#     # if message["method"] == "Network.requestWillBeSent":
#     #     url: str = message["params"]["request"]["url"]
#     #     method = message["params"]["request"]["method"]
#     #     if method == "POST" and url.endswith("live?clientType=WEB_APP&tag=browse"):
#     #         # print("POST URL:", url)
#     #         # print("Payload:", message["params"]["request"].get("postData"))
#     #         # pprint(json.loads(message["params"]["request"].get("postData")))
#     #         cnt += 1
#     #         break

# print(cnt)

# driver.quit()

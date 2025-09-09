import logging
from pathlib import Path
from enum import StrEnum, auto

from utils import (
    read_json,
    read_pickle
)
import requests
from requests.auth import HTTPBasicAuth
from http import HTTPStatus
import sys, os


from constants import BASE_PATH, BASE_SERVER_URL, CREDENTIALTS_AUTH

class API:
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
   
    def generate_url(self, *args: list[str]):
        path = "/".join(
            [arg.strip('/') for arg in args]
        )

        return f"{self.base_url}/{path}/"

class MarketplaceAPI(API):
    CATEGORIES = "categories"
    UOMS = "uoms"
    CURRENCIES = "currencies"
    BRANDS = "brands"
    PRICES = "prices"
    STATISTICS = "statistics"
    PRODUCTS = "products"

    def __init__(self, base_url, credentials):
        super().__init__(base_url)
        self.auth = HTTPBasicAuth(**credentials)

    # TODO: add dictionary (endpoint, method) as key and endpoint as a value
    def list_or_create(self, endpoint, data, params = None) -> tuple[bool, dict, requests.Response]:
        url = self.generate_url(endpoint)

        if not params:
            params = data

        response = requests.get(url, params=params, auth=self.auth)
        records = response.json()

        if records['count'] == 0:
            response = requests.post(
                url, 
                auth=self.auth,
                json=data
            )

            if not response.ok:
                raise Exception(f"{endpoint}: Creation issue with {response.status_code} status code")
            
            return (True,  response.json, response)
            
        return (False, response.json, response)
    
    def get_or_create(self, endpoint, data, params = None) -> tuple[bool, dict, requests.Response]:
        url = self.generate_url(endpoint)

        if not params:
            params = data

        response = requests.get(url, params=params, auth=self.auth)
        records = response.json()

        count = records["count"]
        if count == 0:
            response = requests.post(
                url, 
                auth=self.auth,
                json=data
            )

            if not response.ok:
                raise Exception(f"{endpoint}: Creation issue with {response.status_code} status code\nError: {response.text}")
            
            record = response.json()

            return (True,  record, response)
        
        elif count == 1:
            record = records["results"][0]

            return (False, record, response)
        
        else:
            raise Exception(f"{endpoint}: Duplicated records detected")
        

AUTH = HTTPBasicAuth(**CREDENTIALTS_AUTH)
logger = logging.getLogger(__name__)

    
def main():
    try:
        directory_path = f"/products/network-scraping/data"
        directory = Path(f"{BASE_PATH}/{directory_path}")

        file = None
        for filename in directory.iterdir():
            file = read_json(f'{filename}')
            
            data = file[0]["data"]
            if data:
                break

        api = MarketplaceAPI(BASE_SERVER_URL, CREDENTIALTS_AUTH)

        is_created, brand, response = api.get_or_create(
            endpoint=MarketplaceAPI.BRANDS, 
            data={
                "name": "MonkeyChunkey"
            },
        )

        is_created, uom, response = api.get_or_create(
            endpoint=MarketplaceAPI.UOMS, 
            data={
                "name": "Kilogram",
                "code": "kg",
            },
        )
        
        print(brand)

        is_created, product, response = api.get_or_create(
            endpoint=MarketplaceAPI.PRODUCTS, 
            data={
                "name": "Kilogram 2", 
                "thumbnail": "http://localhost:8069/contactus",
                "display_price": "21$",
                "identifier": "12321321",
                "size": "12",
                "brand": brand["id"],
                "uom": uom["id"],
                "quantity": 0.1,
                "categories": [1],
                "vendors": [1],
            }
        )

        print(product)

    except Exception as error:
        logging.ERROR(error)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
 
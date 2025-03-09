# src/api/ebay_client.py
import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EbayClient:
    def __init__(self):
        self.app_id = os.getenv("EBAY_APP_ID")
        self.auth_token = os.getenv("EBAY_AUTH_TOKEN")

    def fetch_browse_data(self, region_name):
        """Fetch data from the eBay Browse API."""
        api_endpoint = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        params = {
            "q": "bestseller",
            "limit": 10,
            "filter": f"deliveryCountry:{region_name}"
        }
        try:
            response = requests.get(api_endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("itemSummaries", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching eBay Browse API data: {e}")
            return []

    def fetch_finding_data(self, region_name):
        """Fetch data from the eBay Finding API."""
        api_endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": "bestseller",
            "GLOBAL-ID": "EBAY-US",
            "paginationInput.entriesPerPage": 10,
            "itemFilter(0).name": "LocatedIn",
            "itemFilter(0).value": region_name
        }
        try:
            response = requests.get(api_endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("findItemsByKeywordsResponse", [])[0].get("searchResult", [{}])[0].get("item", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching eBay Finding API data: {e}")
            return []

    def parse_browse_data(self, data):
        """Parse data from the eBay Browse API."""
        parsed_data = [
            {
                "Product Title": item.get("title", ""),
                "Price": item.get("price", {}).get("value", ""),
                "Currency": item.get("price", {}).get("currency", ""),
                "Condition": item.get("condition", ""),
                "Item URL": item.get("itemWebUrl", "")
            }
            for item in data
        ]
        return pd.DataFrame(parsed_data)

    def parse_finding_data(self, data):
        """Parse data from the eBay Finding API."""
        parsed_data = [
            {
                "Product Title": item.get("title", [{}])[0].get("value", ""),
                "Price": item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", ""),
                "Currency": item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", ""),
                "Location": item.get("location", ""),
                "Item URL": item.get("viewItemURL", [""])[0]
            }
            for item in data
        ]
        return pd.DataFrame(parsed_data)

    def save_to_csv(self, df, filename):
        """Save a DataFrame to a CSV file."""
        try:
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")
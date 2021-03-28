import scrapy
import datetime as dt
import urllib
import json
import os
import csv
import collections

class ListingSpider(scrapy.Spider):
    name = "listing"

    def start_requests(self):
        self.url_generator = AirbnbListingURLGenerator(self.listing_ids)
        urls = self.url_generator.urls
        for url in urls:
            #print("Queueing first url: " + str(url))
            yield scrapy.Request(url=url, headers = self.url_generator.headers, cookies = self.url_generator.cookies, callback=self.parse)

    def parse(self, response):
        json_response = json.loads(response.body)
        for month in json_response['calendar_months']:
            temp_dict = {}
            temp_dict['taken_at'] = dt.datetime.now().strftime('%Y-%m-%d %I-%M%p')
            for key, value in self.flatten(month).items():
                temp_dict[key] = value
            yield temp_dict

    def flatten(self, d, parent_key='', sep='___'):
        items = []
        if isinstance(d, list):
            for num, i in enumerate(d):
                new_key = parent_key + sep + str(num) if parent_key else str(num)
                if isinstance(i, collections.MutableMapping) or isinstance(i, list):
                    items.extend(self.flatten(i, new_key, sep=sep).items())
                else:
                    items.append((new_key, i))
        if isinstance(d, collections.MutableMapping):
            for k, v in d.items():
                new_key = parent_key + sep + k if parent_key else k
                if isinstance(v, collections.MutableMapping) or isinstance(v, list):
                    items.extend(self.flatten(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        return dict(items)

class AirbnbListingURLGenerator:

    def __init__(self, listing_ids):
        self.base_url = "https://www.airbnb.com/api/v2/calendar_months?"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.cookies = dict(sticky_locale='en')
        self.listing_ids = self.parse_ids(listing_ids)
        self.urls = self.generate_all()

    def parse_ids(self, listing_ids):
        return listing_ids.split(",")

    def generate_from_params(self, params):
        return self.base_url + urllib.urlencode(params)

    def generate(self, listing_id):
        params = self.airbnb_params(listing_id)
        return self.generate_from_params(params)

    def generate_all(self):
        urls = []
        for l in self.listing_ids:
            url = self.generate(l)
            urls.append(url)
        return urls

    def airbnb_params(self, listing_id): return {
        "_format": "with_conditions",
        "count": 6,
        "currency": 'USD',
        "key": "d306zoyjsyarp7ifhu67rjxn52tv0t20",
        "listing_id": listing_id,
        "locale": 'en',
        "month": dt.date.today().month,
        "year": dt.date.today().year
    }


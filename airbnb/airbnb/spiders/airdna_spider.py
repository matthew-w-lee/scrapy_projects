import scrapy
import datetime as dt
import urllib
import json
import collections

class AirdnaSpider(scrapy.Spider):
    name = "airdna"

    def start_requests(self):
        self.url_generator = AirdnaURLGenerator(self.access_token)
        urls = self.url_generator.urls
        print(urls)
        for url in urls:
            #print("Queueing first url: " + str(url))
            yield scrapy.Request(url=url, headers = self.url_generator.headers, callback=self.parse)

    def parse(self, response):
        json_response = json.loads(response.body)
        temp_dict = {}
        temp_dict['taken_at'] = dt.datetime.now().strftime('%Y-%m-%d %I-%M%p')
        for key, value in self.flatten(json_response).items():
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
class AirdnaURLGenerator:

    def __init__(self, access_token):
        self.base_url = "https://api.airdna.co/v1/market/pricing/future/daily?"
        self.headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US',
            'Connection': 'keep-alive',
            'Host': 'api.airdna.co'
            }
        #self.cookies = dict(sticky_locale='en')
        self.access_token = access_token
        self.region_id = [126661]
        self.bedrooms = [2]
        self.accommodates = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
        self.urls = self.generate_all()

    def generate_from_params(self, params):
        return self.base_url + urllib.urlencode(params)

    def generate(self, access_token, region_id, bedrooms, accommodates):
        params = self.airdna_params(access_token, region_id, bedrooms, accommodates)
        return self.generate_from_params(params)

    def generate_all(self):
        urls = []
        for r_id in self.region_id:
            for br in self.bedrooms:
                for a in self.accommodates:
                    url = self.generate(self.access_token, r_id, br, a)
                    urls.append(url)
        return urls

    def airdna_params(self, access_token, region_id, bedrooms, accommodates): return {
        "access_token": self.access_token,
        "region_id": region_id,
        "start_month": dt.date.today().month,
        "start_year": dt.date.today().year,
        "number_of_months": 6,
        "percentiles": ".05,.10,.15,.20,.25,.30,.35,.40,.45,.50,.55,.60,.65,.70,.75,.80,.85,.90,.95",
        "start_day": dt.date.today().day,
        "concise": True,
        "room_types": 'entire_place',
        "bedrooms": bedrooms,
        "accommodates": accommodates
    }


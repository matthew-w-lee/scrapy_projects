import scrapy
import datetime as dt
import urllib
import urlparse
import json
import collections

class NeighborhoodSearchSpider(scrapy.Spider):
    name = "neighborhood_search"

    def __init__(self):
        self.locations = [
            "Lincoln Park, Chicago, IL, United States"
        ]
        self.url_generator = AirbnbURLGenerator(self.locations)

    def start_requests(self):
        print("Queueing first url: " + self.url_generator.current_url())
        yield scrapy.Request(url=self.url_generator.current_url(), headers = self.url_generator.headers, cookies = self.url_generator.cookies, callback=self.parse, dont_filter=True)

    def parse(self, response):
        params = self.params_from_response(response)
        page_rank = 0
        #filename = self.filename(params['query'], params['checkin'], params['items_offset'])
        #with open(filename, 'wb') as f:
        #    f.write(response.body)
        #parsing response to follow pagination
        #if there's no more items left, then queue next url    
        json_response = json.loads(response.body)
        listings = next(section['listings'] for section in json_response['explore_tabs'][0]['sections'] if section['result_type'] == "listings")
        for listing in listings:
            page_rank += 1
            temp_dict = {}
            temp_dict['taken_at'] = dt.datetime.now().strftime('%Y-%m-%d %I-%M%p')
            temp_dict['searched_neighborhood'] = params['query']
            temp_dict['checkin'] = params['checkin']
            temp_dict['items_offset'] = params['items_offset']
            temp_dict['page_rank'] = page_rank
            for key, value in self.flatten(listing).items():
                temp_dict[key] = value
            yield temp_dict
        if json_response['explore_tabs'][0]['pagination_metadata']['has_next_page']:
            params['items_offset'] = json_response['explore_tabs'][0]['pagination_metadata']['items_offset']
            print("Queuing up items_offset: " + str(params['items_offset']))
            yield scrapy.Request(url = self.url_generator.generate_from_params(params), callback=self.parse, dont_filter = True, priority = 1)
        else:
            if self.url_generator.has_next_url():
                next_url = self.url_generator.next_url()
                print("Queuing up next url: " + next_url)
                yield scrapy.Request(url=next_url, headers = self.url_generator.headers, cookies = self.url_generator.cookies, callback=self.parse, dont_filter=True)

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

    def filename(self, location, checkin, items_offset):
        return 'scrape_results/{}---{}---checkin-{}---{}.json'.format(str(dt.date.today()), location, checkin, items_offset) 

    def params_from_response(self, res):
        parsed_url = urlparse.urlparse(res.url)
        params = urlparse.parse_qs(parsed_url[4])
        for p in params:
            params[p] = params[p][0]
        return params

class AirbnbURLGenerator:

    def __init__(self, locations):
        self.base_url = "https://www.airbnb.com/api/v2/explore_tabs?"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.cookies = dict(sticky_locale='en')
        self.locations = locations
        self.dates = self.dates_generator()
        self.urls = self.generate_all()
        self.index = 0

    def generate_from_params(self, params):
        return self.base_url + urllib.urlencode(params)

    def generate(self, location, checkin, checkout):
        params = self.airbnb_params(location, checkin, checkout)
        return self.base_url + urllib.urlencode(params)

    def generate_all(self):
        urls = []
        for l in self.locations:
            for d in self.dates:
                url = self.generate(l, d['checkin'], d['checkout'])
                urls.append(url)
        return urls

    def current_url(self):
        return self.urls[self.index]

    def next_url(self):
        self.index += 1
        return self.current_url()

    def has_next_url(self):
        return self.urls[self.index + 1] is not None

    def dates_generator(self):
        today = dt.date.today()
        day_of_week = today.weekday()
        days_til_next_thursday = None
        if day_of_week == 5:
            days_til_next_thursday = 6
        elif day_of_week == 6:
            days_til_next_thursday = 5
        else:
            days_til_next_thursday = 4 - day_of_week
        next_thursday = today + dt.timedelta(days = days_til_next_thursday)
        checkin_checkout_dates = []
        for week in range(1,26):
            trip_days = 3
            current_thursday = next_thursday + dt.timedelta(days = 7*week)
            dates = {"checkin": current_thursday, "checkout": current_thursday + dt.timedelta(days = 3)}
            checkin_checkout_dates.append(dates)
        return checkin_checkout_dates

    def airbnb_params(self, location, checkin, checkout): return {
        "_format": "for_explore_search_web",
        "adults": 1,
        "checkin": checkin,
        "checkout": checkout,
        "children": 0,
        "experiences_per_grid": 20,
        "guidebooks_per_grid": 20,
        "infants": 0,
        "is_standard_search": True,
        "items_per_grid": 18,
        "key": "d306zoyjsyarp7ifhu67rjxn52tv0t20",
        "locale": "en",
        "metadata_only": False,
        "query": location,
        "refinement_paths[]": "/homes",
        "room_types[]": "Entire home/apt",
        "screen_size": "large",
        "timezone_offset": -300,
        "toddlers": 0,
        "items_offset": 0
    }


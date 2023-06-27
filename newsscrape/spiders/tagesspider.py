import scrapy

# from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
import datetime

from ..items import NewsscrapeItem


class TagesspiderSpider(CrawlSpider):
    name = "tagesspider"
    allowed_domains = ["www.tagesschau.de"]
    # start_urls = ["https://www.tagesschau.de/archiv?datum=2023-06-22"]
    # start_urls = list(urls())

    def start_requests(self):
        base = datetime.datetime.today()
        numdays = 365
        date_list = reversed(
            [base - datetime.timedelta(days=x + 1) for x in range(numdays)]
        )
        for date in date_list:
            yield scrapy.Request(
                url=f"https://www.tagesschau.de/archiv?datum={date.strftime('%Y-%m-%d')}",
                callback=self.parse,
            )

    def parse(self, response):
        articles = response.css(".teaser-right")
        for article in articles:
            item = NewsscrapeItem()
            # item = {}
            # unix timestamp?
            item["tstamp"] = article.css("::attr(data-teaserdate)").get()
            item["title"] = article.css(".teaser-right__headline::text").get().strip()
            # naive datetime string
            item["date"] = article.css(".teaser-right__date::text").get().strip()
            item["shorttext"] = (
                article.css(".teaser-right__shorttext::text").get().strip()
            )

            # try to get the article's url and scrape its full text
            item["url"] = article.css(".teaser-right__link::attr(href)").get()
            if item["url"]:
                yield scrapy.Request(
                    f'https://www.tagesschau.de{item["url"]}',
                    self.parse_full_text,
                    cb_kwargs={"item": item},
                )
            else:
                item["fulltext"] = None
                yield item

    def parse_full_text(self, response, item):
        item["fulltext"] = " ".join(
            [p.strip() for p in response.css("article > p").css("::text").getall()]
        )
        yield item

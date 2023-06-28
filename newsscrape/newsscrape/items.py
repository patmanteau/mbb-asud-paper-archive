# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsscrapeItem(scrapy.Item):
    tstamp = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    shorttext = scrapy.Field()
    fulltext = scrapy.Field()
    url = scrapy.Field()

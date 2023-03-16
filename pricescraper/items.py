# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PricescraperItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    id = scrapy.Field()
    origin_price = scrapy.Field()
    current_price = scrapy.Field()
    eilat_price = scrapy.Field()

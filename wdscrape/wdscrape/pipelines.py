# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import jsonlines as jl


class WdscrapePipeline:
    def open_spider(self, spider):
        self.jl_file = jl.open("../data/4_wd-catalog.jsonl", "a")

    def close_spider(self, spider):
        self.jl_file.close()

    def process_item(self, item, spider):
        self.jl_file.write(item)
        return item

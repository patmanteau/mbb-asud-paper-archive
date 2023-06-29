import scrapy
import json
import jsonlines as jl


class WdspiderSpider(scrapy.Spider):
    name = "wdspider"
    allowed_domains = ["www.wikidata.org"]
    # start_urls = ["https://www.wikidata.org/wiki/Special:EntityData/Q42.json"]

    def start_requests(self):
        existing = []

        with jl.open("../data/4_wd-catalog.jsonl", "r") as wd_items:
            existing = [
                item["id"] for item in wd_items.iter(type=dict, skip_invalid=True)
            ]

        with jl.open("../data/3_catalog.jsonl", "r") as req_items:
            for item in req_items:
                if item["id"] not in existing:
                    yield scrapy.Request(
                        url=f"https://www.wikidata.org/wiki/Special:EntityData/{item['id']}.json",
                        callback=self.parse,
                        cb_kwargs=dict(entity_id=item["id"]),
                    )

    def parse(self, response, entity_id):
        res = json.loads(response.body)
        item = {}
        item["url"] = response.url
        item["id"] = entity_id

        # get correct id if redirected
        id_ = list(res["entities"].keys())[0]
        if id_ != entity_id:
            item["redirect"] = id_

        item["label"] = (
            res["entities"][id_]["labels"]["en"]["value"]
            if res["entities"][id_]["labels"].get("en")
            else id_
        )
        item["description"] = (
            res["entities"][id_]["descriptions"]["en"]["value"]
            if res["entities"][id_]["descriptions"].get("en")
            else id_
        )

        yield item

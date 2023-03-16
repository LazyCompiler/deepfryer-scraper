import scrapy
from decimal import Decimal
from re import sub
from urllib.parse import urlparse, ParseResult, parse_qs, urlencode
import time

def _parse_item(item_element):
    product_id = item_element.attrib['id'].split('_')[-1]
    try:
        product_name_text = item_element.css('h3.title_with_brand::text').get().strip()

        origin_price_text = item_element.xpath(
            './/span[contains(@class, "items_show_origin_price_text")]/following-sibling::text()').get()
        origin_price = Decimal(sub(r'[^\d.]', '', origin_price_text.strip())) if origin_price_text else float('nan')

        current_price_text = item_element.xpath(
            './/span[contains(@class, "items_show_price_text")]/following-sibling::text()').get()
        current_price = Decimal(sub(r'[^\d.]', '', current_price_text.strip())) if current_price_text else float('nan')

        eilat_price_text = item_element.css('span.items_show_eilat_price_price').get()
        eilat_price = Decimal(sub(r'[^\d.]', '', eilat_price_text.strip())) if eilat_price_text else float('nan')

        return {
                'name': product_name_text,
                'id': product_id,
                'origin_price': origin_price,
                'current_price': current_price,
                'eilat_price': eilat_price,
            }
    except Exception as e:
        print(f'Failed to parse item {item_element}: {e}')  # TODO - log
        return None


class HalilitCategoriesSpider(scrapy.Spider):
    name = 'halilitcategories'
    allowed_domains = ['halilit.com']
    download_delay = 5
    randomize_download_delay = True
    current_url = None

    def parse(self, response, **kwargs):
        self.current_url = response.url

        timestamp = int(round(time.time() * 1000))

        # Find the amount of results text to avoid pages with display:none results
        results_element = response.css('span.results b::text').get()
        if not results_element:
            # Save the results body to .html file
            # with open(f'./{timestamp}_result.html', 'w') as f:
            #     f.write(response.body.decode('utf-8'))

            print("No results found")
            # Add to shall_be_filtered.tet file
            # Add new line to the file and create it if it doesn't exist
            # with open('shall_be_filtered.txt', 'a') as f:
            #     f.write(response.url + '\r\n')
            return

        product_elements = response.xpath("//div[contains( @ id, 'item_id_')]")
        for product_element in product_elements:
            parsed_item = _parse_item(product_element)

            if parsed_item:
                parsed_item['time'] = timestamp
                yield parsed_item

            # item_loader = ItemLoader(item=PricescraperItem(), selector=product_element)
            # item_loader.add_value('name', product_name_text)
            # item_loader.add_value('id', product_id)
            # item_loader.add_value('origin_price', origin_price)
            # item_loader.add_value('current_price', current_price)
            # item_loader.add_value('eilat_price', eilat_price)
            # yield item_loader.load_item()

        if len(product_elements) > 0:
            current_url = urlparse(response.url)
            params = parse_qs(current_url.query)
            next_page_number = (int(params['page'][0]) + 1) if 'page' in params else 2
            params['page'] = next_page_number
            result = ParseResult(scheme=current_url.scheme, netloc=current_url.hostname, path=current_url.path, params=current_url.params, query=urlencode(params),
                              fragment=current_url.fragment)
            next_url = result.geturl()
            yield scrapy.Request(next_url, callback=self.parse)

    # def close(self, reason):
    #     start_time = self.crawler.stats.get_value('start_time')
    #     finish_time = self.crawler.stats.get_value('finish_time')
    #     print("Total run time: ", finish_time-start_time)
    #
    #     page_url_without_page_number_param = self.current_url.split('?page')[0]
    #
    #     average_timer = AverageTimer()
    #     average_timer.add_running_time(start_time, finish_time, page_url_without_page_number_param)


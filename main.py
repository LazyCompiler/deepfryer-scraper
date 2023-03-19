import time

from dotenv import load_dotenv

load_dotenv()

import argparse
import json
import os

import boto3
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from pricescraper.spiders.halilitcategories_spider import HalilitCategoriesSpider

sqs_client = boto3.client("sqs")
# sqs_queue_url = os.getenv('AWS_SQS_QUEUE_URL')
sqs_queue_url = "https://sqs.eu-central-1.amazonaws.com/968553126320/DeepfryerCollectorStack-DeepfryerCollectorQueue37797886-cCK8ZGgwWRka"


def get_messages_from_sqs(amount_of_messages=1):
    print(f"Getting {amount_of_messages} messages from SQS queue {sqs_queue_url}...")
    response = sqs_client.receive_message(
        QueueUrl=sqs_queue_url,
        AttributeNames=["SentTimestamp"],
        MaxNumberOfMessages=amount_of_messages,
        WaitTimeSeconds=20,
    )
    if "Messages" in response:
        response_messages = response["Messages"]
        for message in response_messages:
            sqs_client.delete_message(
                QueueUrl=sqs_queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
        return response_messages
    else:
        print("No messages in queue")
        return []


def scrape(urls):
    if len(urls) > 0:
        scraper_settings = get_project_settings()
        process = CrawlerProcess(scraper_settings)
        process.crawl(HalilitCategoriesSpider, start_urls=urls)
        process.start()
        process.stop()


def get_urls(amount_of_messages: int):
    messages = []
    messages_from_sqs = get_messages_from_sqs(amount_of_messages)

    # Get all the messages from SQS
    while len(messages_from_sqs) > 0:
        messages.extend(messages_from_sqs)
        messages_from_sqs = get_messages_from_sqs(amount_of_messages)

    if len(messages) > 0:
        parsed_json_bodies = [json.loads(message["Body"]) for message in messages]
        parsed_json_messages = [
            json.loads(parsed_json_body["Message"])
            for parsed_json_body in parsed_json_bodies
        ]
        urls_to_scrap = [message["Url"] for message in parsed_json_messages]
        return urls_to_scrap


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--amount_of_messages", type=int, default=1)
    parser.add_argument("--debug_urls", type=str, nargs="+", default=[])
    args = parser.parse_args()

    scrap_urls = (
        get_urls(args.amount_of_messages)
        if len(args.debug_urls) == 0
        else args.debug_urls
    )

    starting_time = time.time()
    if scrap_urls and len(scrap_urls) > 0:
        scrape(scrap_urls)

    ending_time = time.time()
    print(f"Scraping took {ending_time - starting_time} seconds")
    print(
        f"Average time per item: {(ending_time - starting_time) / len(scrap_urls)} seconds"
    )
    print("Done")

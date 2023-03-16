import boto3
from dotenv import load_dotenv
import math

load_dotenv()

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


class PricescraperPipeline:
    def __init__(self):
        self.client = None
        self.items = []

    def process_item(self, item, spider):
        # If no prices are available, log
        if 'current_price' not in item and 'eilat_price' not in item and 'origin_price' not in item:
            print(f'No prices available for item {item["name"]}')

        self.items.append(item)
        return item

    def open_spider(self, spider):
        self.client = boto3.client('timestream-write')

    def close_spider(self, spider):
        records = []

        # Remove duplicates by ID
        self.items = list({item['id']: item for item in self.items}.values())

        for item in self.items:
            records.append({
                'MeasureName': 'halilit_price',
                'MeasureValue': str(item['current_price'] if not math.isnan(item['current_price']) else -1),
                'MeasureValueType': 'DOUBLE',
                'Time': str(item['time']),
                'Dimensions': [
                    {
                        'Name': 'item_id',
                        'Value': str(item['id'])
                    },
                    {
                        'Name': 'item_name',
                        'Value': str(item['name'])
                    },
                    {
                        'Name': 'origin_price',
                        'Value': str(item['origin_price']) if 'origin_price' in item else None
                    },
                    {
                        'Name': 'eilat_price',
                        'Value': str(item['eilat_price'])
                    },
                    {
                        'Name': 'current_price',
                        'Value': str(item['current_price'])
                    }
                ]
            })

        # Split records into chunks of 100
        records_chunks = [records[i:i + 100] for i in range(0, len(records), 100)]
        for index, records_chunk in enumerate(records_chunks):
            # Write records to Timestream
            result = self.client.write_records(
                DatabaseName='deepfryer',
                TableName='prices',
                Records=records_chunk
            )
            success = result['ResponseMetadata']['HTTPStatusCode'] == 200
            print(f'Wrote chunk {index + 1} of {len(records_chunks)} to Timestream.')
            if not success:
                print(f'Error writing chunk {index + 1} to Timestream: {result}')
                print(result)
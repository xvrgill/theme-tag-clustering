from modules.scraper import InsightPageScraper
from modules.extractor import ExcelToDataFrame
import pandas as pd
from pandas import DataFrame
import numpy as np

# PANDAS DISPLAY OPTIONS
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.precision', 3)

# aem_path = '/content/invesco/us/en/insights/chinese-onshore-bonds-understanding-policy-signals-and-market-structure'
# audience_role = 'Institutional'
# scraper = InsightPageScraper(aem_path, audience_role)
# scraper.scrape()
# print(scraper.url_with_audience_role)
# print(scraper.publish_date)

us_report_path = 'data/aem_export_082422/xlsm/USNodePageReport_8.24.xlsm'
extractor = ExcelToDataFrame(us_report_path)
extractor.extract()
df: DataFrame = extractor.df_list[0]
# Only include insights pages
df = df[df['content_type_tags'] == 'Insight']


def process_urls(row):
    aem_path = row['aem_path']
    audience_role_parameters = row['user_role_param']
    for param in audience_role_parameters:
        scraper = InsightPageScraper(aem_path, param)
        scraper.scrape()
        row['status_code'] = scraper.status_code
        row['url_with_params'] = scraper.url_with_audience_role
        if scraper.status_code == 200:
            row['publish_date'] = scraper.publish_date
            break
        else:
            row['publish_date'] = np.nan
    return row


df = df.apply(process_urls, axis=1)
test_export_path = us_report_path = 'data/test/'
df.to_csv(test_export_path + 'scraped.csv')



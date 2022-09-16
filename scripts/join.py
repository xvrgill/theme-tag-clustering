import pandas as pd
import re

# Set pandas display options for previewing work
pd.set_option('display.max_columns', None)
# pd.set_option('display.width', None)
pd.set_option('display.precision', 3)

# Define relative paths of spreadsheets to join
scraped_us_node_report = 'data/test/scraped.csv'
content_views_report = 'data/aem_export_082422/xlsx/US 2022 Content Views.xlsx'

# Create dataframes from both spreadsheets
node_report_df = pd.read_csv(scraped_us_node_report, converters={
    'tags': pd.eval,
    'topic': pd.eval,
    'program': pd.eval,
    'asset_class': pd.eval,
    'user_role_param': pd.eval,
    'theme': pd.eval,
    'user_role': pd.eval
})
content_views_df = pd.read_excel(content_views_report, sheet_name='Data by Article')


# Previewing node report df
# print(node_report_df)

# Update page path so that it can be used as a primary key for join
def format_url(row):
    url: str = row['url_with_params']
    path = url.replace('https://www.invesco.com', '')
    pattern = re.compile(r'\?[a-zA-z=]+')
    match = re.search(pattern, path).group(0)
    # print(match)
    path = path.replace(match, '')

    return path


node_report_df['pagePath'] = node_report_df.apply(format_url, axis=1)
# print(node_report_df['authors'].explode(ignore_index=True))

# Join full join on pagePath
merged = node_report_df.merge(content_views_df, how='outer', on='pagePath')


# Make tags lists
# def to_list(row):
#     cols_to_reformat = ['tags', 'topic', 'program', 'theme', 'asset_class']
#     for col in cols_to_reformat:
#         values = row[col]
#         print(list(values))
#         new_list = []
#         for val in values:
#             print(val)
#             new_list.append(val)
#         row[col] = new_list
#     return row


# merged = merged.apply(to_list, axis=1)

# Explode tags and authors
merged = merged.explode('topic', ignore_index=True)
merged = merged.explode('theme', ignore_index=True)
merged = merged.explode('program', ignore_index=True)
merged = merged.explode('user_role', ignore_index=True)
merged = merged.explode('asset_class', ignore_index=True)
merged = merged.explode('authors', ignore_index=True)

merged.to_csv('data/test/merged.csv', index=False)

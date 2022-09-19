from modules.extractor import ReutersTextsExtractor
import glob
import json
from tqdm import tqdm

text_file = '../public_data/reuters/reuters-21578/reut2-000.sgm'
files = glob.glob('../public_data/reuters/reuters-21578/*.sgm')
json_save_path = '../public_data/reuters/reuters_json/reuters-21578.json'

texts = []
print('Extractor initialized')

for file in files:
    print(f'Extracting file: {file}')
    extractor = ReutersTextsExtractor(file)
    for text_dict in extractor.extract():
        texts.append(text_dict)

print(f'Saving to json file: {json_save_path}')
with open(json_save_path, 'w', encoding='utf-8') as f:
    json.dump(texts, f, indent=4)

print('Extraction complete')
from abc import ABC
import pandas as pd
from pandas import DataFrame
import xlrd
from xlrd import Book
import numpy as np
from typing import List
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from typing import Union
from tqdm import tqdm


class Extractor(ABC):
    pass


class ExcelToDataFrame(Extractor):

    def __init__(self, filename: str):
        self.filename = filename
        self.sheet_names = None
        self.df_list = None

    def extract(self):
        # May need create logic to pass in a particular sheet name
        df_dict = pd.read_excel(self.filename, sheet_name=None)
        sheet_names = []
        df_list = []
        for k, v in df_dict.items():
            sheet_names.append(k)
            df = v
            df = self.format_columns(df)
            df['user_role'] = df.apply(self.format_user_role, axis=1)
            df['user_role_param'] = df.apply(self.format_user_role_as_parameter, axis=1)
            df['asset_class'] = df.apply(self.format_asset_class, axis=1)
            df['tags'] = df.apply(self.format_tags, axis=1, tag_name='tags')
            df['topic'] = df.apply(self.format_tags, axis=1, tag_name='topic')
            df['program'] = df.apply(self.format_tags, axis=1, tag_name='program')
            df['theme'] = df.apply(self.format_tags, axis=1, tag_name='theme')
            df['authors'] = df.apply(self.format_authors, axis=1)
            df = df.explode('authors')
            df_list.append(df)
        self.sheet_names = sheet_names
        self.df_list = df_list

    @property
    def column_map(self):
        return {
            'Path': 'aem_path',
            'Title': 'page_title',
            'Template': 'template',
            'Last Modified': 'last_modified',
            'Tags': 'tags',
            'Topic': 'topic',
            'Program': 'program',
            'Theme': 'theme',
            'Content type tags': 'content_type_tags',
            'User role': 'user_role',
            'Asset Class': 'asset_class',
            'Product': 'product',
            'Investment Vehicle': 'investment_vehicle',
            'Strategy': 'strategy',
            'Business Unit': 'business_unit',
            'Person': 'person',
            'Team': 'team',
            'Last modified by': 'last_modified_by',
            'Created by': 'created_by',
            'Replication Status': 'replication_status',
            'Author(s)': 'authors'
        }

    def column_mapper_func(self, column_name: str):
        return self.column_map[column_name]

    def format_columns(self, df: DataFrame):
        columns = df.columns
        new_columns = list(map(self.column_mapper_func, list(columns)))
        df.columns = list(new_columns)
        return df

    @staticmethod
    def format_user_role(row):
        user_roles: str = row['user_role']
        # Keep nan values
        if user_roles == np.nan:
            return
        # Split string by semicolon delimiter
        user_role_list = str(user_roles).split(';')
        # Drop audinence roles that aren't valid user role url parameters
        roles_to_drop = [
            'EDJONES',
            'PFS',
            '2021 DC Language Research Study',
            'Indexing Solutions',
            'Multi Alternatives Solutions'
        ]
        for role in roles_to_drop:
            if role in user_role_list:
                user_role_list.remove(role)
        return user_role_list

    @staticmethod
    def format_user_role_as_parameter(row):
        user_roles: List[str | np.nan] = list(row['user_role'])
        if user_roles == np.nan:
            return
        user_roles = [role.replace(' ', '') for role in user_roles]
        return user_roles

    @staticmethod
    def format_asset_class(row):
        asset_classes = row['asset_class']
        if asset_classes == np.nan:
            return
        asset_classes = str(asset_classes).split(';')
        return asset_classes

    def format_tags(self, row, tag_name: str):
        tags = row[tag_name]
        tag_list = list(self.str_to_list(str(tags)))
        tag_list_sans_double_spaces = [self.remove_double_spaces(x) for x in tag_list]
        # new_list = []
        # for tag in tag_list_sans_double_spaces:
        #     print(tag)
        #     new_list.append(tag)
        return tag_list_sans_double_spaces

    @staticmethod
    def str_to_list(string: str) -> List[str]:
        return string.split(';')

    @staticmethod
    def remove_double_spaces(string: str) -> str:
        return string.replace('  ', ' ')

    @staticmethod
    def format_authors(row):
        author_str = str(row['authors'])
        # Remove Invesco:person/ from string
        new_str = author_str.replace('invesco:person/', '')
        # Split string at semicolon delimiter
        author_list = new_str.split(';')
        # print(author_list)
        return list(author_list)

    # def explode_authors(self, row):
    #     author_str = str(row['authors'])
    #     author_list = self.format_authors(author_str)
    #     author_col_list = []
    #     for i, author in enumerate(author_list):
    #         author_col_list.append(author)
    #         column_name = f'author_{i + 1}'
    #         row[column_name] = author
    #     row['authors'] = author_col_list
    #     return row

    # def explode_authors(self, df: DataFrame):
    #     df = df.explode('authors')
    #     return df


class CSVToDataFrame(ExcelToDataFrame):

    def __init__(self, filename: str):
        super().__init__(filename)

    @property
    def data_frame(self):
        # May need create logic to pass in a particular sheet name
        return pd.read_csv(self.filename)

# TODO: Review this class to see if it is required - likely unnecessary
class XLSMToCSV(Extractor):

    def __init__(self, filename: str):
        self.filename = filename
        self.book: Book = self.open_file()
        self.sheet_count: int = self.get_sheet_count()
        self.sheet_names: list = self.get_sheet_names()
        self.sheet_row_count: list = self.get_sheet_row_count()

    def open_file(self):
        return xlrd.open_workbook(self.filename)

    def get_sheet_count(self):
        return self.book.nsheets()

    def get_sheet_names(self):
        return self.book.sheet_names()

    def get_sheet_row_count(self):
        return [s.nrows for s in self.sheet_names]

    def get_sheet_column_count(self):
        return [s.ncols for s in self.sheet_names]

    def to_dataframe(self):
        frames = []
        for name in self.sheet_names:
            frame = pd.read_excel(self.filename, sheet_name=name)
            frames.append(frame)

        return tuple(frames)


class SGMExtractor(Extractor):

    def __init__(self, file_path: str) -> None:
        """ Base class for the extractor for SGM files

        :param file_path: path to sgm file to be extracted
        """
        self.file_path = file_path
        self.soup = self.create_soup(file_path)

    @staticmethod
    def create_soup(file_path: str) -> BeautifulSoup:
        """ Creates BeautifulSoup object with lxml parser

        :param file_path: path of file to be passed to BeautifulSoup
        :return: BeautifulSoup object
        """
        with open(file_path, 'rb') as f:
            # TODO: Allow for alternate parsers to be selected when called
            soup = BeautifulSoup(f, features='lxml')

        return soup


class ReutersTextsExtractor(SGMExtractor):

    def __init__(self, file_path: str) -> None:
        """ Extractor for the Reuters corpus dataset

        :param file_path: path of SGM file to be extracted
        """

        super().__init__(file_path)

    def get_sgm_texts(self) -> ResultSet:
        """ Retrieves all individual texts within the SGM file passed to the class

        :return: Result set of all texts in the file
        """

        result = self.soup.find_all('reuters')

        return result

    @staticmethod
    def get_text_date(result: Tag) -> str:
        """ Find date tag and extract its text

        :param result: A BeautifulSoup tag that represents the text data of an individual text
        :return: The string representation of the tag's contents
        """

        # There should always be a date tag, so no need to handle attribute errors
        date_tag: Tag = result.date
        date = date_tag.get_text()

        return date

    @staticmethod
    def get_text_topics(result: Tag) -> Union[list[str], None]:
        topic_tag: Tag = result.topics
        topic_wrappers = topic_tag.find_all('d')
        if len(topic_wrappers) < 1:
            return None
        topic_list = [wrapper.get_text() for wrapper in topic_wrappers]

        return topic_list

    @staticmethod
    def get_text_places(result: Tag):
        places_tag: Tag = result.places
        places_wrappers = places_tag.find_all('d')
        if len(places_wrappers) < 1:
            return None
        places_list = [wrapper.get_text() for wrapper in places_wrappers]

        return places_list

    @staticmethod
    def get_text_people(result: Tag):
        people_tag: Tag = result.people
        people_wrappers = people_tag.find_all('d')
        if len(people_wrappers) < 1:
            return None
        people_list = [wrapper.get_text() for wrapper in people_wrappers]

        return people_list

    @staticmethod
    def get_text_orgs(result: Tag):
        orgs_tag: Tag = result.orgs
        orgs_wrappers = orgs_tag.find_all('d')
        if len(orgs_wrappers) < 1:
            return None
        orgs_list = [wrapper.get_text() for wrapper in orgs_wrappers]

        return orgs_list

    @staticmethod
    def get_text_exchanges(result: Tag):
        exchanges_tag: Tag = result.exchanges
        exchanges_wrappers = exchanges_tag.find_all('d')
        if len(exchanges_wrappers) < 1:
            return None
        exchanges_list = [wrapper.get_text() for wrapper in exchanges_wrappers]

        return exchanges_list

    @staticmethod
    def get_text_companies(result: Tag):
        companies_tag: Tag = result.companies
        companies_wrappers = companies_tag.find_all('d')
        if len(companies_wrappers) < 1:
            return None
        companies_list = [wrapper.get_text() for wrapper in companies_wrappers]

        return companies_list

    @staticmethod
    def get_text_title(result: Tag):
        try:
            title_text = result.find('text').find('title').get_text()
        except AttributeError:
            return None
        if len(title_text) < 1:
            return None

        return title_text

    @staticmethod
    def get_text_author(result: Tag):
        try:
            author_text = result.find('text').find('author').get_text()
        except AttributeError:
            return None
        if len(author_text) < 1:
            return None

        return author_text

    @staticmethod
    def get_text_dateline(result: Tag):
        try:
            dateline_text = result.find('text').find('dateline').get_text()
        except AttributeError:
            return None
        if len(dateline_text) < 1:
            return None

        return dateline_text

    @staticmethod
    def get_text_body(result: Tag):
        try:
            body_text = result.find('text').find('dateline').nextSibling.get_text()
        except AttributeError:
            return None
        if len(body_text) < 1:
            return None

        return body_text

    def extract(self):
        texts_list = self.get_sgm_texts()
        for text in tqdm(texts_list):
            text_dict = {
                'date': self.get_text_date(text),
                'topics': self.get_text_topics(text),
                'places': self.get_text_places(text),
                'people': self.get_text_people(text),
                'orgs': self.get_text_orgs(text),
                'exchanges': self.get_text_exchanges(text),
                'companies': self.get_text_companies(text),
                'text': {
                    'title': self.get_text_title(text),
                    'author': self.get_text_author(text),
                    'dateline': self.get_text_dateline(text),
                    'body': self.get_text_body(text)
                }
            }
            yield text_dict


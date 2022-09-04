from abc import ABC
import pandas as pd
from pandas import DataFrame
import xlrd
from xlrd import Book
import numpy as np
from typing import List


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
            df = df.apply(self.explode_authors, axis=1)
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
        # Drop EDJONES and PFS from list since they aren't valid url params
        roles_to_drop = ['EDJONES', 'PFS']
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
        tag_list = self.str_to_list(str(tags))
        tag_list_sans_double_spaces = [self.remove_double_spaces(x) for x in tag_list]
        return tag_list_sans_double_spaces

    @staticmethod
    def str_to_list(string: str) -> List[str]:
        return string.split(';')

    @staticmethod
    def remove_double_spaces(string: str) -> str:
        return string.replace('  ', ' ')

    @staticmethod
    def format_authors(author_str: str):
        # Remove Invesco:person/ from string
        new_str = author_str.replace('invesco:person/', '')
        # Split string at semicolon delimiter
        author_list = new_str.split(';')
        return author_list

    def explode_authors(self, row):
        author_str = str(row['authors'])
        author_list = self.format_authors(author_str)
        print(author_list  )
        for i, author in enumerate(author_list):
            column_name = f'author_{i+1}'
            row[column_name] = author
        return row


class CSVToDataFrame(ExcelToDataFrame):

    def __init__(self, filename: str):
        super().__init__(filename)

    @property
    def data_frame(self):
        # May need create logic to pass in a particular sheet name
        return pd.read_csv(self.filename)


class XLSMToCSV(Extractor):

    def __init__(self, filename: str):
        self.filename = filename
        self.book: Book = self.open_file()
        self.sheet_count: int = self.get_sheet_count()
        self.sheet_names: list = self.get_sheet_names()
        self.sheet_row_count: list = self.get_sheet_row_count()

    def open_file(self):
        # Open workbook
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

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
from requests import Response


class Scraper(ABC):

    @abstractmethod
    def __init__(self):
        pass


# Scraper to be used for each instance of an AEM page
class AEMScraper(Scraper):

    def __init__(self, aem_path: str, audience_role: str) -> None:
        super().__init__()
        self.base_url = 'https://www.invesco.com'
        self.aem_path = aem_path
        self.audience_role = audience_role
        self.full_path = self.create_full_url()
        self.publish_date = None
        self.status_code = None

    def create_full_url(self) -> str:
        full_path = self.aem_path.replace(r'/content/invesco', self.base_url) + '.html'
        return full_path

    @property
    def url_with_audience_role(self):
        return self.full_path + '?audienceRole=' + self.audience_role

    def get_html(self) -> Response|None:
        params = {'audienceRole': self.audience_role}
        response = requests.get(self.full_path, params=params)
        self.status_code = response.status_code
        # Ensure status code is 200
        if response.status_code != 200:
            return None
        return response

    @staticmethod
    def get_lxml_from_response(response_object: Response) -> BeautifulSoup:
        content = response_object.content
        return BeautifulSoup(content, 'lxml')


# Scraper to be used for each instance of an AEM page - insights pages only
class InsightPageScraper(AEMScraper):

    def __init__(self, aem_path: str, audience_role: str):
        super(InsightPageScraper, self).__init__(aem_path, audience_role)

    @staticmethod
    def parse_publish_date(soup: BeautifulSoup) -> str:
        publish_date_element = soup.find('span', attrs={'class': 'article-hero__date'})
        if not publish_date_element:
            raise AttributeError
        publish_date: str = publish_date_element['data-publishdate']
        return publish_date

    def scrape(self):
        response = self.get_html()
        if not response:
            return
        soup = self.get_lxml_from_response(response)
        # Save publish date
        try:
            publish_date = self.parse_publish_date(soup)
        except AttributeError:
            print('Publish date parameter does not exist for:')
            print(self.url_with_audience_role)
        else:
            self.publish_date = publish_date

import urllib
from lxml.html import fromstring


class MSDEF (object):

    def __init__(self, month = None, year = None):
        self.__htmlcache = "html/"
        self.__content = ""
        self.__advisoryLinkMap = {}
        self.__year = year
        self.__month = month

    def get_advisory_link_map(self):
        if not self.__month or not self.__year:
            self.__get_current_month()

        url = self.__get_url()
        self.__page_read(url, self.__htmlcache + \
                       self.__year + "-" + self.__month + ".html")
        self.__map_advisory_links()

        return self.__advisoryLinkMap

    def __get_hrefs(self, html):
        hrefs = []

        if html is None:
            return

        if html.tag in ['a']:
            return [html]

        for each in html.getchildren():
            href = self.__get_hrefs(each)

            if href:
                hrefs.extend(href)

        return hrefs

    def __map_advisory_links(self):
        html = fromstring(self.__content)
        self.__advisoryLinkMap = dict([(self.__isBulletin(each.\
                              text_content()), each.get('href'))\
                              for each in self.__get_hrefs(html)\
                      if self.__isBulletin(each.text_content())])

    def __isBulletin(self, content):
        import re
        result = re.findall("^MS[0-9][0-9]-[0-9]+$", content)

        if result and len(result) == 1:
            return result[0]

        return False

    def __get_url(self):
        base_url = "http://technet.microsoft.com/en-us/security/bulletin/"
        base_url += "ms" + self.__year + "-" + self.__month
        return base_url

    def __page_read(self, url, filename):
        import os

        if not os.path.isfile(filename):
            self.__save_page(url, filename)

        self.__content = open(filename).read()

    def __save_page(self, url, filename):
        import sys
        try:
            url_open = urllib.URLopener()
            url_open.retrieve(url, filename)
        except Exception, msg:
            sys.exit(msg)

    def __get_current_month(self):
        import datetime
        today = datetime.date.today()
        self.__month = today.strftime('%h')
        self.__year = today.strftime('%Y')
        self.__year = self.__year[2:]
        self.__month = self.__month.lower()


def main():
    msdf = MSDEF("apr", "12")
    print msdf.get_advisory_link_map()

if __name__ == "__main__":
    main()

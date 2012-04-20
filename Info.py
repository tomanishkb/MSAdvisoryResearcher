import urllib
from kb import KBDetails
from configobj import ConfigObj
from lxml.html import fromstring
config = None
filename = "conf/msbulletin.conf"


class INFOBank (object):

    def __init__(self, url, bulletin):
        self.__url = url
        self.__bulletin = bulletin
        self.__info_db = {}
        self.__filename = "html/" + bulletin + ".html"
        self.__content = ""
        self.__affected_os = []
        self.__os_map = None

    def get_info_db(self):
        self.__create_db()
        return self.__info_db

    def __collect_details(self):
        self.__read_page()
        self.__parse_bulletin()

    def __get_os_name(self, name):
        os = config['os']
        os_name = None

        for each in os:
            if name.lower().__contains__(each.lower()):
                if os_name:
                    if len(os_name) == len(each):
                        print "OS Detection Error", os_name, each
                        return None
                    elif len(os_name) < len(each):
                        os_name = each
                else:
                    os_name = each

        return os_name

    def __get_milestone(self, name):
        milestones = config["milestones"]
        milestone = None

        for each in milestones:
            for each_milestone in milestones[each]:
                if name.lower().__contains__(each_milestone.lower()):
                    if milestone:
                        if len(milestone) == len(each):
                            print "Milestone Detection Error", name, milestone
                            return None
                        elif len(milestone) < len(each):
                            milestone = each
                    else:
                        milestone = each
        if not milestone:
            milestone = "none"

        return milestone

    def __get_arch(self, name):
        archs = config["architectres"]
        arch = None

        for each in archs:
            for each_arch in archs[each]:
                if name.lower().__contains__(each_arch.lower()):
                    if arch:
                        if len(arch) < len(each):
                            arch = each
                        elif len(arch) == len(each):
                            print "Milestone Detection Error", name, arch
                            return None
                    else:
                        arch = each
        if not arch:
            arch = "x86"

        return arch

    def __get_affectd_os_map(self):
        os_map = {}

        for each in self.__affected_os:
            os_name = self.__get_os_name(each)
            sp_name = self.__get_milestone(each)
            arch = self.__get_arch(each)

            if os_name is None or sp_name is None or arch is None:
                return None

            if os_name not in os_map:
                os_map[os_name] = {}
            if arch not in os_map[os_name]:
                os_map[os_name][arch] = {}
            if sp_name not in os_map[os_name][arch]:
                os_map[os_name][arch][sp_name] = {}

        return os_map

    def __parse_bulletin(self):
        global config
        config = ConfigObj(filename)
        self.__info_db["title"] = self.__get_title()
        self.__info_db["description"] = self.__get_description()
        kb_list = self.__get_affected_platform_info()
        self.__os_map = self.__get_affectd_os_map()

        for each in kb_list:
            if not each:
                continue

            kb_name = self.__get_kb_name(each)
            kb_detail = self.__get_kb_details(kb_name, each)
            self.__info_db[kb_name] = kb_detail

    def __get_kb_name(self, url):
            url_parts = url.split("/")
            return "-".join(url_parts[len(url_parts) - 2:]).upper()

    def __get_kb_details(self, kb, url):
        kb = KBDetails(kb, url, self.__os_map)
        return kb.get_details()

    def __get_html_ele(self, ele, tag_name):
        if ele is None:
            return

        if ele.tag in [tag_name]:
            return ele

        children = ele.getchildren()

        for each in children:
            tag = self.__get_html_ele(each, tag_name)

            if tag is None:
                continue
            else:
                return tag

    def __get_header(self, html):
        header = self.__get_html_ele(self.\
                                     __get_html_ele(self.\
                                     __get_html_ele(self.\
                                     __get_html_ele(html, 'body'), \
                                      'article'), "hgroup"), "h2")

        if header is not None:
            return header.text_content()
        return ""

    def __get_title(self):
        bulletin = fromstring(self.__content)
        header = self.__get_header(bulletin)
        header = str(header).split(" ")
        header = [each for each in header if not each.\
              startswith("(") and not each.endswith(")")]
        header = " ".join(header) + " - " + self.__bulletin
        return header

    def __get_description(self):
        string = "The host is missing a critical security " +\
        "update according to Microsoft bulletin, %s." % (self.__bulletin)
        return string

    def __get_affected_platform_info(self):
        block = self.__get_affected_file_detail()
        return block

    def __get_tables(self, html):
        tables = []

        if html is None:
            return

        if html.tag in ['table']:
            return [html]

        for each in html.getchildren():
            table = self.__get_tables(each)

            if table:
                tables.extend(table)

        return tables

    def __is_info_table_v(self, tb):

        info_list = False

        if not tb:
            return False

        for each in tb:
            if len(each) == 0:
                continue
            if len(each) != 2:
                return
            if self.__get_text(each[0]).__contains__("File Information"):
                info_list = []
                for link in each[1].findall('a'):
                    info_list.append(link.get('href'))

        return info_list

    def __get_rows(self, ele):
        if ele.tag not in ['table']:
            return None

        tbody = self.__get_html_ele(ele, 'tbody')
        thead = self.__get_html_ele(ele, 'thead')
        rows = []

        if ele is not None:
            rows.extend(ele.findall('tr'))
        if len(rows) <= 0:
            if thead is not None:
                rows.extend(thead.findall('tr'))
            if tbody is not None:
                rows.extend(tbody.findall('tr'))

        rows = [self.__get_columns(each) for each in rows]
        return [each for each in rows if each]

    def __get_columns(self, ele):
        if ele is None or ele.tag not in ['tr', 'th']:
            return []

        column = ele.findall('td')

        if not column:
            column = ele.findall('th')

        return column
        #return [self.__get_text(each) for each in column]

    def __get_text(self, ele):
        return ele.text_content()

    def __get_affected_file_detail(self):
        os_file_detail = []
        tables = self.__get_tables(fromstring(self.__content))

        for each in tables:
            tb = self.__get_rows(each)

            file_info_list = self.__is_info_table_v(tb)

            if file_info_list:
                os_file_detail.extend(file_info_list)
            else:
                self.__get_affected_os_list(tb)

        return list(set(os_file_detail))

    def __get_affected_os_list(self, tb):
        flag = False

        for each in tb:
            if not each:
                continue

            if not flag and len(each) < 4:
                return

            if self.__get_text(each[0]).__contains__("Operating System"):
                flag = True
                continue

            if flag:
                self.__affected_os.extend([i.text_content() for i in each[0].\
                                                             findall("a")])

    def __get_os(self, string):
        os = ""

        for each in self.__affected_os:
            if self.__is_matching(each.lower(), string.lower()):
                os = each

        return os

    def __is_matching(self, os1, os2):
        discard_list = set(['for', '-based', 'based', 'systems',
                        'service', 'pack', '1', '2', '3', '4', '5'])
        os_parts = set(os1.split(" "))
        os_parts = os_parts.difference(discard_list)

        for each in os_parts:
            if not os2.__contains__(each):
                return False

        return True

    def __save_page(self):
        page = urllib.urlopen(self.__url)
        self.__content = page.read().decode('utf-8').encode('utf-8')
        f = open(self.__filename, "w")
        f.write(self.__content)
        f.close()

    def __read_page(self):
        import os

        if not os.path.isfile(self.__filename):
            self.__save_page()
        else:
            self.__content = open(self.__filename).read()

    def __create_db(self):
        self.__collect_details()


def main():
    inf = INFOBank("http://technet.microsoft.com/en-us" +
                   "/security/bulletin/ms12-024", "MS12-024")
    inf.get_info_db()

if __name__ == "__main__":
    main()

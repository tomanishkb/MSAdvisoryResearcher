import urllib
from lxml.html import fromstring

KB_SECTION = "kb_section"


class KBDetails (object):
    def __init__(self, kb, url, os):
        """Constructor initialize the kb number, knowledge base url
        and the affected operating system map"""
        #kb=KB-2660465
        #url= http://support.microsoft.com/kb/2660465
        #os = {'Windows Vista':
        #                        {'x86':
        #                                {'sp2':
        #                                 {}
        #                                 },
        #                         'x64': {'sp2':
        #                                 {}
        #                                 }
        #                         },
        #       'Windows XP':
        #                          {'x86':
        #                                {'sp3':
        #                                 {}
        #                                 },
        #                           'x64':
        #                                {'sp2':
        #                                 {}
        #                                 }
        #                           },
        #    }
        self.__url = url
        self.__content = ""
        self.__filename = "html/" + kb + ".html"
        self.__kb_info = {}
        self.__os = os

    def get_details(self):
        """returns kb info map for each of the affected os"""
        self.__read_page()
        self.__parse_kb()
        return self.__kb_info

    def __parse_kb(self):
        """Function parse the knowledge base html page and
        collect the file details of affected operating system."""
        kb = fromstring(self.__content)
        file_info = self.__get_file_info_section(kb)

        if file_info is None:
            print "Parsing failed ", self.__url, __name__
            return

        self.__kb_info = self.__get_file_dict(file_info)

    def __get_file_dict(self, div):
        """Function accepts lxml html element
        returns the file info map of affected operating systems."""
        if div is None:
            print "Parsing failed ", self.__url, __name__
            return

        groups = self.__group_children(div.getchildren())
        os_file_map = self.__convert_to_os_map(groups)
        os_arch_file_map = self.__convert_to_arch_map(os_file_map)
        return os_arch_file_map

    def __convert_to_arch_map(self, os_file_map):
        """Function accepts a dictionary containing key as operating
        system names and value as a list containing html elements
        holding file information.
        Returns a complete categorized file info map by further parsing the
        html elements"""
        arch_file_map = []

        for each in os_file_map:
            os_map = {}
            arch_map = self.__get_arch_map(os_file_map[each], each)

            if arch_map:
                os_map['osdetails'] = arch_map
                os_map['operatingsystem'] = each
                arch_file_map.append(os_map)

        return arch_file_map

    def __get_arch_map(self, file_map, os):
        """Function accepts """
        ldr_gdr_div = self.__get_ldr_gdr(file_map)
        groups = self.__get_groups(file_map)
        groups = self.\
        __remove_invalid_entries_and_retrieve_arch_map(groups, os)
        groups = self.__mile_stone_grouping(groups, ldr_gdr_div, self.__os[os])
        return groups

    def __mile_stone_grouping(self, group, ldr_gdr_div, default):
        arch_info_map = {}
        for each in group:
            arch_info_map[each] = self.__get_mile_stone_map(group[each], \
                                        ldr_gdr_div, each, default[each])

        return arch_info_map

    def __get_index(self, row, value):
        """Function accepts a list and a string
        Returns None if string is not present inside the list
        Returns index of the first appearance of the string inside the list
        """
        for index in range(len(row)):
            if row[index].lower().__contains__(value):
                return index

    def __get_file_index(self, header):
        return self.__get_index(header, "file name")

    def __get_version_index(self, header):
        return self.__get_index(header, "version")

    def __get_arch_index(self, header):
        return self.__get_index(header, "platform")

    def __get_mile_stone_index(self, header):
        return self.__get_index(header, "sp requirement")

    def __get_branch_index(self, header):
        return self.__get_index(header, "service branch")

    def __get_branch_corrected(self, branch):
        if branch.lower().__contains__('qfe'):
            return 'QFE'
        if branch.lower().__contains__('ldr'):
            return 'LDR'
        if branch.lower().__contains__('gdr'):
            return 'GDR'
        return branch.replace(" ", "_")

    def __get_map(self, file_ptr, version_ptr, arch_mtr, milestone_ptr, \
                                                branch_ptr, arch, rows):
        """
         Returns map which holds archtecture and service pack and ldr gdr
        info and file info
        """
        file_map = {}

        for each in rows:
            local_arch = each[arch_mtr]
            milestone = each[milestone_ptr]
            branch = self.__get_branch_corrected(each[branch_ptr])
            file_name = each[file_ptr]
            version = each[version_ptr]

            #if not local_arch == arch:
            #    continue

            if milestone not in file_map:
                file_map[milestone] = {}

            if branch not in file_map[milestone]:
                file_map[milestone][branch] = {file_name: version}
            else:
                file_map[milestone][branch].update({file_name: version})

        #return value
        #{architecture:
        #    {service pack:
        #        {ldr gdr info:
        #            {filename:
        #                fileversion
        #            }
        #        }
        #    }
        return file_map

    def __is_pattern_matching(self, pattern, version):
        pattern = pattern.lower()
        version = version.lower()

        while pattern.find("x") >= 0:
            pattern = pattern.replace("x", "0")

        return int(version) >= int(pattern)

    def __is_matching(self, version, pattern):
        version = version.split(".")
        pattern = pattern.split(".")

        if len(version) != len(pattern):
            return False

        for index in range(len(version)):
            if version[index] != pattern[index] and index != 0:
                if index + 1 == len(version) and self.\
                   __is_pattern_matching(pattern[index], version[index]):
                    continue
                else:
                    return False
        return True

    def __get_mile_stone_and_branch_from_version(self, version, pattern):
        for mile_stone in pattern:
            for branch in pattern[mile_stone]:
                if self.__is_matching(version, pattern[mile_stone][branch]):
                    return (mile_stone, branch)

    def __get_map_by_pattern(self, file_ptr, version_ptr, arch_ptr, \
                         arch, default_milestone, rows, pattern_map):
        """
         Returns map which holds archtecture and service pack and ldr gdr
        info and file info
        """
        file_map = {}

        for each in rows:
            local_arch = each[arch_ptr]
            file_name = each[file_ptr]
            version = each[version_ptr]
            milestone = self.\
              __get_mile_stone_and_branch_from_version(version, pattern_map)

            if not milestone or len(milestone) != 2:
                continue

            branch = milestone[1]
            milestone = milestone[0]

            #if not local_arch == arch:
            #    continue

            if milestone not in file_map:
                file_map[milestone] = {}

            if branch not in file_map[milestone]:
                file_map[milestone][branch] = {file_name: version}
            else:
                file_map[milestone][branch].update({file_name: version})

        #return value
        #{architecture:
        #    {service pack:
        #        {ldr gdr info:
        #            {filename:
        #                fileversion
        #            }
        #        }
        #    }
        return file_map

    def __get_mile_stone_map(self, group, ldr_gdr_div, arch, default):
        """
        Function accepts list of lists which holds file info, lxml html
        element which holds ldr gdr info, string containing the
        architecture, string containing the service pack
        Returns map which holds archtecture and service pack and ldr gdr
        info and file info
        """
        mile_stone_map = {}
        pattern_map = self.__get_mile_stone_pattern(ldr_gdr_div)

        f_index = self.__get_file_index(group[0])
        v_index = self.__get_version_index(group[0])
        a_index = self.__get_arch_index(group[0])
        m_index = self.__get_mile_stone_index(group[0])
        b_index = self.__get_branch_index(group[0])

        if not (a_index or f_index or v_index):
            return mile_stone_map

        if m_index and b_index:
            return self.__get_map(f_index, v_index, a_index, \
                           m_index, b_index, arch, group[1:])
        else:
            return self.__get_map_by_pattern(f_index, v_index, a_index, \
                                  arch, default, group[1:], pattern_map)

        #return value
        #{architecture:
        #    {service pack:
        #        {ldr gdr info:
        #            {filename:
        #                fileversion
        #            }
        #        }
        #    }

    def __get_mile_stone_pattern(self, div):
        """Accepts an lxml html element which containing ldr gdr info
        Returns a dictionary of dictionaries, inside dictonary contains
        key as the ldr, gdr, qfe branch and value as its version pattern
        outer dictionary has key as the service pack.
        """
        tb = self.__get_table(div)
        version_index = 0
        mile_stone_index = 0
        branch_index = 0
        pattern_map = {}

        if not tb:
            return

        header = tb[0]
        tb = tb[1:]

        for index in range(len(header)):
            if header[index].lower() == 'version':
                version_index = index
            elif header[index].lower() == 'milestone':
                mile_stone_index = index
            elif header[index].lower() == 'service branch':
                branch_index = index

        for row in tb:
            if row[mile_stone_index] not in pattern_map:
                pattern_map[row[mile_stone_index]] = {}
            pattern_map[row[mile_stone_index]][row[branch_index]] = \
                                                  row[version_index]

        return pattern_map

    def __get_ldr_gdr(self, file_map):
        """Function accepts a list of lxml html elements
        Returns an lxml html element which holds ul tag.
        """
        for each in file_map:
            if each.tag in ['ul']:
                return each

    def __remove_invalid_entries_and_retrieve_arch_map(self, groups, os):
        """Function accepts a list of lists (where inside list holds
        information about operating system such as os name, service pack,
        ldr gdr version pattern, affected file versions) and a string which
        holds an operating system.
        Returns a map which holds information about the os name give through
        the second parameter. In the map, key will be the affected
        architecture, values will be a list of lists of lists
        which holds the file version info.
        """
        arch_map = {}

        for each in groups:
            if not (len(each) == 2 and each[0].tag in ['h4']):
                print 'table parsing failed for subheader h4'
                continue

            if self.__is_os_present(os, each[0].text_content()):
                arch = self.__get_arch(each[0].text_content())

                if not arch:
                    arch = "x86"

                if arch in arch_map:
                    print "architecture parsing error h4"
                    continue

                info_tab = self.__get_table(each[1])

                if not info_tab:
                    print "version info table parsing error <table> ", \
                                               each[1].text_content()
                    continue

                arch_map.update({arch: info_tab})

        return arch_map

    def __is_os_present(self, os_name, string_part):
        """Function accepts two string inputs in which the first one is
        a complete operating system name and 2nd one is a string from
        the kb html.
        Returns true or false based on the presence of operating system
        name in the second string
        """
        flag = False

        if os_name.lower() == "windows server 2008":
            if string_part.lower().replace("windows server 2008 r2", "").\
                                            __contains__(os_name.lower()):
                flag = True
        elif string_part.lower().__contains__(os_name.lower()):
            flag = True

        return flag

    def __get_groups(self, file_map):
        """Function accepts a list of html elements, which conatining
        information about operating system, service pack, architecture
        and file information LDR GDR version pattern etc.
        Returns a list of list in which inside list contains information about
        one operating system such as os name, service pack info, architecture
        info, file info ldr gdr file version pattern.
        """
        groups = []
        group = []

        for each in file_map:
            if each.tag in ['h4']:
                if group:
                    groups.append(group)
                group = []
                group.append(each)
            elif group and len(group) < 2 and each.tag in ['div']:
                group.append(each)
        else:
            if group:
                groups.append(group)

        return groups

    def __convert_to_os_map(self, groups):
        """Function accepts a list of lists, inside lists contains
        html elements that holds file information to a specific
        operating system or operating systems.
        Returns a dictionary where key will be the operating system name
        and value will be a list containing html elements which holds file
        info"""
        os_map = {}

        for each in groups:
            os_name_map = self.__get_os_name_map(each)

            if os_name_map:
                os_map.update(os_name_map)

        return os_map

    def __get_os_name_map(self, group):
        """Function accepts a list which containing a group of html
         elements, first elemet is supposed have operating system name,
         and which is an html header. All other elements are holding
         file information."""
        #Current logic is based on the fact all h3 headers are supposed to
        #contain operating system name.
        if len(group) <= 1:
            return None

        os_names = self.__get_os(group[0].text_content())

        if os_names:
            name_map = {}

            for each_os in os_names:
                name_map.update({each_os: group[1:]})

            return name_map

    def __get_os(self, heading):
        """Function accepts a heading text from kb html, which holds
        operating system name or operating system names.
        Returns a list containing the exact operating system names.
        """
        os_list = []

        for each in self.__os.keys():
            if heading and heading.lower().endswith("file information") and \
               heading.lower().__contains__(each.lower()):
                if each.lower() == "windows server 2008":
                    if heading.lower().replace("windows server 2008 r2", "")\
                                        .__contains__("windows server 2008"):
                        os_list.append(each)
                else:
                    os_list.append(each)

        return os_list

    def __group_children(self, child_list):
        """Accepts a list of lxml html elements.
        returns a list of list in which inside list contains
        child elements of Operating system file info"""
        groups = []
        group = []

        for each in child_list:
            if each.tag in ['h3']:
                if group:
                    groups.append(group)
                group = []
                group.append(each)
            elif group:
                group.append(each)

        return groups

    def __get_table(self, ele):
        """Function accepts an lxml html element
        Returns None if the given element doesn't contain a table
        Returns a list of list of list, in which inside list holds
        the column values.
        """
        if ele.tag in ['table']:
            return self.__get_rows(ele)

        for each in ele.getchildren():
            table = self.__get_table(each)

            if table:
                return table

    def __get_rows(self, ele):
        """Function accepts an lxml html element
        Returns None if the given element is not table
        Returns a list of list, in which inside list holds
        the column values."""
        if ele is None or ele.tag not in ['table']:
            return None

        tbody = ele.findall('tbody')
        if tbody is not None and len(tbody) == 1:
            tbody = tbody[0]

        thead = ele.findall('thead')
        if thead is not None and len(thead) == 1:
            thead = thead[0]

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
        """Function accepts an lxml html element
        Returns None if the given element is not table row
        Returns a list of string, which represent the column values."""
        if ele is not None and ele.tag not in ['tr']:
            return None

        column = ele.findall('td')
        if not column:
            column = ele.findall('th')

        return [self.__get_text(each) for each in column]

    def __get_text(self, ele):
        """Function accepts an lxml html element and
        returns its text content"""
        return ele.text_content()

    def __get_arch(self, heading):
        """Function accepts a string (file info header<h4>) and returns
        the platform mentioned inside the header"""
        if heading.__contains__("x64") or \
           heading.__contains__("64-bit"):
            return "x64"
        if heading.__contains__("x86") or \
           heading.__contains__("32-bit"):
            return "x86"
        if heading.__contains__("IA-64") or \
           heading.__contains__("Itanium"):
            return "IA-64"

    def __get_file_info_section(self, kb):
        """Function accepts ms bulletin root element of
        knowledge base. and returns the child element which
        holds the file information."""
        section = kb.get_element_by_id(KB_SECTION)
        flag = False

        for each in section:
            if flag and each.get("class") in ["sbody"]:
                return each
            if each.text_content() in ["FILE INFORMATION"]:
                flag = True

    def __save_page(self):
        """Function reads the kb url and save the corresponding html in
        the standard path"""
        page = urllib.urlopen(self.__url)
        self.__content = page.read()

        f = open(self.__filename, "w")
        f.write(self.__content)
        f.close()

    def __read_page(self):
        """Function save the knowledge base html and reads the content."""
        import os

        if not os.path.isfile(self.__filename):
            self.__save_page()
        else:
            self.__content = open(self.__filename).read()


def main():
    a = {'Windows Vista': {'x86': {'sp2': {}}, 'x64': {'sp2': {}}}, \
         'Windows XP': {'x86': {'sp3': {}}, 'x64': {'sp2': {}}}, \
         'Windows Server 2003': {'IA-64': {'sp2': {}}, 'x86': {'sp2': {}}, \
         'x64': {'sp2': {}}}, 'Windows 7': {'x86': {'sp1': {}}, \
         'x64': {'sp1': {}}}, 'Windows Server 2008': {'IA-64': {'sp2': {}}, \
         'x86': {'sp2': {}}, 'x64': {'sp2': {}}}, 'Windows Server 2008 R2': \
         {'IA-64': {'sp1': {}}, 'x64': {'sp1': {}}}}
    kb = KBDetails("KB-2660465", "http://support.microsoft.com/kb/2660465", a)
    details = kb.get_details()
    print details

if __name__ == "__main__":
    main()

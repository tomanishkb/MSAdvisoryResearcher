__base_path = "research/"


def create_research_dir():
    import os
    os.system("mkdir -p " + __base_path)
    del(os)


def main():
    research()


def prepare_report():
    from MSInitializer import MSDEF
    ms = MSDEF("mar", "12")
    bulletin_map = ms.get_advisory_link_map()
    report_map = {}

    for each in bulletin_map:
        create_research_dir()
        report_map[each] = get_report(each, bulletin_map[each])
        create_report(report_map[each], each)

    return report_map


def create_report(bulletin_reports, file_name):
    from xmldict import dict_to_xml
    xml = dict_to_xml({file_name: bulletin_reports})
    f_ptr = open(__base_path + file_name + ".xml", "w")
    f_ptr.write(xml)
    f_ptr.close()


def research():
    from import_check import check_researcher_imports

    if not check_researcher_imports():
        return
    prepare_report()


def get_report(bulletin, url):
    from Info import INFOBank as Info
    info = Info(url, bulletin)
    return info.get_info_db()

if __name__ == "__main__":
    main()

def check_import(module_name):
    """Accepts a python module name(String)
       Return true or false based on the module's availability."""

    print "Checking for python modle " + module_name
    try:
        exec "import " + module_name
    except ImportError:
        print "Python module " + module_name + "is missing"
        return try_install(module_name)

    print "Python module " + module_name + " is present on the system"
    return True


def check_cmd(cmd):
    """Accepts a linux command name(String)
       Return true or false based on the command's availability."""
    import commands

    print "Checking for command " + cmd
    if commands.getoutput(cmd).__contains__("command not found"):
        return try_install_easy_install(cmd)

    return True


def try_install_easy_install(cmd):
    """Accepts a linux command name(String)
       Tries to install the command."""
    import os
    import commands
    print "Trying to install command " + cmd

    os.system('wget http://peak.telecommunity.com/dist/ez_setup.py')
    os.system('python ez_setup.py')
    os.system("rm ez_setup.py")

    if commands.getoutput(cmd).__contains__("command not found"):
        return False


def try_install(module):
    """Accepts a python module name(String)
       Function try to install that python module through easy_install
       Return true or false based on the module's install status."""
    import os

    if check_cmd("easy_install"):
        print "Trying to install python module " + module
        os.system('sudo easy_install ' + module)
    else:
        return False

    del(os)
    return True


def check_researcher_imports():
    """Function returns true or false based on the availability of
    python modules required for ms researcher to execute"""
    print "#" * 80
    print "#Checking for python module dependency." + " " * (80 - 40) + "#"
    print "#" * 80
    module_list = ['StringIO',
                   'lxml',
                   'urllib',
                   're',
                   'configobj',
                   'datetime']

    for each in module_list:
        if not check_import(each):
            return False

    print "#" * 80
    print "# All required modules are present." + " " * (80 - 36) + "#"
    print "#" * 80
    print
    return True


def main():
    check_import('xmldict')

if __name__ == "__main__":
    main()

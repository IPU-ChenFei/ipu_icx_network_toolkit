import argparse
import copy
import os

from configparser import ConfigParser
from xml.dom import minidom

event_template = (
    {
        'case_name': 'AddEnvPath',
        'argument': r'src\collateral_scripts\_utils\set_cc_env.py'
    },
    {
        'case_name': 'AddVirtualEnvPath',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\set_cc_env.py'
    },
    {
        'case_name': 'ClearCMOS',
        'argument': r'test\toolkit\infra\test_infra_sut_clear_cmos.py'
    },
    {
        'case_name': 'KillSimics',
        'argument': r'src\collateral_scripts\_utils\kill_simics.py'
    },
    {
        'case_name': 'Switch_to_redhat',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=sut.ini --sut1_os=redhat'
    },
    {
        'case_name': 'Switch_to_win',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=sut.ini --sut1_os=windows'
    },
    {
        'case_name': 'Switch_to_centos',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=sut.ini --sut1_os=centos'
    },
    {
        'case_name': 'Switch_to_vmware',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=sut.ini --sut1_os=vmware'
    },

    {
        'case_name': 'Switch_2sut_default_os_to_linux',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=C:\automation\tkconfig\sut\network_server.ini --sut=C:\automation\tkconfig\sut\network_client.ini --sut1_os=redhat --sut2_os=redhat'
    },
    {
        'case_name': 'Switch_2sut_default_os_to_win',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=C:\automation\tkconfig\sut\network_server.ini --sut=C:\automation\tkconfig\sut\network_client.ini --sut1_os=windows --sut2_os=windows'
    },
    {
        'case_name': 'Switch_2sut_default_os_to_centos',
        'argument': r'src\collateral_scripts\_utils\switch_sut_default_os_dtaf.py --sut=C:\automation\tkconfig\sut\network_server.ini --sut=C:\automation\tkconfig\sut\network_client.ini --sut1_os=centos --sut2_os=centos'
    },
)


class ModifiedParser(ConfigParser):
    def __init__(self):
        super().__init__(allow_no_value=True, delimiters=(' ',))

    def optionxform(self, optionstr):
        return optionstr

    def parser(self):
        assert (isinstance(self, ConfigParser))
        d = {}
        for sec in self.sections():
            d2 = {}
            for op in self.options(sec):
                d2[op] = self.get(sec, op)
            d[sec] = copy.deepcopy(d2)
        return d


def xml_header():
    dom = minidom.getDOMImplementation().createDocument(None, "TestCases", None)
    # Create Header nodes
    root = dom.documentElement
    dom.appendChild(root)

    global_prop_node = dom.createElement("GlobalProperties")
    root.appendChild(global_prop_node)

    cmd_node = dom.createElement("Command")
    cmd_text = dom.createTextNode("python")
    cmd_node.appendChild(cmd_text)

    pass_node = dom.createElement("PassOutputPathAsParameter")
    pass_text = dom.createTextNode("true")
    pass_node.appendChild(pass_text)

    global_prop_node.appendChild(cmd_node)
    global_prop_node.appendChild(pass_node)

    return dom, root


def generate_events():
    for event in event_template:
        # TestCase Node
        test_node = dom_obj.createElement("TestCase")
        xml_root.appendChild(test_node)

        # Package Name
        pkg_node = dom_obj.createElement("PackageName")
        pkg_text = dom_obj.createTextNode("Event")
        pkg_node.appendChild(pkg_text)
        # TestCaseName
        name_node = dom_obj.createElement("TestCaseName")
        name_text = dom_obj.createTextNode(event.get('case_name'))
        name_node.appendChild(name_text)
        # Arguments
        arg_node = dom_obj.createElement("Arguments")
        arg_text = dom_obj.createTextNode(event.get('argument'))
        arg_node.appendChild(arg_text)
        # isEvent
        event_node = dom_obj.createElement("IsEvent")
        event_text = dom_obj.createTextNode("true")
        event_node.appendChild(event_text)

        test_node.appendChild(pkg_node)
        test_node.appendChild(name_node)
        test_node.appendChild(arg_node)
        test_node.appendChild(event_node)


def generate_system_test_case(root_dir):
    system_test_dir = os.path.join(root_dir, "test", "toolkit")
    infra_dir = os.path.join(system_test_dir, "infra")
    steps_lib_dir = os.path.join(system_test_dir, "steps_lib")

    # loop system test case
    for system_test_case_dir in (infra_dir, steps_lib_dir):
        for entry in os.scandir(system_test_case_dir):
            if entry.name.startswith("test_") and entry.name.endswith(".py"):
                # TestCase Node
                test_node = dom_obj.createElement("TestCase")
                xml_root.appendChild(test_node)

                # Package Name
                pkg_node = dom_obj.createElement("PackageName")
                pkg_text = dom_obj.createTextNode("system_test")
                pkg_node.appendChild(pkg_text)
                # TestCaseName
                name_node = dom_obj.createElement("TestCaseName")
                name_text = dom_obj.createTextNode(entry.name.replace('.py', ''))
                name_node.appendChild(name_text)
                # Arguments
                arg_node = dom_obj.createElement("Arguments")
                src_path = entry.path.replace(root_dir + '\\', '')
                arg_text = dom_obj.createTextNode(src_path)
                arg_node.appendChild(arg_text)
                # isEvent
                event_node = dom_obj.createElement("IsEvent")
                event_text = dom_obj.createTextNode("false")
                event_node.appendChild(event_text)

                test_node.appendChild(pkg_node)
                test_node.appendChild(name_node)
                test_node.appendChild(arg_node)
                test_node.appendChild(event_node)


def generate_domain_test_case(domain_name, test_name_with_title):
    for os_key in parsed_domain_plan:
        for case_name, case_params in parsed_domain_plan[os_key].items():
            # TestCase Node
            test_node = dom_obj.createElement("TestCase")

            # Package Name
            pkg_node = dom_obj.createElement("PackageName")
            package_name = domain_name.upper() + '_' + os_key
            pkg_text = dom_obj.createTextNode(package_name)
            pkg_node.appendChild(pkg_text)

            # TestCaseName
            name_node = dom_obj.createElement("TestCaseName")
            if test_name_with_title == "True":
                case_name_without_extension = os_key + "-" + case_name.replace('.py', '')
            else:
                case_name_without_extension = case_name.replace('.py', '')
            # modify case name for Linux series cases which reuse one case template
            # e.g. _R for Redhat, _C for CentOS
            if case_name_without_extension.endswith("L"):
                case_name_without_extension = case_name_without_extension + '_' + os_key
            name_text = dom_obj.createTextNode(case_name_without_extension)
            name_node.appendChild(name_text)

            # Arguments
            arg_node = dom_obj.createElement("Arguments")
            arg = os.path.join(f"src\\{domain_name}\\tests", case_name)
            if case_params is not None:
                arg = arg + " " + case_params
            arg_text = dom_obj.createTextNode(arg)
            arg_node.appendChild(arg_text)

            # isEvent
            event_node = dom_obj.createElement("IsEvent")
            event_text = dom_obj.createTextNode("false")
            event_node.appendChild(event_text)

            test_node.appendChild(pkg_node)
            test_node.appendChild(name_node)
            test_node.appendChild(arg_node)
            test_node.appendChild(event_node)

            xml_root.appendChild(test_node)

def generate_simics_test_case(root_dir):
    system_test_dir = os.path.join(root_dir, "test", "toolkit")
    simics_dir = os.path.join(system_test_dir, "simics")

    for entry in os.scandir(simics_dir):
        if entry.name.startswith('test_') and entry.name.endswith('.py'):
            # TestCase Node
            test_node = dom_obj.createElement("TestCase")
            xml_root.appendChild(test_node)

            # Package Name
            pkg_node = dom_obj.createElement("PackageName")
            pkg_text = dom_obj.createTextNode("simics_test")
            pkg_node.appendChild(pkg_text)
            # TestCase Name
            name_node = dom_obj.createElement("TestCaseName")
            name_text = dom_obj.createTextNode(entry.name.replace('.py', ''))
            name_node.appendChild(name_text)
            # Arguments
            arg_node = dom_obj.createElement("Arguments")
            src_path = entry.path.replace(root_dir + '\\', '')
            arg_text = dom_obj.createTextNode(src_path)
            arg_node.appendChild(arg_text)
            # isEvent
            event_node = dom_obj.createElement("IsEvent")
            event_text = dom_obj.createTextNode("false")
            event_node.appendChild(event_text)

            test_node.appendChild(pkg_node)
            test_node.appendChild(name_node)
            test_node.appendChild(arg_node)
            test_node.appendChild(event_node)


def get_parser():
    parser = argparse.ArgumentParser(description="arg support for make_cc_plans")
    parser.add_argument('--plan', type=str, default="network_bhs.ini", help="set path of testplan file")
    parser.add_argument('--domain', type=str, default="network", help="domain name")
    parser.add_argument('--target', type=str, default="postsilicon", help="presilicon/postsilicon[default]")
    parser.add_argument('--test_name_with_title', type=str, default=False, help="test-name-with-title")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # configuration
    # folder name under src folder
    # domain_name = "network_bhs"
    # ini file must exist under automation_testcases folder
    # test_plan_name = "network_bhs.ini"
    args = get_parser()
    src_dir = os.path.dirname(os.path.dirname(os.path.split(os.path.realpath(__file__))[0]))
    root_dir = os.path.dirname(src_dir)
    with open(os.path.join(root_dir, 'automation_testcases', args.plan)) as f:
        text_list = f.readlines()
        if args.target == 'presilicon':
            for x in text_list:
                if x.startswith("#") and "simics" in x:
                    simics_args = x.split(":")[1].strip()
                    text_list[text_list.index(x) + 1] = text_list[text_list.index(x) + 1].replace("\n",
                                                                                                  "") + " " + simics_args + "\n"
                    text_list.remove(x)

    with open(os.path.join(root_dir, 'automation_testcases', args.plan + "_del"), "w+") as f:
        for x in text_list:
            f.write(x)

    parser = ModifiedParser()
    parser.read(os.path.join(root_dir, 'automation_testcases', args.plan + "_del"))
    parsed_domain_plan = parser.parser()

    # create dom header
    dom_obj, xml_root = xml_header()

    # generate events
    generate_events()

    # generate system test case
    #generate_system_test_case(root_dir)
    
    # generate simics test case
    #generate_simics_test_case(root_dir)

    # generate domain test case
    generate_domain_test_case(args.domain, args.test_name_with_title)

    # write xml content to file
    xml_file_path = os.path.join(root_dir, 'testCases_dtaf.xml')
    try:
        with open(xml_file_path, 'w', encoding='UTF-8') as fs:
            dom_obj.writexml(fs, indent='', addindent='\t', newl='\n', encoding='UTF-8')
    except Exception as ex:
        raise ex

    os.remove(os.path.join(root_dir, 'automation_testcases', args.plan + "_del"))

import copy
import os
import re

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
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\kill_simics_dtaf.py'
    },
    {
        'case_name': 'Simics_switch_to_centos',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_os_switch.py --new_os=centos'
    },
    {
        'case_name': 'Simics_switch_to_windows',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_os_switch.py --new_os=windows'
    },
    {
        'case_name': 'Simics_switch_to_vmware',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_os_switch.py --new_os=vmware'
    },
    {
        'case_name': 'Simics_ms_switch_topology_full_1',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Fully_Connected_1'
    },
    {
        'case_name': 'Simics_ms_switch_topology_full_2',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Fully_Connected_2'
    },
    {
        'case_name': 'Simics_ms_switch_topology_full_3',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Fully_Connected_3'
    },
    {
        'case_name': 'Simics_ms_switch_topology_full_4',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Fully_Connected_4'
    },
    {
        'case_name': 'Simics_ms_switch_topology_full_5',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Fully_Connected_5'
    },
    {
        'case_name': 'Simics_ms_switch_topology_ring_1',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Ring_1'
    },
    {
        'case_name': 'Simics_ms_switch_topology_ring_2',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Ring_2'
    },
    {
        'case_name': 'Simics_ms_switch_topology_ring_3',
        'command': 'dflaunch',
        'argument': r'src\collateral_scripts\_utils\simics_multisocket_topology_switch.py --topology=TOPOLOGY_4S_Ring_3'
    },
    {
        'case_name': 'Switch_to_redhat',
        'argument': r'src\collateral_scripts\_utils\switch_default_boot_os.py --new_boot_os=redhat'
    },
    {
        'case_name': 'Switch_to_win',
        'argument': r'src\collateral_scripts\_utils\switch_default_boot_os.py --new_boot_os=windows'
    },
    {
        'case_name': 'Switch_to_centos',
        'argument': r'src\collateral_scripts\_utils\switch_default_boot_os.py --new_boot_os=centos'
    },
    {
        'case_name': 'Switch_to_vmware',
        'argument': r'src\collateral_scripts\_utils\switch_default_boot_os.py --new_boot_os=vmware'
    },
    {
        'case_name': 'Switch_2sut_default_os_to_linux',
        'argument': r'src\steps_lib\domains\network\env\switch_2sut_default_os.py --sut=src\steps_lib\domains\network\sut1.ini --sut=src\steps_lib\domains\network\sut2.ini --sut1_os=rhel --sut2_os=rhel'
    },
    {
        'case_name': 'Switch_2sut_default_os_to_win',
        'argument': r'src\steps_lib\domains\network\env\switch_2sut_default_os.py --sut=src\steps_lib\domains\network\sut1.ini --sut=src\steps_lib\domains\network\sut2.ini --sut1_os=windows --sut2_os=windows'
    },
    {
        'case_name': 'Switch_2sut_default_os_to_centos',
        'argument': r'src\steps_lib\domains\network\env\switch_2sut_default_os.py --sut=src\steps_lib\domains\network\sut1.ini --sut=src\steps_lib\domains\network\sut2.ini --sut1_os=centos --sut2_os=centos'
    },
)


def get_domain_name_from_file_name(file_name):
    start_index = file_name.find('[')
    end_index = file_name.find(']')
    if start_index == -1 or end_index == -1:
        return None

    return file_name[start_index + 1: end_index]


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


class TestCaseXmlGenerator:
    def __init__(self, root_path, src_path):
        self.root_path = root_path
        self.src_path = src_path
        self.dom_obj, self.xml_root = self.__xml_header()

    # generate xml file header
    def __xml_header(self):
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

    # generate events
    def generate_events(self):
        for event in event_template:
            # TestCase Node
            test_node = self.dom_obj.createElement("TestCase")
            self.xml_root.appendChild(test_node)

            # Package Name
            pkg_node = self.dom_obj.createElement("PackageName")
            pkg_text = self.dom_obj.createTextNode("Event")
            pkg_node.appendChild(pkg_text)
            test_node.appendChild(pkg_node)

            # TestCaseName
            name_node = self.dom_obj.createElement("TestCaseName")
            name_text = self.dom_obj.createTextNode(event.get('case_name'))
            name_node.appendChild(name_text)
            test_node.appendChild(name_node)

            # Command
            if 'command' in event.keys():
                command_node = self.dom_obj.createElement("Command")
                command_text = self.dom_obj.createTextNode(event.get('command'))
                command_node.appendChild(command_text)
                test_node.appendChild(command_node)

            # Arguments
            arg_node = self.dom_obj.createElement("Arguments")
            arg_text = self.dom_obj.createTextNode(event.get('argument'))
            arg_node.appendChild(arg_text)
            test_node.appendChild(arg_node)

            # isEvent
            event_node = self.dom_obj.createElement("IsEvent")
            event_text = self.dom_obj.createTextNode("true")
            event_node.appendChild(event_text)
            test_node.appendChild(event_node)

    # generate system test case
    def generate_system_test_case(self):
        system_test_dir = os.path.join(self.root_path, "test", "toolkit")
        infra_dir = os.path.join(system_test_dir, "infra")
        steps_lib_dir = os.path.join(system_test_dir, "steps_lib")

        # loop system test case
        for system_test_case_dir in (infra_dir, steps_lib_dir):
            for entry in os.scandir(system_test_case_dir):
                if entry.name.startswith("test_") and entry.name.endswith(".py"):
                    # TestCase Node
                    test_node = self.dom_obj.createElement("TestCase")
                    self.xml_root.appendChild(test_node)

                    # Package Name
                    pkg_node = self.dom_obj.createElement("PackageName")
                    pkg_text = self.dom_obj.createTextNode("system_test")
                    pkg_node.appendChild(pkg_text)
                    # TestCaseName
                    name_node = self.dom_obj.createElement("TestCaseName")
                    name_text = self.dom_obj.createTextNode(entry.name.replace('.py', ''))
                    name_node.appendChild(name_text)
                    # Arguments
                    arg_node = self.dom_obj.createElement("Arguments")
                    src_path = entry.path.replace(self.root_path + '\\', '')
                    arg_text = self.dom_obj.createTextNode(src_path)
                    arg_node.appendChild(arg_text)
                    # isEvent
                    event_node = self.dom_obj.createElement("IsEvent")
                    event_text = self.dom_obj.createTextNode("false")
                    event_node.appendChild(event_text)

                    test_node.appendChild(pkg_node)
                    test_node.appendChild(name_node)
                    test_node.appendChild(arg_node)
                    test_node.appendChild(event_node)

    # generate simics test case
    def generate_simics_test_case(self):
        system_test_dir = os.path.join(self.root_path, "test", "toolkit")
        simics_dir = os.path.join(system_test_dir, "simics")

        for entry in os.scandir(simics_dir):
            if entry.name.startswith('test_') and entry.name.endswith('.py'):
                # TestCase Node
                test_node = self.dom_obj.createElement("TestCase")
                self.xml_root.appendChild(test_node)

                # Package Name
                pkg_node = self.dom_obj.createElement("PackageName")
                pkg_text = self.dom_obj.createTextNode("simics_test")
                pkg_node.appendChild(pkg_text)
                # TestCase Name
                name_node = self.dom_obj.createElement("TestCaseName")
                name_text = self.dom_obj.createTextNode(entry.name.replace('.py', ''))
                name_node.appendChild(name_text)
                # Arguments
                arg_node = self.dom_obj.createElement("Arguments")
                src_path = entry.path.replace(self.root_path + '\\', '')
                arg_text = self.dom_obj.createTextNode(src_path)
                arg_node.appendChild(arg_text)
                # isEvent
                event_node = self.dom_obj.createElement("IsEvent")
                event_text = self.dom_obj.createTextNode("false")
                event_node.appendChild(event_text)

                test_node.appendChild(pkg_node)
                test_node.appendChild(name_node)
                test_node.appendChild(arg_node)
                test_node.appendChild(event_node)

    # generate domain test case
    def generate_domain_test_case(self, config_file):
        domain_name = get_domain_name_from_file_name(config_file)

        parser = ModifiedParser()
        parser.read(config_file)
        domain_plan_config = parser.parser()

        for os_key in domain_plan_config:
            for case_name, case_params in domain_plan_config[os_key].items():
                # TestCase Node
                test_node = self.dom_obj.createElement("TestCase")

                # Package Name
                pkg_node = self.dom_obj.createElement("PackageName")
                package_name = domain_name.upper() + '_' + os_key
                pkg_text = self.dom_obj.createTextNode(package_name)
                pkg_node.appendChild(pkg_text)

                # TestCaseName
                name_node = self.dom_obj.createElement("TestCaseName")
                if case_params is not None and re.search(r'--case_name=\S+', case_params):
                    given_case_name = re.search(r'--case_name=(\S+)', case_params).group(1)
                    name_text = self.dom_obj.createTextNode(given_case_name)
                    case_params = re.sub(r'--case_name=\S+', '', case_params)
                else:
                    case_name_without_extension = case_name.replace('.py', '')
                    # modify case name for Linux series cases which reuse one case template
                    # e.g. _R for Redhat, _C for CentOS
                    if case_name_without_extension.endswith("L"):
                        case_name_without_extension = case_name_without_extension + '_' + os_key
                    name_text = self.dom_obj.createTextNode(case_name_without_extension)
                name_node.appendChild(name_text)

                # Command
                if case_params is not None and '--cscript=true' in case_params:
                    command_node = self.dom_obj.createElement("Command")
                    command_node.appendChild(self.dom_obj.createTextNode('dflaunch'))
                    case_params = re.sub(r'--cscript=true', '', case_params)
                else:
                    command_node = None

                # Arguments
                arg_node = self.dom_obj.createElement("Arguments")
                arg = os.path.join(f"src\\{domain_name}\\tests", case_name)
                if case_params is not None:
                    arg = arg + " " + case_params
                arg_text = self.dom_obj.createTextNode(arg.strip())
                arg_node.appendChild(arg_text)

                # isEvent
                event_node = self.dom_obj.createElement("IsEvent")
                event_text = self.dom_obj.createTextNode("false")
                event_node.appendChild(event_text)

                test_node.appendChild(pkg_node)
                test_node.appendChild(name_node)
                if command_node is not None:
                    test_node.appendChild(command_node)
                test_node.appendChild(arg_node)
                test_node.appendChild(event_node)

                self.xml_root.appendChild(test_node)

    # generate testCase.xml file
    def generate_xml_file(self):
        # write xml content to file
        xml_file_path = os.path.join(self.root_path, 'testCases.xml')
        try:
            with open(xml_file_path, 'w', encoding='UTF-8') as fs:
                self.dom_obj.writexml(fs, indent='', addindent='\t', newl='\n', encoding='UTF-8')
        except Exception as ex:
            raise ex


def select_test_plan_file(root_path, src_path):
    test_plan_path = os.path.join(root_path, 'automation_testcases')

    valid_test_plan = []
    for entry in os.scandir(test_plan_path):
        if str(entry.name).endswith('.ini'):
            domain_name = get_domain_name_from_file_name(entry.name)
            if domain_name is not None and os.path.exists(os.path.join(src_path, domain_name)):
                valid_test_plan.append(entry)

    for index, domain in enumerate(valid_test_plan):
        print(f'{index}. {domain.name}')

    selected_test_plan = set()
    while True:
        if len(selected_test_plan) == 0:
            user_input = input('please input file index or input q to exit: ')
        else:
            print(f'you have selected test plans: {[plan.name for plan in selected_test_plan]}\n')
            user_input = input('please input file index or input q to exit: ')

        if user_input == 'q':
            break

        try:
            file_index = int(user_input)
            if file_index < len(valid_test_plan):
                selected_test_plan.add(valid_test_plan[file_index])
        except ValueError:
            print('you input invalid index, please input again\n')

    return selected_test_plan


if __name__ == "__main__":
    src_absolut_path = os.path.dirname(os.path.dirname(os.path.split(os.path.realpath(__file__))[0]))
    root_absolut_path = os.path.dirname(src_absolut_path)

    test_plan_files = select_test_plan_file(root_absolut_path, src_absolut_path)

    xml_generator = TestCaseXmlGenerator(root_absolut_path, src_absolut_path)

    xml_generator.generate_events()

    xml_generator.generate_system_test_case()

    xml_generator.generate_simics_test_case()

    for test_plan_file in test_plan_files:
        xml_generator.generate_domain_test_case(test_plan_file.path)

    xml_generator.generate_xml_file()

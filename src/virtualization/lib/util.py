import os
from src.virtualization.lib.const import sut_tool


def create_nic_xml_on_sut(sut, vm_name, bus, slot, function):
    bus = bus if '0x' in bus else '0x' + bus
    slot = slot if '0x' in slot else '0x' + slot
    function = function if '0x' in function else '0x' + function

    xml_filename = f'pci_device_{vm_name}_{bus}_{slot}_{function}.xml'
    xml_content = get_pci_xml_content(bus, slot, function)

    with open(xml_filename, "w") as xml_file:
        xml_file.write(xml_content)

    sut.upload_to_remote(localpath=xml_filename, remotepath=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    os.remove(xml_filename)

    return f"{sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/{xml_filename}"


def get_pci_xml_content(bus, slot, function):
    content = '<hostdev mode="subsystem" type="pci" managed="yes">\n'
    content += '    <driver name="vfio"/>\n'
    content += '    <source>\n'
    content += f'        <address domain="0x0000" bus="{bus}" slot="{slot}" function="{function}"/>\n'
    content += '    </source>\n'
    content += '</hostdev>\n\n'
    return content


def split_pci_dev_id(target_nic_id):
    return target_nic_id[:2], target_nic_id[3:5], target_nic_id[6:]

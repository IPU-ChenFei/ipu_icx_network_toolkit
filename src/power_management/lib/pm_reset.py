import re

from dtaf_core.lib.tklib.basic.utility import get_xml_prvd


def check_punit_mc_status(sut, itp):
    if get_xml_prvd('cpu').find('.//family').text.lower() == 'icx':
        itp.execute("from pysvtools import server_ip_debug")
        ret = itp.execute("server_ip_debug.pm.errors.get_mca_status()")
        # ret = itp.execute("server_ip_debug.punit.errors.get_mca_status()")
        assert 'error' not in ret, 'exist MC errors after boot'

    elif get_xml_prvd('cpu').find('.//family').text.lower() == 'bhs':
        ret = itp.execute("sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status.show()")
        reg_values = re.findall(r'0x\w+', ret)
        for reg_value in reg_values:
            assert reg_value == '0x00000000', 'exist MC errors after boot'

        ret = itp.execute("sv.sockets.ios.uncore.punit.ptpcfsms.ptpcfsms.mc_status.show()")
        reg_values = re.findall(r'0x\w+', ret)
        for reg_value in reg_values:
            assert reg_value == '0x00000000', 'exist MC errors after boot'

import argparse
import sys
import os

from src.lib.validationlanguage.src_translator.const import Assert, VERSION, default_pvl_mapping_file, defalut_bios_knobs_file

def parse_arguments():
    args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='translator high level steps into low level steps'
                    '--query <query_num_in_hsdes> : translate all the tcd in hsd-es query'
                    '--tcd <tcd_num_in_hsdes>     : translate a test case description from HSD-ES'
                    '-i <in_file> -o <out file>   : translate text file'
                )
    parser.add_argument('-t', '--tcd', default=None, dest='tcd_num', action='store',
                        help='tcd number in HSD-ES')
    parser.add_argument('-q', '--query', default=None, dest='tcd_query', action='store',
                        help='translate all the TCD in given HSD-ES query')
    parser.add_argument('-i', '--input', default=None, dest='input_file', action='store',
                        help='input text file')
    parser.add_argument('-o', '--output', default=None, dest='output_file', action='store',
                        help='output file, default as out.lls and out.py under output folder')
    parser.add_argument('-f', '--folder', default=None, dest='output_folder', action='store',
                        help='output folder, default at output folder')
    parser.add_argument('-m', '--mode', default='h2l', dest='mode', action='store',
                        help='translate from what to what'
                        'h2py : high level steps to python (default)'
                        'l2py : low level steps to python (only validate for file translation)'
                        'h2l  : high level steps to low level steps')
    parser.add_argument('-b', '--bios', default=False, dest='trans_bios_table', action='store_true',
                        help='translate bios menu table')
    parser.add_argument('-v', '--version', action='version', version=f'pre {VERSION}',
                        help=f'print version {VERSION}')
    parser.add_argument('-p', '--platform-configuration', action='store', default=None, dest='platform_configuration_file',
                        help='use --platform-configuration pvl_simics.xlsx for simics')
    # parser.add_argument('-d', '--bios-dump', action='store', default=None, dest='bios_dump_file',
    #                     help='xmlcli dump file, xml format')
    #parser.add_argument('--verify', default=False, dest='verify', action='store_true',
    #                    help='translate test case only, without feature definition table')
    return parser.parse_args(args)

def get_platform_config_real_path(name=None):
    if name is None:
        name = default_pvl_mapping_file
    transfile = os.path.realpath(name)
    if os.path.exists(transfile):
        return transfile

    transfile = os.path.join(os.getcwd(), name)
    if os.path.exists(transfile):
        return transfile

    transfile = os.path.join(os.path.split(os.path.realpath(__file__))[0], name)
    if os.path.exists(transfile):
        return transfile

    transfile = os.path.realpath(os.path.join(os.path.split(os.path.realpath(__file__))[0], '..', name))
    if os.path.exists(transfile):
        return transfile
    
    Assert(False, f'failed to find translation mapping table : {name}')

def get_pvl_mapping_file_path():
    ret = parse_arguments()
    return get_platform_config_real_path(ret.platform_configuration_file)

def get_bios_dump_file_path():
    # ret = parse_arguments()
    # bios_knobs = defalut_bios_knobs_file if ret.bios_dump_file is None else ret.bios_dump_file
    bios_knobs = defalut_bios_knobs_file
    if os.path.exists(bios_knobs):
        return os.path.realpath(bios_knobs)

    pvlpath = get_platform_config_real_path()
    pvlfolder = os.path.split(pvlpath)[0]
    xmlpath = os.path.join(pvlfolder, 'bios_xml', bios_knobs)
    if os.path.exists(xmlpath):
        return xmlpath

    xmlpath = os.path.join(pvlfolder, bios_knobs)
    if os.path.exists(xmlpath):
        return xmlpath

    Assert(False, f'failed to find BiosKnobs.xml')

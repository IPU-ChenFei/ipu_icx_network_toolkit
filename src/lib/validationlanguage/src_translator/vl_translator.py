from src.lib.validationlanguage.src_translator.trans_utils import parse_arguments,get_pvl_mapping_file_path
from src.lib.validationlanguage.src_translator.trans_h2l import HlsTranslator
from src.lib.validationlanguage.src_translator.trans_tcd import translate_tcd, HsdesVlTranslator
from src.lib.validationlanguage.src_translator.trans_l2p import PythonTransaltor, BiosMenuTranslator
from src.lib.validationlanguage.src_translator.hsdes import *
from src.lib.validationlanguage.src_translator.const import Assert, bios_knob_config_module, VERSION

import os

DEFAULT_OUTPUT_FOLDER='output'
DEFAULT_PYTHON_FOLDER = 'python'

def create_folder(folder):
    if os.path.isabs(folder):
        if not os.path.exists(folder):
            os.mkdir(folder)
        return folder

    path = os.path.join(os.getcwd(), folder)
    print(path)
    if not os.path.exists(path):
        os.mkdir(path)

    return path

def get_output_file(file, default_path):
    if os.path.isabs(file):
        return file
    else:
        return os.path.join(default_path, file)

def translate_query(query_id, out_lss, out_script, l2py):
    tcd_list = hsdes_query_ids(query_id)
    parser = HsdesVlTranslator(get_pvl_mapping_file_path())
    tcd = PythonTransaltor(get_pvl_mapping_file_path())
    for tcd_id in tcd_list:
        lls_file = get_output_file(f'{tcd_id}.lls', out_lss)

        output = parser.translate_tcd(tcd_id, out_lss)
        out_f = open(lls_file, 'w')
        output.insert(0, f'# Tool Version [{VERSION}]')
        out_f.writelines([line + '\n' for line in output])
        out_f.close()

        if l2py:
            py_file = get_output_file(f'{tcd_id}.py', out_script)
            tcd.translate_file(lls_file, py_file)

def translate_bios_menu_table(out_script):
    py_file = get_output_file(f'{bios_knob_config_module}.py', out_script)
    translator = BiosMenuTranslator(get_pvl_mapping_file_path())
    print(f'translate bios menu table to {py_file}')
    translator.translate_to_file(py_file)

def search_file(file):
    file = file.strip()
    if os.path.isabs(file):
        if os.path.exists(file) and os.path.isfile(file):
            return file
        else:
            return None

    suffix = file[-3:]
    if suffix in ('hls', 'lls'):
        subfolder = suffix
    elif suffix == '.py':
        subfolder = DEFAULT_PYTHON_FOLDER
    else:
        subfolder = DEFAULT_OUTPUT_FOLDER

    cwd = os.getcwd()
    search_paths = [
        cwd,
        os.path.join(cwd, DEFAULT_OUTPUT_FOLDER),
        os.path.join(os.path.split(os.path.realpath(__file__))[0], '..'),
        os.path.join(os.path.split(os.path.realpath(__file__))[0], '..', DEFAULT_OUTPUT_FOLDER)
    ]
    for p in search_paths:
        path = os.path.join(p, file)
        if os.path.exists(path) and os.path.isfile(path):
            return path
        path = os.path.join(p, subfolder, file)
        if os.path.exists(path) and os.path.isfile(path):
            return path

    return None


def main():
    ret = parse_arguments()

    # TODO: disable python translation
    #assert(ret.mode == 'h2l')

    if ret.output_folder is None:
        output_folder = create_folder('output')
    else:
        output_folder = create_folder(ret.output_folder)
    lls_folder = create_folder(os.path.join(output_folder, 'lls'))
    script_folder = create_folder(os.path.join(output_folder, 'python'))

    h2l = False
    l2py = False
    if ret.mode in ('h2py', 'h2l'):
        h2l = True
    if ret.mode in ('h2py', 'l2py'):
        l2py = True

    if ret.trans_bios_table:

        translate_bios_menu_table(script_folder)

    assert (ret.mode in ('h2l', 'h2py', 'l2py'))

    if ret.tcd_query is not None:
        assert(h2l)
        print(f'output_folder={output_folder}')
        translate_query(int(ret.tcd_query), lls_folder, script_folder, l2py)
        return

    lls_file = None
    output_file = None

    if ret.tcd_num is not None:
        id = int(ret.tcd_num)
        if ret.mode == 'h2l':
            lls_file = get_output_file(f'{id}.lls', lls_folder)
            output_file = lls_file
        elif ret.mode == 'h2py':
            lls_file = os.path.join(lls_folder, f'{id}.lls')
            output_file = get_output_file(f'{id}.py', script_folder)
        else:
            Assert(False, f'mode [{ret.mode}] is not supported for --tcd <id>')
        translate_tcd(id, lls_file, lls_folder)
    elif ret.input_file is not None and ret.output_file is not None:
        print(f'translate {ret.input_file} to')
        print(f'out={ret.output_file}')

        if ret.mode == 'h2l':
            lls_file = get_output_file(ret.output_file, lls_folder)
            output_file = lls_file
        elif ret.mode == 'h2py':
            lls_name = os.path.basename(ret.input_file).split('.')[0]
            lls_file = os.path.join(lls_folder, lls_name + '.lls')
            output_file = get_output_file(ret.output_file, script_folder)

        input_file = search_file(ret.input_file)
        assert (input_file is not None)
        if ret.mode == 'l2py':
            lls_file = input_file
            output_file = get_output_file(ret.output_file, script_folder)

        if h2l:
            assert(input_file is not None)
            assert(lls_file is not None)
            print(f'low level steps at {lls_file}')
            tcd = HlsTranslator(get_pvl_mapping_file_path())
            tcd.translate_file(input_file, lls_file)

    elif not ret.trans_bios_table:
        print('either of following parameters patterns is required')
        print('-q | --query <id> : for TCD query')
        print('-t | --tcd   <id> : for TCD ID')
        print('-i | --input <in_file> -o | --output <out_file> : for text file input')

    if l2py:
        assert (output_file is not None)
        assert (lls_file is not None)
        print(f'python script at {output_file}')
        tcd = PythonTransaltor(get_pvl_mapping_file_path())
        tcd.translate_file(lls_file, output_file)

    print('Translation Done!')
    print(f'output to {output_file}')
    #print(f'under {output_folder}')

if __name__ == '__main__':
    main()
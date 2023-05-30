import copy
import os

from src.lib.validationlanguage.src_translator.translator import *
from src.lib.validationlanguage.src_translator.const import *
from src.lib.validationlanguage.src_translator.sys_variables import SystemVariables
from src.lib.validationlanguage.src_translator.python_generator import *
from src.lib.validationlanguage.src_translator.data import TIME_STAMP

def get_script_path(name):
    path = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..', 'python')
    if os.path.exists(path):
        return os.path.join(path, name)

    path = os.path.join(os.getcwd(), 'python')
    print(path)
    if os.path.exists(path):
        return os.path.join(path, name)

    return None

def get_python_code_path(name):
    path = os.path.join(os.getcwd(), 'python_code', name + '.py')
    if os.path.exists(path):
        return path
    path = os.path.join(os.path.split(os.path.realpath(__file__))[0], '..', 'python_code', name + '.py')
    if os.path.exists(path):
        return path
    return None

def read_python_code_lines(name):
    path = get_python_code_path(name)
    print(f'python code path = {path}')
    f = open(path, 'r')
    output=[]
    for line in f.readlines():
        l = line.strip()
        idx = line.find(l)
        for i in range(0, idx):
            l = ' '+l
        output.append(l)
    f.close()
    return output

class StepSentence(Sentence):
    def __init__(self, instance):
        assert(isinstance(instance, Sentence))
        super(StepSentence, self).__init__(OP_STEP, instance.templates)

    def get_args(self, args_str):
        arg_list = get_args(args_str)
        num = arg_list[0]
        if len(arg_list) > 1:
            idx = args_str.find(',')
            assert (idx>=0)
            comments = args_str[idx+1:].replace("\"", '\\"')
            arg_list = [num, comments]
        return arg_list

class LogSentence(Sentence):
    def __init__(self, instance):
        assert (isinstance(instance, Sentence))
        super(LogSentence, self).__init__(OP_LOG, instance.templates)

    def get_args(self, args_str):
        args_str = args_str.replace("\"", '\\"')
        return [args_str]

class ExecuteCmdSentence(CommandSentence):
    def get_args(self, args_str):
        arg_list = []
        args_str = args_str.strip()

        temp = args_str.split(',')

        if len(temp) == 1:
            return [args_str]

        arg_next = temp[0].strip()

        for i in temp:
            if arg_next.startswith('nocheck'):
                arg_list.append(arg_next)
                assert(len(temp) > 1)
                temp = temp[1:]
                arg_next = temp[0].strip()

            if arg_next.startswith('timeout='):
                timeout = arg_next[len('timeout='):]
                if is_int(timeout):
                    arg_list.append(timeout)
                    assert (len(temp) > 1)
                    temp = temp[1:]
                    arg_next = temp[0].strip()

        assert(len(temp) > 0)
        cmd = arg_next
        if len(temp) > 1:
            for i in range(1, len(temp)):
                cmd = cmd + ',' + temp[i]
        arg_list.append(cmd)

        return arg_list

    def translate(self, args_str, sys_var, escape=False):
        # type: (str, SystemVariables, bool) -> Translation

        trans = super(ExecuteCmdSentence, self).translate(args_str, sys_var, escape)
        if trans is not None and trans.output_lines is not None:
            assert(len(trans.output_lines)==1)
            if sys_var.environment == SystemVariables.Environment.OS:
                trans.output_lines[0] = 'sutos.'+trans.output_lines[0]
            elif sys_var.environment == SystemVariables.Environment.UEFI_SHELL:
                trans.output_lines[0] = 'UefiShell.' + trans.output_lines[0]
            else:
                Assert(False, f'wrong environment value {sys_var.environment}')

        return trans
"""
class SwitchDcSentence(Sentence):
    def __init__(self, instance):
        assert (isinstance(instance, Sentence))
        super(SwitchDcSentence, self).__init__(instance.op, instance.templates)

    def translate(self, args_str, sys_var, escape=False):
        # type: (str, SystemVariables, bool) -> Translation

        trans = super(SwitchDcSentence, self).translate(args_str, sys_var, escape)
        if args_str.strip().lower() == 'off' and trans is not None and trans.output_lines is not None:
            assert(len(trans.output_lines)==1)
            if sys_var.environment == SystemVariables.Environment.OS:
                trans.output_lines[0] = 'sutos.'+trans.output_lines[0]
            elif sys_var.environment == SystemVariables.Environment.UEFI_SHELL:
                trans.output_lines[0] = 'UefiShell.' + trans.output_lines[0]
            else:
                Assert(False, f'wrong environment value {sys_var.environment}')

        return trans
"""

class SetBiosKnobSentence(Sentence):
    def __init__(self, bios_menu_table):
        super(SetBiosKnobSentence, self).__init__(OP_SET_BIOS_KNOB)
        self.__bios_menu_table = bios_menu_table

    def parse_knobs(self, args_str):
        args_list = self.get_args(args_str)

        bios_menu_arg_list = []
        cmd_arg_list = [] # xmlcli

        cli_str = ''
        for arg_pair_str in args_list:
            item = parse_assignment_line(arg_pair_str.strip())
            Assert(item is not None, f'wrong parameter for [{OP_SET_BIOS_KNOB}] {arg_pair_str}')
            (knob_name, knob_value) = item
            if knob_name in self.__bios_menu_table.keys():
                bios_menu_arg_list.append(item)
            else:
                if len(cli_str) == 0:
                    cli_str = f'{knob_name}={knob_value}'
                else:
                    cli_str += f', {knob_name}={knob_value}'
                cmd_arg_list.append(item)

        Assert(len(cmd_arg_list) + len(bios_menu_arg_list) >0,
               f'missing parameters')
        #return (cmd_arg_list, bios_menu_arg_list)
        return (cli_str, bios_menu_arg_list)

    def __get_prefix(self, env):
        if env == SystemVariables.Environment.OS:
            return 'sut.xmlcli_os'
        elif env == SystemVariables.Environment.UEFI_SHELL:
            return 'sut.xmlcli_uefi'
        else:
            assert(not 'invalid Environment')
            return None

    def translate(self, args_str, sys_var, escape=False):
        # type: (str, SystemVariables, bool) -> Translation

        (cli_args, bios_args) = self.parse_knobs(args_str)

        assert(sys_var.environment in (SystemVariables.Environment.OS, SystemVariables.Environment.UEFI_SHELL))

        output_lines = []
        output_lines.append(f'## {self.op}: {args_str.strip()}')
        #output_lines.append(f'## when Environment = {sys_var.environment}')
        #new_environment = ori_environment = sys_var.environment
        prefix = self.__get_prefix(sys_var.environment)
        # output_lines.append('need_reset = False')
        items = []
        condition = None

        if len(cli_args) > 0:
            output_lines.append(f'set_cli = not {prefix}.check_bios_knobs("{cli_args}")')

            code = []
            code.append(f'{prefix}.set_bios_knobs("{cli_args}")')
            #code.append(f'tcd.expect(f\'set bios knobs "{cli_args}" success\',ret)')
            if len(bios_args) == 0:
                code.extend(python_reset_to(sys_var.environment, sys_var.environment))
                code.append(f'tcd.expect("double check bios knobs", {prefix}.check_bios_knobs("{cli_args}"))')

            output_lines.extend(python_if('set_cli', code))


        if len(bios_args) > 0:
            # reset to BIOS setup menu anyway
            reset_code = python_reset_to(sys_var.environment, SystemVariables.Environment.BIOS_MENU)
            #new_environment =
            assert (reset_code is not None)
            output_lines.extend(reset_code)
            items = []
            condition = None
            for i in range(0, len(bios_args)):
                id, value = bios_args[i]
                var = get_bios_menu_knob_var_name(id)
                #TODO: optimize if knobs on the same BIOS page
                output_lines.append(f'changed_{i} = sut.set_bios_knobs_menu({var}, "{value}")')
                items.append(f'changed_{i}')
            assert(len(items) > 0)
            condition = get_and_items(items)
            #output_lines.append(f'need_reset = {condition}')
            check_code = python_reset_to(SystemVariables.Environment.BIOS_MENU, SystemVariables.Environment.BIOS_MENU)
            for i in range(0, len(bios_args)):
                id, value = bios_args[i]
                var = get_bios_menu_knob_var_name(id)
                #TODO: optimize if knobs on the same BIOS page
                check_code.append(f'tcd.expect("{id}/{var} is {value}", sut.check_bios_knobs_menu({var}, "{value}"))')
            output_lines.extend(python_if(condition, check_code))
            output_lines.extend(python_enter(SystemVariables.Environment.BIOS_MENU, sys_var.environment))

            if len(cli_args) > 0:
                check_code = []
                check_code.append(f'tcd.expect("double check", {prefix}.check_bios_knobs("{cli_args}"))')
                output_lines.extend(python_if('set_cli', check_code))

        else:
            assert(len(cli_args) > 0)

        """
        elif len(cli_args) > 0:
            condition = get_or_items(items)
            output_lines.append(f'need_reset = {condition}')
            #output_lines.append(get_or_items('need_reset', items))
        """

        # last reset


        output_lines.append('')
        #output_lines.append('')
        return Translation(self.op, output_lines)



class PythonTransaltor(VlTranslator):

    def __init__(self, transfile=default_pvl_mapping_file, check_syntax=False):
        super(PythonTransaltor, self).__init__(transfile, check_syntax)
        self.escape = True
        self.mapping_table = self.table_parser.l2py_table
        self.translators = {
            # op_name : sentence instance
        }
        for op, template in self.table_parser.l2py_table.items():
            assert (op not in self.translators.keys())
            self.translators[op] = Sentence(op, template)

        self.translators[OP_LOG] = LogSentence(self.translators[OP_LOG])
        self.translators[OP_STEP] = StepSentence(self.translators[OP_STEP])
        self.translators[OP_EXECUTE_CMD] = ExecuteCmdSentence(self.translators[OP_EXECUTE_CMD])
        self.translators[OP_SET_BIOS_KNOB] = SetBiosKnobSentence(self.table_parser.bios_menu_table)
        self.translators[OP_ITP_CMD] = CommandSentence(self.translators[OP_ITP_CMD])
        #self.translators[OP_DC] = SwitchDcSentence(self.translators[OP_DC])

    def is_prefix(self, line):
        return line.find('ID:') == 0 or line.find('TITLE:') == 0 or line.find('DOMAIN:') == 0


    def translate_assign_line(self, line):
        ret = parse_assignment_line(line)
        if ret is None:
            return None

        name, value = ret
        ret = self.sys_var_check_set(name, value)
        if ret:
            print(f'\tVariable Changed! {name}={value}')
            return [f'tcd.{name.lower()} = {value}']
        else:
            return [f'{name} = {value}']

    def translate_with_indent(self, line, indent_level):
        trans = self.translate(line)
        if trans is None:
            return None
        elif trans.output_lines is None:
            return None

        trans.output_lines = python_indent(trans.output_lines, indent_level)
        return trans

    def has_indent(self, line):
        return line.find('    ') == 0

    def __check_trans(self, trans_list):
        for trans in trans_list:
            assert (isinstance(trans, Translation))
            if trans.op not in (OP_EMPTY, OP_COMMENTS, OP_REPEAT,OP_END, OP_LOW_LEVEL):
                return True

        return False

    def __translate_step(self, lines):
        outlines = []
        repeat_trans = []

        indent_level = 0
        for idx in range(0, len(lines)):
            line = lines[idx].strip()
            print(f'translating Line {idx+1}: {line}')
            if len(line) == 0:
                outlines.append('')
                continue

            if line.find(OP_REPEAT + ':') == 0:
                Assert(indent_level==0, 'last Repeat has not an "End:"')
                indent_level += 1
                il = 0
                repeat_trans = []
            elif line.find(OP_END + ':') == 0:
                Assert(indent_level==1, 'End before Repeat')
                indent_level -= 1
                Assert(self.__check_trans(repeat_trans), 'repeat shall have body')
                continue
            else:
                il=indent_level

            trans = self.translate_with_indent(line, il)
            Assert(trans is not None, f'Error: cannot parse [{line}]')
            repeat_trans.append(trans)
            op = trans.op
            out = trans.output_lines

            Assert(op not in (OP_STEP, OP_PREPARE), f'{OP_STEP} and {OP_PREPARE} shall not embed')
            outlines.extend(out)
        # loop end

        Assert('Repeat shall have End', indent_level == 1)
        return outlines

    def _parse_code(self, lines):
        code_blocks = []
        block_lines = []
        first_prepare = True
        first_step = True
        for idx in range(0, len(lines)):
            line = lines[idx].strip()
            is_prepare = line.find(OP_PREPARE + ':') == 0
            is_step = line.find(OP_STEP + ':') == 0
            if is_prepare or is_step:
                # end last block
                if len(block_lines) > 0:
                    code_blocks.append(copy.deepcopy(block_lines))

                assert(not is_prepare or first_step)
                if is_prepare and first_prepare:
                    block_lines = []
                    block_lines.append('#################################################################')
                    block_lines.append('# Pre-Condition Section')
                    block_lines.append('#################################################################')
                    code_blocks.append(block_lines)
                    first_prepare = False
                elif is_step and first_step:
                    block_lines = []
                    block_lines.append('#################################################################')
                    block_lines.append('# Steps Section')
                    block_lines.append('#################################################################')
                    code_blocks.append(block_lines)
                    first_step = False

                # star a new block
                block_lines = []
                if is_step:
                    res = line.split(':')
                    param = res[1].strip().strip(',')
                    if  param.find(',') < 0:
                        for j in range(idx+1, len(lines)):
                            next_line = lines[j].strip()
                            if len(next_line) > 0:
                                if next_line[0] == '#':
                                    lines[idx] = lines[idx].strip().strip(',') + ', ' + next_line[1:].strip()
                                    print('update step')
                                else:
                                    lines[idx] = lines[idx].strip().strip(',')
                                # break anyway for non-blank line
                                break
            #endif

            # append line to current block
            block_lines.append(lines[idx])

        #end loop
        if len(block_lines) > 0:
            code_blocks.append(copy.deepcopy(block_lines))

        return code_blocks

    def translate_lines(self, lines, msg_prefix=''):
        prefix_lines = []
        outlines = []

        code_blocks = self._parse_code(lines)
        for block_lines in code_blocks:
            assert(len(block_lines) > 0)
            line1 = block_lines[0].strip()
            if line1.find(OP_PREPARE + ':') == 0 or line1.find(OP_STEP + ':') == 0:
                trans = self.translate_with_indent(line1, 0)
                assert(trans.op in (OP_PREPARE, OP_STEP))
                outlines.append(trans.output_lines[0])
                step_head = trans.output_lines[1]
                step_code = self.__translate_step(block_lines[1:])
                output = python_if(step_head, step_code)
            else:
                output = self.__translate_step(block_lines)

            # add translated block
            outlines.extend(output)

        outlines = python_indent(outlines, 1)

        file_lines = [
            'CASE_DESC = [',
            '    "it is a python script generated from validation language"'
        ]
        length = len(prefix_lines)
        for i in range(0, length):
            file_lines[-1] = file_lines[-1] + ','
            file_lines.append(f'    "{prefix_lines[i]}"')
        file_lines.append(']')
        file_lines.append('')

        lines = read_python_code_lines('import')
        file_lines.extend(lines)
        file_lines.append('')
        file_lines.append('')
        file_lines.extend(outlines)
        file_lines.append('')
        file_lines.append('')

        lines = read_python_code_lines('case')
        file_lines.extend(lines)

        return file_lines

    def translate_lines_only(self, lines, msg_prefix=''):
        prefix_lines = []
        outlines = []

        code_blocks = self._parse_code(lines)
        for block_lines in code_blocks:
            assert(len(block_lines) > 0)
            line1 = block_lines[0].strip()
            if line1.find(OP_PREPARE + ':') == 0 or line1.find(OP_STEP + ':') == 0:
                trans = self.translate_with_indent(line1, 0)
                assert(trans.op in (OP_PREPARE, OP_STEP))
                outlines.append(trans.output_lines[0])
                step_head = trans.output_lines[1]
                step_code = self.__translate_step(block_lines[1:])
                output = python_if(step_head, step_code)
            else:
                output = self.__translate_step(block_lines)

            # add translated block
            outlines.extend(output)

        outlines = python_indent(outlines, 1)
        return outlines

    def translate_file(self, inputfile, outputfile='out.txt'):
        f = open(inputfile, 'r')
        out_f = open(outputfile, 'w')
        outlines = self.translate_lines(f.readlines())
        outlines.insert(0, f'# Tool Version [{VERSION}]')
        #out_f.writelines(outlines)
        out_f.writelines([line + '\n' for line in outlines])
        f.close()
        out_f.close()


class BiosMenuTranslator(BasicTranslator):
    def __init__(self, transfile=default_pvl_mapping_file):
        super(BiosMenuTranslator, self).__init__(transfile)
        self.escape = True

    @property
    def bios_table(self):
        # type:()->dict
        return self.table_parser.bios_menu_table

    def translate_table(self):

        code_lines = [
            f'# this is generated code from validation language mapping table ({self.table_parser.filename})',
            f'# knobs for bios setup menu only in "{bios_menu_knob_tab}" tab',
            f'# Time Stamp: {TIME_STAMP()}',
            '',
            f'from dtaf_core.lib.tklib.infra.bios.bios import BIOS_KNOB_SERIAL',
            '',
            ''
        ]
        assert(self.bios_table is not None)

        # prepare definition
        bios_menu_knob_table = {}
        bios_menu_knob_table_translated = {}
        for item in self.bios_table.items():
            id = item[0].strip()
            knob_name, knob_path = item[1]

            assert(len(id.split())==1)
            var = get_bios_menu_knob_var_name(id)

            code = python_knob_menu_knob(id, knob_name.strip(), knob_path)
            code_lines.extend(code)
            code_lines.append('')

        for line in code_lines:
            print(line)

        return code_lines

    def translate_to_file(self, pyfile):
        out_f = open(pyfile, 'w')
        outlines = self.translate_table()
        outlines.insert(0, f'# Tool Version [{VERSION}]')
        out_f.writelines([line + '\n' for line in outlines])
        out_f.close()

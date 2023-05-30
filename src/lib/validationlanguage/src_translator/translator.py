from src.lib.validationlanguage.src_translator.parser_table import MappingTableParser, get_args
from src.lib.validationlanguage.src_translator.sys_variables import SystemVariables
from src.lib.validationlanguage.src_translator.const import *
import copy


def is_assign_line(line):
    line = line.strip()

    if line.find('=') < 1:
        return False

    chars = 'abcdefghijklmnopqrstuvwxyz_'
    assert(len(chars) == 27)
    if chars.find(line[0].lower()) < 0:
        return False

    chars += '0123456789={}\'"'
    for i in range(0, len(line)):
        if line[i] != ' ' and chars.find(line[i].lower()) < 0:
            return False

    return True

def parse_assignment_line(line):
    line = line.strip()
    if not is_assign_line(line):
        return None

    ret = line.split('=')
    if len(ret)!= 2:
        return None
    name = ret[0].strip()
    if len(name.split()) > 1:
        return None
    value = ret[1].strip()

    return (name, value)

def is_int(nstr):
    for i in range(0, len(nstr)):
        if '0123456789+-*/ '.find(nstr[i]) < 0:
            return False
    return True


def is_variable(arg):
    arg = arg.strip()
    if arg[0] == '<' and arg[len(arg)-1] == '>':
        return True
    else:
        return False

def match_arg(op_arg, input_arg):
    op_arg = op_arg.strip()
    input_arg = input_arg.strip()
    if is_variable(op_arg):
        return True
    else:
        return op_arg == input_arg

"""
def check_args(op_args, input_args):
    assert (isinstance(op_args, list))
    assert (isinstance(input_args, list))
    if len(op_args) != len(input_args):
        return False
    for i in range(0, len(op_args)):
        if not is_variable(op_args[i]) and not match_arg(op_args[i], input_args[i]):
            return False
    return True
"""

def parse_args(op_args, input_args):
    assert (isinstance(op_args, list))
    assert (isinstance(input_args, list))
    if len(op_args) != len(input_args):
        return None

    table = {}
    for i in range(0, len(op_args)):
        op_args[i] = op_args[i].strip()
        input_args[i] = input_args[i].strip()

        if is_variable(op_args[i]):
            assert(op_args[i] not in table.keys())
            arg_name=op_args[i][1:-1].strip()
            arg_value = input_args[i]
            if arg_value.find(f'{arg_name}=') == 0:
                arg_value=arg_value[len(arg_name)+1:]

            idx_equal = arg_value.find('=')
            idx_quotation = arg_value.find('"')
            idx_quotation_single = arg_value.find('\\\'')
            if idx_equal < idx_quotation and idx_equal < idx_quotation_single:
                print(f'ERROR: parse_args: [{arg_value}] contains = before quotation')
                return None

            table[op_args[i]] = arg_value
        elif not match_arg(op_args[i], input_args[i]):
            return None
    return table


class Translation(object):
    def __init__(self, op, outlines, args=None):
        self.op = op
        assert(outlines is None or isinstance(outlines, list))
        self.output_lines = outlines
        if args is None:
            self.args = []
        else:
            self.args = args

    def add_prefix(self, prefix):
        if len(prefix) > 0:
            print(f'add indent [{prefix}]')
            for i in range(0, len(self.output_lines)):
                self.output_lines[i] = prefix+self.output_lines[i]

class Sentence(object):
    def __init__(self, op, translate_templates=None):
        self.op = op
        self.templates = translate_templates
        self.step_support = True
        self.prepare_support = True

    def get_args(self, args_str):
        return get_args(args_str)

    def translate(self, args_str, sys_var, escape=False):
        assert (isinstance(sys_var, SystemVariables))
        if sys_var.check_stage:
            if sys_var.in_prepare:
                Assert(self.prepare_support, f'Error: {self.op} is not allowed for Prepare')
            else:
                Assert(self.step_support, f'Error: {self.op} is not allowed for Step')
        output_lines = []
        args_list = self.get_args(args_str)

        for item in self.templates:
            op_args, low_lines = item
            args = parse_args(op_args, args_list)
            if args is not None:
                for low_l in low_lines:
                    translation=low_l
                    for (var, value) in args.items():
                        if escape:
                            #value = value.replace("\"", '\\"')
                            value = value.replace("\'", '\\\'')
                        translation = translation.replace(var, value)
                    output_lines.append(translation)
                return Translation(self.op, output_lines, args_list)
        return None



class CommandSentence(Sentence):
    def __init__(self, instance):
        assert (isinstance(instance, Sentence))
        super(CommandSentence, self).__init__(instance.op, instance.templates)

    def get_args(self, args_str):
        arg_list = []
        args_str = args_str.strip()

        temp = args_str.split(',')

        if len(temp) == 1:
            return [args_str]

        arg_next = temp[0].strip()
        if arg_next.find('timeout=') == 0:
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

class BasicTranslator(object):
    def __init__(self, transfile):
        self.table_parser = MappingTableParser(transfile)
        self.escape = False
        self.mapping_table = None



class VlTranslator(BasicTranslator):

    def __init__(self, transfile, check_syntax=False):
        super(VlTranslator, self).__init__(transfile)
        self.var = SystemVariables()
        self.check_syntax = check_syntax
        self.translators = None

    def is_low_level_step(self, op):
        return op not in self.table_parser.high_level_step_os_list and op in self.table_parser.low_level_step_os_list

    def sys_var_check_set(self, name, value):
        if not SystemVariables.is_sys_var(name):
            return False

        if name == 'ItpLib' and self.var.check_stage:
            Assert(self.var.in_prepare, f'{name} cannot be set out of Pre-condition')

        success = self.var.set(name, value)
        assert (success, f'Wrong value to system variables: {name} = {value}')
        return True



    def translate(self, line_ori):
        line = line_ori.strip()

        if line.find('#') == 0:
            return Translation(OP_COMMENTS, [line_ori])

        output_lines = self.translate_assign_line(line)
        if output_lines is not None:
            return Translation(OP_ASSIGNMENT, output_lines)

        ret = line.split(':')
        if len(ret) <= 1:
            return None

        op = ret[0]
        args_str = line[line.find(':')+1:]
        if op not in self.translators.keys():
            return None

        tr = self.translators[op]
        trans = tr.translate(args_str, self.var, self.escape)
        assert(isinstance(trans, Translation))
        return trans

    def handle_unknown_line(self, line):
        Assert(not self.check_syntax, f'Syntax Error: {line}')
        return line

    def translate_assign_line(self, line):
        pass

    def translate_lines(self, lines, msg_prefix=''):
        pass



#if __name__ == '__main__':
    #test_h2l()
    #test_l2py()



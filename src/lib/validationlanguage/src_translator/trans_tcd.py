from src.lib.validationlanguage.src_translator.trans_h2l import HlsTranslator
from src.lib.validationlanguage.src_translator.hsdes_tcd import Tcd, TcdAPI
from src.lib.validationlanguage.src_translator.const import Assert, default_pvl_mapping_file, VERSION
from src.lib.validationlanguage.src_translator.trans_utils import get_pvl_mapping_file_path
import json
import os

class HsdesVlTranslator(HlsTranslator):

    def __init__(self, transfile=default_pvl_mapping_file):
        super(HsdesVlTranslator, self).__init__(transfile)
        self.var.check_stage = True

    def __translate_step(self, step):
        # type: (dict) -> list
        input = step["action"]
        outlines = [f'STEP: {self.step}']
        #outlines.append('### Actions ###')
        #first_line=True

        self.var.in_prepare = False
        lines = input.split('\n')
        output = self.translate_lines(lines, f'Step {self.step}')
        outlines.extend(output)

        # outlines.append('"""')
        input = step["expected_results"].strip()
        if len(input) > 0:
            outlines.append('##################')
            outlines.append('Log: ### Expected result ###')
            for line in input.split('\n'):
                if len(line) == 0:
                    continue
                out = "Log: " + line.strip()
                outlines.append(out)

        input = step["notes"].strip()
        if len(input) > 0:
            outlines.append('### Notes ###')
            for line in input.split('\n'):
                if len(line) == 0:
                    continue
                out = "# " + line.strip()
                outlines.append(out)

        outlines.append('##################')
        return outlines

    @classmethod
    def __to_plain_text(cls, text):
        table = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&quot;': '\"',
            '&lt;': '<',
            '&gt;': '>',
            '"': '\"',
            '\n': ' '
        }
        output = text.strip()
        for name, value in table.items():
            output = output.replace(name, value)

        return output.strip()

    @classmethod
    def text2line_remove_tags(cls, text):
        output = []
        rest = text.strip()
        print(text)
        line = ''
        while len(rest) > 0:
            idx_start = rest.find('<')
            idx_end = rest.find('>')

            assert (idx_start >= 0)
            assert (idx_end > idx_start)
            content = rest[:idx_start]

            line = line+content
            tag = rest[idx_start + 1:idx_end].strip()
            tag_text = tag.strip('/').strip()
            if tag_text.lower() in ('p', 'span', 'table', 'li', 'div'):
                if tag.find('/') == 0 and len(line) > 0:
                    output.append(cls.__to_plain_text(line))
                    line=''
                else:
                    assert(len(line)==0)
            elif tag.lower()=='br/':
                output.append(cls.__to_plain_text(line))
                line=''
            rest = rest[idx_end + 1:].strip()

        assert (len(line)==0)
        return output

    def __translate_precondition(self, text):
        outlines=[
            'PREPARE: setup system for test'
        ]
        lines = self.text2line_remove_tags(text)

        self.var.in_prepare = True
        output = self.translate_lines(lines, f'Prep')
        outlines.extend(output)
        return outlines

    def __text_to_file(self, text, file):
        out_f = open(file, 'w')

        out_f.write(text)
        out_f.close()

    def translate_tcd(self, id, logfolder):
        api = TcdAPI()
        tcd = api.download_article(id)
        print("===============================================================")
        print(tcd.to_json())
        title = tcd.get_field('title')
        domain = tcd.get_field('domain')
        output = [
            f'#ID/LINK: https://hsdes.intel.com/appstore/article/#/{id}',
            f'#TITLE: {title}',
            f'#DOMAIN: {domain}',
            ''
        ]

        output.append('')
        #output.append('#################################################################')
        #output.append('# Pre-Condition Section')
        #output.append('#################################################################')
        precondition_string = tcd.get_field('server_platf.test_case_definition.pre_condition')
        self.__text_to_file(precondition_string, os.path.join(logfolder, f'{id}.precondition.xml'))
        self.step = 0
        self.var.in_prepare = True
        out = self.__translate_precondition(precondition_string)
        output.extend(out)
        output.append('')

        output.append('')
        #output.append('#################################################################')
        #output.append('# Steps Section')
        #output.append('#################################################################')
        steps_string = tcd.get_field('test_case_definition.test_steps')
        self.__text_to_file(steps_string, os.path.join(logfolder, f'{id}.steps.json'))
        steps = json.loads(steps_string)
        self.var.in_prepare = False
        for i in range(0, len(steps)):
            self.step = i+1
            out = self.__translate_step(steps[i])
            output.extend(out)
            output.append('')
            output.append('')

        return output

def translate_tcd(id, outputfile, logfolder):
    parser = HsdesVlTranslator(get_pvl_mapping_file_path())


    output = parser.translate_tcd(id, logfolder)
    output.insert(0, f'# Tool Version [{VERSION}]')
    out_f = open(outputfile, 'w')

    out_f.writelines([line + '\n' for line in output])
    out_f.close()

    return

def test_precondition(file):
    f = open(file, 'r')
    text = ''
    for l in f.readlines():
        text += l
    f.close()

    text2 = HsdesVlTranslator.text2line_remove_tags(text)
    print(text2)
    pass

if __name__ == '__main__':
    import os
    test_precondition(os.path.join(os.getcwd(), 'output', 'lls', 'test.xml'))
    #translate_tcd(16015342566, '16015342566.txt', os.getcwd())


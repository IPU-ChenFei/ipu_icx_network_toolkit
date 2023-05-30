import os

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'This API provide some function for messages/dmesg/eventlog check'
]


# Common Windows Function
def find_string_windows(file, filter_file):
    f = open(file, encoding='utf-16')
    b = open(filter_file, 'w', encoding='utf-16')
    for line in f:
        if "error" in line or "Error" in line or "Critical" in line:
            print(line)
            b.write(line)
    f.close()
    b.close()


def winlog_split_file(file, split_file):
    f = open(file, encoding='utf-16')
    c = open(split_file, 'w', encoding='utf-16')
    for line in f:
        print(line[53:])
        c.write(line[53:])
    f.close()


def winlog_compare_file(ignorable_file, split_file, compare_file):
    str1 = []
    str2 = []
    str_dump = []
    fa = open(ignorable_file, 'r', encoding='utf-16')
    fb = open(split_file, 'r', encoding='utf-16')
    fc = open(compare_file, 'w+', encoding='utf-16')


# Common Linux Function

def find_string(file, filter_file):
    f = open(file)
    b = open(filter_file, 'w')
    for line in f:
        if "error" in line or "Error" in line or "Critical" in line:
            print(line)
            b.write(line)
    f.close()
    b.close()


#
# def remove_time(file):
#     f = open(file)
#     c = open('remove_time_file', 'w')
#     for line in f:
#         print(line[16:])
#         c.write(line[16:])
#     f.close()

def split_file(file, split_file):
    f = open(file)
    c = open(split_file, 'w')
    for line in f:
        b = ''.join(line.split(':', 3)[3])
        print(b)
        c.write(b)
    f.close()
    c.close()


def dmesg_split_file(file, split_file):
    f = open(file)
    c = open(split_file, 'w')
    for line in f:
        b = ''.join(line.split(':', 1)[1:])
        print(b)
        c.write(b)
    f.close()
    c.close()


def compare_file(ignorable_file, split_file, compare_file):
    str1 = []
    str2 = []
    str_dump = []
    fa = open(ignorable_file, 'r')
    fb = open(split_file, 'r')
    fc = open(compare_file, 'w+')

    for line in fa.readlines():
        str1.append(line.replace("\n", ''))
    for line in fb.readlines():
        str2.append(line.replace("\n", ''))

    for i in str1:
        if i in str2:
            str_dump.append(i)

    str_all = set(str1 + str2)

    for i in str_dump:
        if i in str_all:
            str_all.remove(i)

    for i in list(str_all):
        fc.write(i + '\n')

    fa.close()
    fb.close()
    fc.close()


def check_compare_file(file):
    f = open(file)
    for line in f:
        if "error" in line or "Error" in line or "Critical" in line:
            raise ValueError('Found fail string in compare_file')
    f.close()

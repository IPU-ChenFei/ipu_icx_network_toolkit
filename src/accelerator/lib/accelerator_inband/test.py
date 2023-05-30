# # from add_path import add_path_to_environment
# #
# # add_path_to_environment('DSA_DRIVER', '/home/BKCPkg/domains/acce_tools/DSA')
#
# import sys
# import argparse
# from lnx_exec_with_check import lnx_exec_command
# import os
#
#
# def setup_argparse():
#     args = sys.argv[1:]
#     parser = argparse.ArgumentParser(
#         description='add the only folder under the path to the system environment variable'
#                     '--name <system environment variable name>'
#                     '--path <value of the system environment variable which should be a path>')
#     parser.add_argument('-n', '--name', required=True, dest='name', action='store', help='environment variable name')
#     parser.add_argument('-p', '--path', required=True, dest='path', action='store',
#                         help='variable path')
#     ret = parser.parse_args(args)
#     return ret
#
#
# def add_path_to_environment(variable_name, variable_path):
#     """
#           Purpose: add the only folder under the path to the system environment variable and name it as variable name
#           Args:
#               variable_path: system environment variable name
#               variable_name: value of the system environment variable which should be a path
#           Returns:
#               No
#           Raises:
#               RuntimeError: If any errors
#           Example:
#               Simplest usage: check key 'end' in /root/.bashrc file
#                     add_path_to_environment('SCRIPT', '')
#     """
#     listdir = os.listdir(variable_path)
#     if len(listdir) != 1:
#         raise Exception(f"path to be added to the system environment should contain exactly one file")
#     else:
#         _, out, err = lnx_exec_command('ll')
# out='''
# total 14404
# -rw-r--r-- 1 root  root   443019 Oct 21 16:01 632506-0.7-intel-qat-getting-start                                                                                                                               ed-guide-v2.0.pdf
# -rw-r--r-- 1 root  root   426964 Oct 21 16:00 632507-0.9-qat-software-for-linux-                                                                                                                               release-notes-hardware-v2.0.pdf
# -rw-rw-rw- 1 40281 22537    2015 Aug  9  2021 binary-redistribution-license.txt
# drwxr-xr-x 2 root  root     4096 Mar 23 19:35 build
# -rwxrwxrwx 1 40281 22537   45297 Aug  9  2021 config.guess
# -rw-r--r-- 1 root  root     7276 Mar 23 19:32 config.h
# -rw-rw-rw- 1 40281 22537    6913 Aug  9  2021 config.h.in
# -rw-r--r-- 1 root  root    61440 Mar 23 19:32 config.log
# -rwxrwxrwx 1 40281 22537    7292 Oct 14 23:30 config.sh
# -rwxr-xr-x 1 root  root    37133 Mar 23 19:32 config.status
# -rwxrwxrwx 1 40281 22537   35533 Aug  9  2021 config.sub
# -rwxrwxrwx 1 40281 22537  333520 Oct 14 23:28 configure
# -rwxrwxrwx 1 40281 22537    4089 Oct 14 23:30 config_vqat.sh
# -rw-rw-rw- 1 40281 22537   61732 Oct 14 23:31 filelist
# -rwxrwxrwx 1 40281 22537   13997 Aug  9  2021 install-sh
# -rw-rw-rw- 1 40281 22537    1599 Aug  9  2021 LICENSE.BSD
# -rw-rw-rw- 1 40281 22537   17987 Aug  9  2021 LICENSE.GPL
# -rw-rw-rw- 1 40281 22537    6121 Aug  9  2021 LICENSE.OPENSSL
# -rw-r--r-- 1 root  root    73093 Mar 23 19:32 Makefile
# -rw-rw-rw- 1 40281 22537   79223 Oct 14 23:28 Makefile.in
# -rwxrwxrwx 1 40281 22537    6873 Aug  9  2021 missing
# -rw-r--r-- 1 root  root  6972861 Mar 23 19:32 qat20.l.0.8.0-00071_4.zip
# -rw-r--r-- 1 root  root  6036566 Oct 19 12:15 QAT20.L.0.8.0-00071.tar.gz
# drwxrwxrwx 7 40281 22537     102 Oct 14 23:31 quickassist
# -rw-rw-rw- 1 40281 22537    9254 Aug  9  2021 README
# drwxr-xr-x 2 root  root      237 Oct 21 10:47 Report
# -rw-r--r-- 1 root  root       23 Mar 23 19:32 stamp-h1
# -rw-rw-rw- 1 40281 22537     165 Oct 14 23:30 versionfile
# '''
# line_list = out.strip().split('\n')
# for line in line_list:
#     if line[0] == 'd':
#         file_name =line.split(' ')[-1]
#         print(file_name)
    #             lnx_exec_command(
    #                 'echo export ' + variable_name + '=' + variable_path + '/' + file_name + '>> $HOME/.bashrc', timeout=60)
    #     file_name = listdir[0]
    # _, out, err = lnx_exec_command(
    #     'echo export ' + variable_name + '=' + variable_path + '/' + file_name + '>> $HOME/.bashrc', timeout=60)

#
# if __name__ == '__main__':
#     args_parse = setup_argparse()
#     add_path_to_environment(args_parse.name, args_parse.path)
# cd $API_SCRIPT && python3 $API_SCRIPT/lnx_exec_with_check.py  -c 'ls |grep cpa'

# python3 lnx_exec_with_check.py -c 'ls -l' -t 20
# from src.accelerator.acce_hls.apiscripts.lnx_exec_with_check import lnx_exec_command
#
#
# def get_folder_name(variable_path):
#     _, out, err = lnx_exec_command('ll', cwd=variable_path)
#     line_list = out.strip().split('\n')
#     for line in line_list:
#         if line[0] == 'd':
#             file_name = line.split(' ')[-1]
#             print(file_name)
#

if '':
    print('pass')
else:
    print('fail')
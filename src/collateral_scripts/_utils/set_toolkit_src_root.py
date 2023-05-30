import sys
import platform

# print(sys.path)

# This is compatible with Auto toolkit
is_auto_toolkit = False
sys_test = 'src\\system_test'
spl_cont = 'src\\sample_content'
if platform.system().lower() != 'windows':
    sys_test = sys_test.replace('\\', '/')
    spl_cont = spl_cont.replace('\\', '/')
if sys_test in sys.path[0] or spl_cont in sys.path[0]:
    sys.path[0] = sys.path[0].split('src')[0] + 'src'
    is_auto_toolkit = True

# This is for dtaf content
if not is_auto_toolkit:
    test_toolkit = 'test\\toolkit' if platform.system().lower() == 'windows' else 'test/toolkit'
    if test_toolkit in sys.path[0]:
        sys.path[0] = sys.path[0].split(test_toolkit)[0]
    elif 'src' in sys.path[0]:
        sys.path[0] = sys.path[0].split('src')[0]

# print(sys.path)

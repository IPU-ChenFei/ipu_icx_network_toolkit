import os

IMPORT_AUTO_API_SENTENCE = 'from src.lib.toolkit.auto_api import *\n'
IMPORT_SET_TOOLKIT_SRC_ROOT_SENTENCE = 'import set_toolkit_src_root\n'
NOINSPECTION_UNRESOLVED_REFERENCES_SENTENCE = '# noinspection PyUnresolvedReferences\n'

# configuration
# folder name under src folder
domain_name = "accelerator"

root_dir = os.path.abspath(__file__).split('src')[0]
domain_dir = os.path.join(root_dir, 'src', domain_name)

count = 0
for root, dirs, files in os.walk(domain_dir):
    for file in files:
        if not str(file).endswith('.py'):
            continue

        file_path = os.path.join(root, file)
        with open(file_path, 'r', encoding='utf-8') as fs:
            file_content = fs.readlines()

        if IMPORT_AUTO_API_SENTENCE in file_content:
            # remove old
            if IMPORT_SET_TOOLKIT_SRC_ROOT_SENTENCE in file_content:
                file_content.remove(IMPORT_SET_TOOLKIT_SRC_ROOT_SENTENCE)
            if NOINSPECTION_UNRESOLVED_REFERENCES_SENTENCE in file_content:
                file_content.remove(NOINSPECTION_UNRESOLVED_REFERENCES_SENTENCE)

            # add new
            auto_api_import_index = file_content.index(IMPORT_AUTO_API_SENTENCE)
            file_content.insert(auto_api_import_index, IMPORT_SET_TOOLKIT_SRC_ROOT_SENTENCE)
            file_content.insert(auto_api_import_index, NOINSPECTION_UNRESOLVED_REFERENCES_SENTENCE)

            with open(file_path, 'w', encoding='utf-8') as fs:
                fs.writelines(file_content)
            print(f'file {file_path} has been changed')
            count += 1

print(f'\n{count} files have been changed')

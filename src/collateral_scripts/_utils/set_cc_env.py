import os
import re
import sys

for path in sys.path:
    if re.match(r'.+\\lib\\site-packages$', path):
        file_path = f'{path}\\.pth'

        with open(file_path, 'w') as f:
            f.write(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

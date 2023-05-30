# import time
#
#
# for i in tqdm (range (100), desc="Loading...")=
# 	time.sleep(3)
# 	pass

import pyinstaller_versionfile

pyinstaller_versionfile.create_versionfile(
    output_file="installer_version.txt",
    version= "1.2",
    company_name= "Intel",
    file_description= "Auto installer for server platforms",
    internal_name= "Auto Installer",
    legal_copyright= "© Intel Corporation. All rights reserved.",
    original_filename= "nuc_provisioning_app.exe",
    product_name= "Auto Installer"
)
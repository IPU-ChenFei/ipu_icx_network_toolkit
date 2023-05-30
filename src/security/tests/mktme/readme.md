## MKTME Setup Instructions
### Introduction
For EagleStream, test content should be run on Windows. Linux OSs and VMware ESXi is not a POR OS for EGS and is a POC not covered at this time by Platform Validation.

For Windows, a strictly controlled POC release will be used for Platform Validation testing.  Unless otherwise stated in the test case, the scripts for Windows and Linux should be interchangeable.  Please note that the automation will 
determine if Windows or Linux is being used by the \<sut\> tags in the system_configuration.xml file in C:\Automation on the lab host.  If you require access to the Windows POC image, please contact your validation lead.  

### Minimum hardware/software configuration
#### Non-CAPI system configurations
1. AC cycle:  RSC2, OneCloudApi or Banino
2. BIOS : Serial Connections(COM)
3. PythonSV
4. CScripts
5. OpenIPC
6. OpenSSH
7. ITP Unlocker

### Setup Instructions
To run the following test cases successfully, the following set up is required.
1. MKTME enabled host OS must be installed following the corresponding test case.  This process is not yet automated.
2. A Windows/Linux VM image must exist in the prescribed location in the content_configuration.xml file.  The creation of said VM image has not yet been automated.
3. The user credentials must be set up to use ITP Unlocker credential caching for the unlock to function.
4. Verify the following fields are completed in the content_configuration.xml file:<mktme>
    ```xml
    <mktme>
        <windows>
            <!-- AC cycle instead of warm reset from OS -->
            <ac_reset>True</ac_reset>
            <!-- MKTMETool.efi tool location-->
            <mktme_tool_path_host>C:\Automation\bkc\tools\MKTMETool\MKTMETool.efi</mktme_tool_path_host>
            <vm_guest_image>
                <!-- td guest user name -->
                <vm_guest_user>Administrator</vm_guest_user>
                <!-- where TD guest user account password-->
                <vm_guest_user_password>Intel123</vm_guest_user_password>
                <!-- time to wait for VM to boot in seconds -->
                <vm_boot_time>120</vm_boot_time>
                <!-- guest OS specs -->
                <vm_os>WINDOWS</vm_os>
                <!-- base location for the custom tools to be copied in VM -->
                <vm_tools_base_loc>C:\Automation\Tools</vm_tools_base_loc>
                <!-- where to save imported VM images on SUT -->
                <vm_guest_image_dir>c:\mktmevm\images\</vm_guest_image_dir>
                <exported_vm_guest_image_path_sut>C:\tmp\22438\Virtual Machines</exported_vm_guest_image_path_sut>
                <exported_legacy_vm_image_path_sut>C:\tmp\22438\Virtual Machines</exported_legacy_vm_image_path_sut>
            </vm_guest_image>
        </windows>
        <linux>
            <!-- MKTMETool.efi tool location-->
            <mktme_tool_path_host>C:\Automation\bkc\tools\MKTMETool\MKTMETool.efi</mktme_tool_path_host>
        </linux>
    </mktme>
    ```
 
### Implementation Details

#### General
All VM related test cases are expecting a exported VM at a prescribed location in the SUT. The Windows test cases are expecting two kind of virtual mahines at exported location, legacy VM images and TD VM images.  Legacy VM images can be from recent Windows or Linux versions where as TD VM images has to be from MTC special builds.

			Virtualization TC Configuration details

Below are the Tag Names and expected values to be filled before running Virtualization testcases.

memory_size = will take value in MB and only take the input in integer format
as given. (default value provided in the configuration file)

no_of_cpu = will take the no of virtual cpu you required for the VM. Only 
take the input in integer format as given. (default value provided in the configuration file)

disk_size = VM virtual disk size, it will take value in GB. Only take 
the input in integer format as given. (default value provided in the configuration file)

os_variant = this tag is the version of the VM OS. It depends on the which OS want to 
flash in the VM. If ISO file is RHEL-8.1.x.x then os_variant will be 8.1. 
if iso file is RHEL-8.2.x.x then os_variant will be 8.2.

kernel_version = this tag is for the version of the kernel. (default value provided in the configuration file)

image_host_location = this tag needs to be filled up with the path of the ISO file which
 you want to flash on VM.  Path is expecting the complete path with the iso file. Requesting 
 you to make a folder structure like C:\Automation\BKC\VM_DETAILS\IMAGE and put the iso file under this path.
 
yum_repo = This tag is for yum repo files. This is an optional for now. So dont make any changes as and let it 
be as it is. (Will update this doc after enablement of the same feature)

Sample Configuration details:
<virtualization>
    <linux>
        <RHEL>
            <memory_size>4098</memory_size>
            <no_of_cpu>2</no_of_cpu>
            <disk_size>6</disk_size>
            <os_variant>8.2</os_variant>
            <kernel_version>3.3</kernel_version>
            <image_host_location>C:\Automation\BKC\VM_DETAILS\IMAGE\RHEL-8.2.0-20200404.0-x86_64-dvd1.iso</image_host_location>
            <yum_repo>C:\Automation\BKC\VM_DETAILS\RHEL_REPOS</yum_repo>
        </RHEL>
    </linux>
</virtualization>

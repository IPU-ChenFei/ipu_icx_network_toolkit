This is nested virtualization Test case.
Please Make sure that System Under Test SUT has atleasy 64GB free disk space.

For this Test, the CentOS image e.g. "centos-8.4.2105-embargo-installer-202108161742.iso" and
RHEL Image RHEL-8.2.0-20200404.0-x86_64-dvd1.iso must be present
in the directory as per path given in content_configuration.xml file for CENTOS
as given example below.
One can download latest CentOS Image from the latest BKC path, e.g. https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202108161742/images/
<CENTOS>
    <ISO>
        <memory_size>4098</memory_size>
        <no_of_cpu>2</no_of_cpu>
        <disk_size>20</disk_size>
        <os_variant>8</os_variant>
        <kernel_version>4.18</kernel_version>
        <image_host_location>C:\Automation\BKC\VM_DETAILS\IMAGE\centos-8.4.2105-embargo-installer-202108161742.iso</image_host_location>
        <yum_repo>C:\Automation\BKC\Tools\RHEL_REPOS.zip</yum_repo>
        <!-- Put the free MAC id which is registered in IT portal
        example: <mac_id>52:54:00:83:CE:82, 52:54:00:BA:84:11</mac_id>-->
        <mac_id>52:54:00:9a:1e:e2, 52:54:00:96:70:dd, 52:54:00:15:da:b3, 52:54:00:04:87:94, 52:54:00:96:70:dd</mac_id>
    </ISO>
</CENTOS>

OR

<CENTOS>
    <ISO>
        <memory_size>4098</memory_size>
        <no_of_cpu>2</no_of_cpu>
        <disk_size>20</disk_size>
        <os_variant>8</os_variant>
        <kernel_version>4.18</kernel_version>
        <image_host_location>C:\Automation\BKC\Tools\centos-8.4.2105-embargo-installer-202108161742.iso</image_host_location>
        <yum_repo>C:\Automation\BKC\Tools\RHEL_REPOS.zip</yum_repo>
        <!-- Put the free MAC id which is registered in IT portal
        example: <mac_id>52:54:00:83:CE:82, 52:54:00:BA:84:11</mac_id>-->
        <mac_id>52:54:00:9a:1e:e2, 52:54:00:96:70:dd, 52:54:00:15:da:b3, 52:54:00:04:87:94, 52:54:00:96:70:dd</mac_id>
    </ISO>
</CENTOS>

for nested VM Image please use below only...
<RHEL>
    <ISO>
        <memory_size>4098</memory_size>
        <no_of_cpu>2</no_of_cpu>
        <disk_size>6</disk_size>
        <os_variant>8.2</os_variant>
        <kernel_version>4.18</kernel_version>
        <image_host_location>C:\Automation\BKC\Tools\RHEL-8.2.0-20200404.0-x86_64-dvd1.iso</image_host_location>
        <yum_repo>C:\Automation\BKC\Tools\RHEL_REPOS.zip</yum_repo>
        <!-- Put the free MAC id which is registered in IT portal
        example: <mac_id>52:54:00:83:CE:82, 52:54:00:BA:84:11</mac_id>-->
        <mac_id>52:54:00:9a:1e:e2, 52:54:00:96:70:dd, 52:54:00:15:da:b3, 52:54:00:04:87:94, 52:54:00:96:70:dd</mac_id>
    </ISO>
    <VM_Template>
        <no_of_cpu>2</no_of_cpu>
        <disk_size>6</disk_size>
        <os_variant>8.2</os_variant>
        <kernel_version>4.18</kernel_version>
        <template_host_location>C:\Automation\BKC\VM_DETAILS\IMAGE\RHEL-8.2.0-4.18-20200404.0-x86_64-dvd1.vhdx</template_host_location>
    </VM_Template>
</RHEL>
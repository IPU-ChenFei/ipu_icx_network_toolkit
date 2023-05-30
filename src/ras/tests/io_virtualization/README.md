RAS-Virtualisation

Below Configuration need to fill for these TC:

content_configuration.xml:

<virtualization>
        <linux>
            <RHEL>
				<ISO>
					<memory_size>4098</memory_size>
					<no_of_cpu>2</no_of_cpu>
					<disk_size>6</disk_size>
					<os_variant>8.2</os_variant>
					<kernel_version>4.18</kernel_version>
					<image_host_location>C:\Automation\BKC\Tools\RHEL-8.2.0-20200404.0-x86_64-dvd1.iso</image_host_location>
					<-- All required repo file need to zip eg: RHEL_REPOS.zip and path should be updated in below yem_repo tag--!> 
					<yum_repo>C:\Automation\BKC\Tools\RHEL_REPOS.zip</yum_repo>
				</ISO>
            </RHEL>
        </linux>
		
</virtualization>

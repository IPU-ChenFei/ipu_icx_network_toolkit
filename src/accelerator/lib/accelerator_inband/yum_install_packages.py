from lnx_exec_with_check import lnx_exec_command
from add_environment_to_file import add_environment_to_file
from log import logger

def rpm_install():
    """
          Purpose: To install rpm packages
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install rpm packages
                  rpm_install()
    """
    # rpm_list = ['git', 'grubby', 'wget', 'openssl-devel', 'libcurl-devel', 'protobuf-devel', 'yum-utils.noarch', 'zlib-devel.x86_64',
    #             'yasm systemd-devel', 'boost-devel.x86_64', 'libnl3-devel', 'gcc', 'gcc-c++',
    #             'libgudev.x86_64', 'libgudev-devel.x86_64', 'systemd*', 'boost-devel.x86_64', 'autoconf',
    #             'automake', 'libtool', 'pkgconf', 'rpm-build', 'rpmdevtools', 'asciidoc', 'xmlto', 'libuuid-devel',
    #             'json-c-devel', 'kmod-devel', 'libudev-devel', 'qemu*', 'abrt-cli', 'epel-release', 'autoconf',
    #             'automake', 'libtool', 'pkgconf', 'rpm-build', 'rpmdevtools', 'asciidoc', 'xmlto', 'libuuid-devel',
    #             'json-c-devel', 'kmod-devel', 'libudev-devel', 'msr-tools', 'epel-release', 'readline-devel',
    #             'xxhash-devel', 'lz4-devel']
    rpm_list = ['git', 'grubby', 'wget', 'automake', 'libtool', 'pkgconf', 'rpm-build', 'rpmdevtools', 'asciidoc',
                'xmlto', 'libuuid-devel', 'systemd-devel']
    add_environment_to_file('http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
    add_environment_to_file('HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
    add_environment_to_file('https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
    add_environment_to_file('HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
    add_environment_to_file('no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
    lnx_exec_command('yum groupinstall -y "Development Tools" --allowerasing', timeout=100 * 60)
    for rpm in rpm_list:
        ret, _, _ = lnx_exec_command(f'yum -y install {rpm}', timeout=60000)
        if ret != 0:
            logger.error('yum install fail')
            raise Exception('yum install fail')


if __name__ == '__main__':
    rpm_install()


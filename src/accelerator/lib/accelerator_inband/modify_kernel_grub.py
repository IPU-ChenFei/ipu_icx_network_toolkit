import sys
import argparse
from lnx_exec_with_check import lnx_exec_command


def modify_kernel_grub(vm_function, add_or_remove=True):
    """
          Purpose: Modify kernel grub file
          Args:
              vm_function: What config need to add/remove to grub file
              add_or_remove: Is add or remove config file
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Add 'intel_iommu=on,sm_on iommu=on no5lvl' function to kernel grub file
                  modify_kernel_grub('intel_iommu=on,sm_on iommu=on no5lvl', True)
    """

    _, out, err = lnx_exec_command('uname -r', timeout=60)
    if add_or_remove:
        ret, _, _ = lnx_exec_command(f'grubby --update-kernel=/boot/vmlinuz-{out.strip()} --args="{vm_function}"', timeout=60)
    else:
        ret, _, _ = lnx_exec_command(f'grubby --update-kernel=/boot/vmlinuz-{out.strip()} --remove-args="{vm_function}"', timeout=60)
    return ret


if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Modify kernel grub file and reboot!'
                    '--args <kernel argument> '
                    '--remove <remove or update> ')
    parser.add_argument('-a', '--args', default=None, dest='args', action='store', help=' What config need to add/remove to grub file')
    parser.add_argument('-r', '--remove', default=False, dest='remove', action='store',
                        help=' True for remove the args')
    parse_args = parser.parse_args(args)
    modify_kernel_grub(parse_args.args, not parse_args.remove)
    sys.exit(0)

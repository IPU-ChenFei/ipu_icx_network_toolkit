from toolpath import *
from lnx_exec_with_check import lnx_exec_command

def get_platform_version():
    """
          Purpose: get platform version
          Args:
              No
          Returns:
              version name
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage:
                    get_platform_version()
    """
    _,out,_ = lnx_exec_command('dmidecode |grep Version|grep -e EGS -e BHS')
    if 'EGS' in out:
        return 'EGS'
    elif 'BHS' in out:
        return 'BHS'
    else:
        return vm_platform
		
QAT_DEVICE_NUM = 4
DLB_DEVICE_NUM = 4
DSA_DEVICE_NUM = 4
IAX_DEVICE_NUM = 4
DEVICE_ID = {
        'EGS': {
            'QAT_DEVICE_ID': '4940',
            'DLB_DEVICE_ID': '2710',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4941',
            'DLB_VF_DEVICE_ID': '2711',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        },
        'BHS': {
            'QAT_DEVICE_ID': '4944',
            'DLB_DEVICE_ID': '2714',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4945',
            'DLB_VF_DEVICE_ID': '2715',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        }
    }

vm_platform = 'EGS'
platform = get_platform_version()
qat_id = DEVICE_ID[platform].get('QAT_DEVICE_ID')
dlb_id = DEVICE_ID[platform].get('DLB_DEVICE_ID')
dsa_id = DEVICE_ID[platform].get('DSA_DEVICE_ID')
iax_id = DEVICE_ID[platform].get('IAX_DEVICE_ID')
qat_vf_id = DEVICE_ID[platform].get('QAT_VF_DEVICE_ID')
dlb_vf_id = DEVICE_ID[platform].get('DLB_VF_DEVICE_ID')
qat_mdev_id = DEVICE_ID[platform].get('QAT_MDEV_DEVICE_ID')
dlb_mdev_id = DEVICE_ID[platform].get('DLB_MDEV_DEVICE_ID')
dsa_mdev_id = DEVICE_ID[platform].get('DSA_MDEV_DEVICE_ID')
iax_mdev_id = DEVICE_ID[platform].get('IAX_MDEV_DEVICE_ID')
qat_device_num = QAT_DEVICE_NUM
dlb_device_num = DLB_DEVICE_NUM
dsa_device_num = DSA_DEVICE_NUM
iax_device_num = IAX_DEVICE_NUM

if __name__ == '__main__':
    _, out, err = lnx_exec_command('cat /home/BKCPkg/accelerator_inband/toolpath.py', timeout=60)
    out = out.replace("f'{","$").replace("}","").replace("'","").replace(" ","")
    tool_list = out.strip().split('\n')
    for tn in tool_list:
        if len(tn.split('=')) !=2:
            continue
        print(f'importing {tn}')
        lnx_exec_command(f'source $HOME/.bashrc && echo "export {tn}" >> $HOME/.bashrc', timeout=60)
    print('all driver path import done')
#！/usr/bin/sh
#date:2021-1217
DEVICE_NAME="br0"
ifcfg="ifcfg-br0"
echo "============= start create $ifcfg======================"
if [ -f $ifcfg ];then
  rm -f $ifcfg
fi
# create
cat >> $ifcfg << EOL
DEVICE=$DEVICE_NAME
BOOTPROTO="dhcp"
ONBOOT='"yes"
TYPE="Bridge"
EOL
echo "============= copy $ifcfg======================"
# copy
dest='/etc/sysconfig/network-scripts'
cp -a $ifcfg $dest
rm -f $ifcfg
is_e=$(find "$dest/ifcfg-$1" | xargs grep -ri "BRIDGE=$DEVICE_NAME")
ADD_DEVICE="BRIDGE=$DEVICE_NAME"
if [ ! -n "$is_e" ];then
  echo "============= BRIDGE=$DEVICE_NAME >> $dest/ifcfg-$1======================"
  echo $ADD_DEVICE >> $dest/ifcfg-enp1s0
fi

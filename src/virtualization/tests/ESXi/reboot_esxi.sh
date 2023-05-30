#!/bin/bash
file_cycle="/vmfs/volumes/datastore1/cycle_number"
if [ -e $file_cycle ]
then
cycle_number=`cat $file_cycle`
if [ $cycle_number -le 1000 ]
then
cycle_number1=`expr $cycle_number + 1`
echo $cycle_number1 > $file_cycle
echo "begin to reboot in 120s..."
sleep 120
`reboot`
fi
else
echo "file not exists"
fi

#!/bin/bash

monitorProcess=`ps aux | grep  monitor.py | cut -d ' ' -f 8`

for pid in $monitorProcess
do
    `kill -9 $pid > /dev/null 2>&1`
done
# clear pyc files
rm ./uploadVideoToHDFS/*.pyc > /dev/null 2>&1
rm ./monitor.log
exit 0

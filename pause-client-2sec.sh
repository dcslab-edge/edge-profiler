#!/usr/bin/bash

echo Stop Client for 2 seconds...
pid=`ssh dcslab@147.46.240.226 "ps aux | grep img-dnn_client_networked | grep -v 'grep'" | awk '{print $2}'`
echo Stopping Client \($pid\) for 2 seconds...
pause=`ssh dcslab@147.46.240.226 "kill -STOP $pid"`
sleep 2

echo Resuming Client \($pid\)...
resume=`ssh dcslab@147.46.240.226 "kill -CONT $pid"`


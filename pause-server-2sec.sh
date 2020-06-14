#!/usr/bin/bash

echo Stop Server for 2 seconds...
pid=`ps aux | grep img-dnn_server_networked | grep -v 'grep' | awk '{print $2}'`
echo Stopping Server \($pid\) for 2 seconds...
kill -STOP $pid
sleep 2

echo Resuming Server \($pid\)...
kill -CONT $pid


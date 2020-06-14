#!/bin/bash
for QPS in 200 400 600 800 1000; do
echo QPS
python3.7 ./benchmark_launcher.py ../experiments/debug/multi_lc/test/tailbench-solo/img-dnn/th_2/ntail-umg-dnn-${QPS}

done
exit

#!/bin/bash

#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/GpuKMeansBatchGpu/all_max/ ../experiments/static-iso/jetson_tx2/GpuKMeansBatchGpu/cpu_cores_half/ ../experiments/static-iso/jetson_tx2/GpuKMeansBatchGpu/cpu_min_freq/ ../experiments/static-iso/jetson_tx2/GpuKMeansBatchGpu/cpu_percent_half/ ../experiments/static-iso/jetson_tx2/GpuKMeansBatchGpu/gpu_min_freq/

#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/SparkGPULRGpu/all_max/
#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/SparkGPULRGpu/cpu_cores_half/
#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/SparkGPULRGpu/cpu_min_freq/ 
#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/SparkGPULRGpu/cpu_percent_half/ 
#python3.6 benchmark_launcher.py ../experiments/static-iso/jetson_tx2/SparkGPULRGpu/gpu_min_freq/
echo Bench starts...

#workloads='GpuKMeansGpu GpuKMeansBatchGpu SparkDSLRGpu SparkGPULRGpu'

#jetson_configs='all_max cpu_cores_half cpu_min_freq cpu_percent_half gpu_min_freq'
#desktop_configs='all_max cpu_cores_half cpu_min_freq cpu_percent_half'

#exp_base_path='../experiments/static-iso/'
#node='jetson_tx2'
#node='desktop'

#for workload in $workloads
#do
#  cmd='python3.6 benchmark_launcher.py '+$exp_base_path+
#done

# ==========================

python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/GpuKMeansBatchCpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/GpuKMeansBatchGpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/GpuKMeansCpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/GpuKMeansGpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/SparkDSLRCpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/SparkDSLRGpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/SparkGPULRCpu
python3.6 benchmark_launcher.py ../experiments/single-node/jetson_tx2/solorun/sparkgpu/SparkGPULRGpu




echo All done...

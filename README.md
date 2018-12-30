#edge-profiler

이 repo는 성능을 측정하고자 하는 workload와, 
측정에 이용하는 profiler를 연결하여, 
workload의 수행 및 performance 측정을 자동화하는 코드를 담고 있다.

실행을 위해서는, git repo 경로 안에 config.json파일을 만들어 두어야 하며, 실행 결과 및 로그를 저장할 디렉토리를 지정해주어야 한다
python3.7 환경에서 실행

python3.7 benchmark_launcher.py <설정 파일 디렉토리>


##실험방법
edge-profiler로 특정 workload의 실행 성능을 측정하고 싶다면,

우선 workload 실행 설정 파일을 담을 디렉토리에 실행할 workload들을 지정하고 저장한 뒤,

git repo안의 config.json을 설정해준다

- 이 때, 'stream-ip-address'는 반드시  data-stream-python이 담겨있는 곳으로 지정해주어야함' 

위의 명령어로 benchmark_launcher.py를 실행해준다


##config.json
실행하려는 profiler및 benchmark의 설정을 담는다

- interval :  edge-iso와의 연동을 위해 200(ms)로 설정 필수
- events : 읽고자 하는 metric들의 나열
- benchmark : 실행하려는 benchmark들의 위치를 담는 코드
    - stream-ip-address : 'data-stream-python'이 위치해 있는 서버의 ip 주소. 해당 주소로 spark-submit 및 signal-invoker가 연결을 시도함

config.*.template.json 참조    
    
##<설정 파일 디렉토리>
실행하고자 하는 workload들의 아래의 설정들이 담긴 'config.json'을 보관하는 장소

해당 장소로 실험 결과들이 동시에 저장되기도한다

- 실행 workload명
- 실행 코어
- freq제한
- cpu 사용 percent 제한
- fg/bg 실행 설정
- post_script 코드 여부

local_config.*.template.json 참조

##benchmark
driver/ 안의 코드들로 정해져있는 workload를 탐색, 실행하도록 로드하는 코드공간

###benchmark/driver 
실행하고자 하는 workload들을 연결하는 driver code들을 담는 공간

아래 목록에 있는 benchmark 들을 지원

- Rodinia
- NPB
- Parsec
- Spec

edge-iso의 성능 측정을 위해 직접 만든 benchmark들의 driver code들은 아래와 같다

- sparkgpu_data_receiver_python.py
    - data-stream-python의 실행을 담당하는 코드
    - 'data-stream-python' 안의 'signal_invoker.py'를 별도의 프로세스로 생성하여 실행함
- sparkgpu_driver.py
    - SparkGPU의 GPU Example benchmark들의 실행을 담당하는 코드


##containers
각 프로파일러 및 message queue의 실행을 담당하는 코드들의 공간


##post_scripts
성능측정 이후의 추가 작업을 담당하는 코드






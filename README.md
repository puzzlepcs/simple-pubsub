# Simple Middleware based on Publish and Subscribe Model

## Test Environment
- OS: Ubuntu 16.04
- language: python 3.7.0, python 3.5.2
- ip 주소는 세 소스코드 모두 `127.0.0.1`를 사용했습니다. 

## 구현된 기능
- MessageBroker: `broker.py`
  - Topic Register Request 처리.
  - pub, sub 두 개의 딕셔너리로 topic의 owner 저장.
  - 어떤 사용자가 접속을 종료하면 해당 사용자의 subscribers 이나 publishers에게 해당 사용자가 접속을 종료했다고 알려줍니다.
  - match 관리: 
    - 사용자로부터 Topic Rgister Request를 받을 때 마다 match된 Subscriber 에게 REPORT를 보냅니다.
- Publisher: `publisher.py`
  - Matched Subscriber 에게 Data 전송.
    - PUB 커맨드로 publish 하면 저장되어 있는 구독자들에게 해당 데이터 전송.
  - Subscribe Request 처리
    - 구독 요청시 해당 토픽의 데이터를 전송. 
  - Multi-topic Publish 
- Subscriber: `subscriber.py`
  - 브로커로부터 온 REPORT 처리
    - REPORT에 새로운 publisher가 있다면 해당 publisher에게 Subscribe Request를 보냅니다.
  - Matched Publisher로부터 Data 수신. 
  - Multi-topic Subscribe

## 구현하지 못한 기능
- keep-alive 관련 기능.
- Pub-sub 동시 수행 기능
- file publish: publisher가 pub 할 당시 입력한 스트링만 subscribers에게 전달합니다.
- period 관련 기능: publisher가 가장 최신에 pub한 데이터만 한번 전송하게 됩니다. 

## Manual
브로커의 포트는 10020 으로 설정되어 있습니다.  
세 소스코드 모두 `format.py`을 사용합니다. 브로커를 먼저 실행하고 publisher/subscriber을 실행해 주십시오.
1. broker를 `python broker.py` 로 실행한다. 
  - `Ctrl+C` 로 종료합니다.
2. publisher를 `python publisher.py`로 실행한다. (여러개 실행 가능)
  - 실행 후 포트를 입력하면 publisher가 시작. 아래의 커맨드를 사용 할 수 있다.
    - `quit`: 해당 프로그램을 종료.
    - `pub [topicname]`: 해당 토픽을 publish
      - 띄어쓰기 기준으로 파싱하기 때문에 __토픽이름은 띄어쓰기 없이__ 입력해주시기 바랍니다.
    - `list` : 토픽과 저장된 데이터, 해당 토픽의 구독자들의 열람.
3. subscriber를 `python subscriber.py`로 실행한다. (여러개 실행 가능)
  - 실행 후 포트를 입력하면 subscriber가 시작. 아래의 커맨드를 사용 할 수 있다.
    - `quit`: 해당 프로그램을 종료.
    - `sub [topicname]`: 해당 토픽을 subscribe
      - 띄어쓰기 기준으로 파싱하기 때문에 __토픽이름은 띄어쓰기 없이__ 입력해주시기 바랍니다.
    - `list` : 토픽, 해당 토픽의 Publisher 열람.

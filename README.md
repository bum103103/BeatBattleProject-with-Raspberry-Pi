
# BeatBattle: 2인용 라즈베리 파이 게임

> **Reaction Game + Rhythm Game**  
> 라즈베리 파이 2대를 이용해, 두 명이 동시에 즐길 수 있는 반응속도 & 리듬게임 프로젝트

<br/>

## 프로젝트 소개 (Overview)

**BeatBattle**는 두 대의 라즈베리 파이와 물리 버튼(3개) & LED(3개)를 통해 구현한 **2인용 게임**입니다.  
웹 브라우저(Flask 기반)에서 게임을 제어할 수 있고, 다음과 같은 게임 모드를 지원합니다.

1. **Reaction Game**  
   - LED가 랜덤으로 점등되면, 해당 LED에 해당하는 버튼을 먼저 누른 플레이어가 점수를 획득하는 반응속도 대결 게임입니다.  
   - 틀린 버튼을 누르거나 타이밍이 안 맞으면 점수가 깎입니다.

2. **Rhythm Game**  
   - 미리 랜덤으로 생성된 “노트”가 시간차를 두고 떨어지는 방식  
   - 플레이어는 리듬에 맞춰 올바른 열(column)의 버튼을 누르면 점수를 얻을 수 있습니다.

플레이어 각각 **라즈베리 파이 1대**와 **3개의 물리 버튼**을 사용하며,  
서버 측에서는 **Flask 웹**으로 점수·게임 상태를 확인하고, **BGM 재생**도 컨트롤할 수 있습니다.

<br/>

## 주요 기능 (Features)

- **2인용 실시간 대결**: 각 라즈베리 파이가 ‘Player 1’, ‘Player 2’로 동작  
- **반응속도 게임(Reaction)**:  
  - LED가 랜덤 점등 -> 올바른 버튼을 누르는 데 걸리는 시간 대결  
  - 누가 먼저 맞추느냐에 따라 점수 획득/감소  
- **리듬게임(Rhythm)**:  
  - 랜덤 생성된 노트를 타이밍에 맞춰 버튼 입력  
  - 일정 범위(±200ms) 이내에 맞추면 점수 획득  
- **Flask 웹 UI**:  
  - 게임 모드 선택(Reaction / Rhythm)  
  - 게임 시작/중지, 점수 확인, BGM 재생/정지  
  - 리듬게임 노트가 화면에서 시각적으로 떨어지는 애니메이션  
- **BGM 재생**:  
  - `mpg123`를 사용해 mp3 파일을 재생/중지 가능  
- **GPIO 제어**:  
  - 버튼 입력 감지 / LED 점등 관리  

<br/>

## 데모

> - 추후 업데이트 예정

<br/>

## 기술 스택 (Tech Stack)

- **언어/프레임워크**:  
  - Python 3.x  
  - Flask (웹 서버 & 간단한 API)  
  - Socket (TCP) 통신  
  - RPi.GPIO (라즈베리 파이 GPIO 제어)  
- **프론트엔드**:  
  - HTML5, CSS, JavaScript  
  - (간단한 애니메이션, AJAX 통신)  
- **하드웨어**:  
  - 라즈베리 파이 2대  
  - 버튼 3개 & LED 3개 (각 플레이어당 버튼 3개, 서버 측에 LED 3개)  

<br/>

## 프로젝트 구조 (Directory Structure)

```bash
BeatBattle/
├─ server/
│   ├─ server.py           # Flask + Socket 서버
│   ├─ requirements.txt    # Python 패키지 의존성
│   └─ (Optional) bgm.mp3  # BGM 파일 (또는 외부에 보관)
├─ client/
│   └─ client.py           # 클라이언트 라즈베리 파이 코드
├─ templates/
│   └─ index.html          # Flask 템플릿 (웹 UI)
├─ .gitignore
├─ README.md               # 이 문서
└─ LICENSE
```

- **`server/`**:  
  - `server.py` 내부에서 Flask 웹 서버와 Socket 서버를 동시에 실행.  
  - Reaction 게임, Rhythm 게임 로직이 포함됨.  
  - `requirements.txt`에 `Flask`, `RPi.GPIO`, `mpg123` 관련 등 필요한 패키지 버전 명시  
- **`client/`**:  
  - `client.py`로 물리 버튼 입력을 감지해 Socket 메시지(“Button X”) 형태로 서버에 전송  
- **`templates/`**:  
  - Flask가 렌더링할 HTML(지금은 `index.html` 한 파일)  
- **`.gitignore`**:  
  - `__pycache__`, `*.pyc`, 임시 파일 등은 깃에 올라가지 않도록 처리  
- **`LICENSE`** :  
  - 이 프로젝트는는 MIT 라이선스를 따릅니다.

<br/>

## 설치 및 실행 방법 (Getting Started)

### 1) 사전 요구사항

- **하드웨어**:  
  - 라즈베리 파이 2대  
  - 각 파이에 버튼 3개가 GPIO 핀에 연결 (예: BCM 핀 15, 18, 23)  
  - LED 3개 (서버 파이에 연결, 또는 원하는 구조에 맞게 구성)  
  - 배선도(간단)  
    - 버튼은 PULL_DOWN 사용 → 눌리면 HIGH 감지  
    - LED는 GPIO.OUT으로 제어 (LOW = 켜짐, HIGH = 꺼짐)  

- **소프트웨어**:  
  - Python 3.x  
  - `pip install -r requirements.txt`  (Flask, RPi.GPIO 등)

### 2) 서버 실행

1. **이 저장소를 클론**합니다.
   ```bash
   git clone https://github.com/bum103103/BeatBattleProject-with-Raspberry-Pi.git
   cd BeatBattle/server
   ```
2. **패키지 설치**  
   ```bash
   pip install -r requirements.txt
   ```
3. **서버 실행**  
   ```bash
   python server.py
   ```
   - 정상 실행되면, Flask가 **포트 5000**에서 동작하고, 소켓 서버는 **포트 12346**에서 Listen.

### 3) 클라이언트 실행

1. **클라이언트용 라즈베리 파이**에서:
   ```bash
   cd BeatBattle/client
   python client.py
   ```
2. 스크립트가 실행되면, **버튼 입력**을 기다립니다.  
   - 버튼이 눌릴 때마다 서버로 “Button X” 메시지 전송.

### 4) 웹 브라우저 접속

- **다른 PC나 스마트폰**에서, 서버 파이의 IP:5000으로 접근  
  - 예) `http://192.168.0.10:5000`  
- 웹 UI에서 **게임 모드 선택 → Start Game** 클릭  
- Scores, BGM 제어, 리듬 게임 애니메이션 등을 확인

<br/>

## 동작 방식 (Architecture)

아래는 간단한 흐름도입니다. (텍스트로 예시)

```
[Player 1's Raspberry Pi] --socket--> 
        [Server Raspberry Pi: server.py + Flask] <--socket-- [Player 2's Raspberry Pi]
              |    
              └---> [Flask Web UI (index.html)] <--- Browser(PC/Phone)
```

- 각 클라이언트는 소켓으로 서버와 연결  
- 서버는 Flask 웹 서버를 동시에 구동하며, `/update` API 등으로 점수/상태를 반환  
- 브라우저(UI)에서 Start/Stop/BGM 요청 → Flask API → 서버 내부 로직 수행  
- 클라이언트(버튼 입력) → 서버(판정 로직) → 점수 업데이트 & 웹에 반영

<br/>

## 시연 & 결과 (결과, 성능, 느낀 점)

- **반응속도 측정**: 0.0x초 단위로 승부가 갈리는 박진감 있는 게임  
- **리듬게임**: ±200ms 오차 범위를 적용해 점수 판정, 버튼 타이밍 훈련에 유익  
- **확장 아이디어**:  
  - 4인용 확장, 더 난이도 높은 리듬게임(노트 속도 증가), 고급 UI/UX 적용 등

<br/>

## 개발자 정보 (About Me)

- **개발자**: 김범준/bum103103, 유정원/mahoora0
- **역할**: 김범준/기획, 하드웨어 배선, 소프트웨어 설계, 테스트  유정원/기획, 하드웨어 배선, 소프트웨어 설계, 테스트, 웹 UI
- **연락처**: 김범준/bum103103, 유정원/mahoora0

<br/>

## 라이선스 (License)

이 프로젝트는 [MIT License](./LICENSE)를 따릅니다.  
자유롭게 Fork/수정/재배포할 수 있지만, 출처 표기를 부탁드립니다.

<br/>

---

## FAQ (자주 묻는 질문)

- **Q**: 라즈베리 파이가 없으면 테스트가 불가능한가요?  
  **A**: 로컬 환경에서 일부 소켓/Flask 동작은 확인 가능하지만, 실제 버튼/LED 기능은 라즈베리 파이 환경이 필요합니다.

- **Q**: BGM 재생이 안 되는데요?  
  **A**: `mpg123` 패키지를 설치해야 합니다. `sudo apt-get install mpg123` 등으로 설치 후, `bgm.mp3` 파일이 존재해야 합니다.

- **Q**: GPIO 핀 번호는 어디서 바꿀 수 있나요?  
  **A**: `client.py`와 `server.py` 상단의 `BUTTON_PINS`, `LED_PINS` 값을 변경하면 됩니다.

<br/>

## 마치며

**BeatBattle**는 **라즈베리 파이 & 물리적 버튼**이라는 요소를 통해 네트워크 프로그래밍, Flask 웹, GPIO 제어, 간단한 게임 로직을 모두 다뤄 볼 수 있는 프로젝트입니다.  
부족한 부분도 많지만, 직접 배선하고 코드를 작성하며 **임베디드 + 네트워크 + 웹**을 통합했다는 점에서 의미가 크다고 생각합니다.

프로젝트에 관심이 있으시거나, 개선 제안/문의가 있다면 자유롭게 이슈(issues)를 남겨주세요.  
감사합니다!

---

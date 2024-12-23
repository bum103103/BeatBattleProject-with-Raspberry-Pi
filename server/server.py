"""
server.py
- 소켓 서버 + Flask 웹 서버가 동시에 동작하는 메인 서버 스크립트
- Reaction Game, Rhythm Game 두 가지 모드 지원
- 두 라즈베리 파이 클라이언트(Player 1, Player 2)와 소켓으로 통신
- Flask를 통해 웹 브라우저에서 게임 제어, 점수 확인, BGM 재생 등을 제공
"""

import threading
import RPi.GPIO as GPIO
import socket
import time
import random
import json
import subprocess
import os
from flask import Flask, render_template, jsonify, request

# 1. GPIO 설정
BUTTON_PINS = [15, 18, 23]  # 버튼 GPIO 핀 번호
LED_PINS = [16, 20, 21]     # Reaction 게임에서 사용할 LED 핀 번호 (반전제어: LOW=ON, HIGH=OFF)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 버튼 핀 초기화
for pin in BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# LED 핀 초기화
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # LED OFF (HIGH)

# 2. 전역 변수
scores = {"Player 1": 0, "Player 2": 0}  # 점수 저장
current_game = None     # 'reaction' / 'rhythm' / None
game_active = False
winner_declared = False
current_led = None
rhythm_notes = []
game_start_time = None

# 플레이어 소켓 연결
connections = {"Player 1": None, "Player 2": None}

# 멀티쓰레드 동시 접근을 위한 Lock
lock = threading.Lock()

# Flask 애플리케이션
app = Flask(__name__)

# 소켓 서버
server_socket = None

# 배경음악 재생 프로세스
bgm_process = None

###############################################################################
# Flask 라우트
###############################################################################
@app.route('/')
def home():
    """
    메인 페이지 렌더링(템플릿: index.html)
    """
    return render_template('index.html', scores=scores, current_game=current_game)

@app.route('/update')
def update():
    """
    클라이언트(브라우저)에서 일정 주기로 호출하여 게임 상태 갱신
    """
    game_status = {
        "scores": scores,
        "current_game": current_game,
        "game_active": game_active
    }
    return jsonify(game_status)

@app.route('/set_game', methods=['POST'])
def set_game():
    """
    웹 UI에서 게임 모드(reaction/rhythm)를 선택
    """
    global current_game
    data = request.json
    game = data.get('game')
    if game in ["reaction", "rhythm"]:
        with lock:
            current_game = game
        return jsonify({"status": "success", "current_game": current_game})
    else:
        return jsonify({"status": "fail", "message": "Invalid game mode"}), 400

@app.route('/start_game', methods=['POST'])
def start_game():
    """
    웹 UI에서 'Start Game' 버튼을 눌렀을 때 처리
    - 점수 초기화
    - game_active = True
    - 필요한 경우 노트 생성 등
    """
    global game_active, current_game, rhythm_notes, game_start_time, scores, winner_declared
    data = request.json
    game = data.get('game')
    if game not in ["reaction", "rhythm"]:
        return jsonify({"status": "fail", "message": "Invalid game mode"}), 400

    with lock:
        # 이미 다른 게임이 진행 중인 경우
        if game_active:
            return jsonify({"status": "fail", "message": "Another game is already active"}), 400

        # 게임 시작 설정
        current_game = game
        game_active = True
        scores["Player 1"] = 0
        scores["Player 2"] = 0
        winner_declared = False

        if current_game == "rhythm":
            # 리듬 게임 노트 생성
            rhythm_notes = generate_rhythm_notes()
            game_start_time = int(time.time() * 1000)  # 밀리초 기준 시작시간
        else:
            # Reaction 게임 LED를 바로 켜주기 위해 current_led, winner_declared 관리
            current_led = None  # reaction_game_loop에서 랜덤으로 켜줄 것

    return jsonify({"status": "started", "current_game": current_game})

@app.route('/stop_game', methods=['POST'])
def stop_game():
    """
    웹 UI에서 'Stop Game' 버튼을 눌렀을 때 처리
    - game_active = False
    - LED나 노트 목록 정리
    """
    global game_active, current_game, current_led, rhythm_notes
    data = request.json
    game = data.get('game')
    if game not in ["reaction", "rhythm"]:
        return jsonify({"status": "fail", "message": "Invalid game mode"}), 400

    with lock:
        # 해당 모드의 게임이 진행 중이 아닐 경우
        if not game_active or current_game != game:
            return jsonify({"status": "fail", "message": "Game is not active"}), 400

        # 게임 중지
        game_active = False
        if current_game == "reaction":
            if current_led is not None:
                control_led(current_led, turn_on=False)
                current_led = None
        elif current_game == "rhythm":
            rhythm_notes = []

        current_game = None

    return jsonify({"status": "stopped", "current_game": current_game})

@app.route('/get_notes')
def get_notes():
    """
    리듬 게임 노트 정보 반환
    (브라우저에서 노트 애니메이션을 위해 사용)
    """
    if current_game != "rhythm" or not game_active:
        return jsonify({"notes": []})
    return jsonify({"notes": rhythm_notes})

@app.route('/play_bgm')
def play_bgm():
    """
    BGM 재생 (mpg123 사용)
    """
    global bgm_process
    if bgm_process is not None:
        return "BGM is already playing.", 400

    bgm_path = 'bgm.mp3'  # 실제 BGM 파일 경로
    if not os.path.isfile(bgm_path):
        return f"BGM file not found: {bgm_path}", 404

    try:
        bgm_process = subprocess.Popen(['mpg123', bgm_path])
        return "BGM started."
    except Exception as e:
        return f"Failed to start BGM: {e}", 500

@app.route('/stop_bgm')
def stop_bgm():
    """
    BGM 중지
    """
    global bgm_process
    if bgm_process:
        bgm_process.terminate()
        bgm_process = None
        return "BGM stopped."
    else:
        return "BGM is not playing.", 400

###############################################################################
# 게임 로직 관련 함수
###############################################################################
def generate_rhythm_notes():
    """
    리듬 게임용 노트 목록 생성
    예시: 20개의 노트, 1초 간격, 총 3개 열 중 랜덤
    """
    notes = []
    num_notes = 20
    interval = 1000  # 밀리초(1초)
    for i in range(num_notes):
        time_ms = (i + 1) * interval
        column = random.randint(0, 2)  # 0~2 열
        notes.append({"time": time_ms, "column": column})
    return notes

def broadcast_message(message):
    """
    모든 플레이어 소켓에 동일한 메시지를 전송
    """
    for player, conn in connections.items():
        if conn:
            try:
                conn.sendall(message.encode())
            except Exception:
                connections[player] = None

def control_led(index, turn_on=True):
    """
    Reaction 게임에서 LED를 제어
    turn_on=True -> GPIO.LOW (켜짐)
    turn_on=False -> GPIO.HIGH (꺼짐)
    """
    GPIO.output(LED_PINS[index], GPIO.LOW if turn_on else GPIO.HIGH)

def handle_reaction_game(player, button_index):
    """
    Reaction Game 로직:
    - 현재 켜져 있는 LED와 동일한 버튼을 누르면 점수 +1
    - 틀리거나 타이밍이 맞지 않으면 점수 -1
    """
    global current_led, winner_declared, scores
    if not game_active or current_game != "reaction":
        # Reaction 게임이 아니거나 진행 중 아님
        scores[player] -= 1
        print(f"[Reaction] {player} pressed button at invalid time. Penalty! Scores: {scores}")
        broadcast_message(f"{player} pressed button at invalid time. Penalty! Scores: {scores}")
        return

    if not winner_declared:
        if current_led is not None:
            if button_index == current_led:
                # 정답
                scores[player] += 1
                print(f"[Reaction] {player} wins! Current scores: {scores}")
                broadcast_message(f"{player} wins! Current scores: {scores}")
                control_led(current_led, turn_on=False)
                current_led = None
                winner_declared = True
                # 다음 라운드 대기
                threading.Thread(target=wait_after_reaction, daemon=True).start()
            else:
                # 틀린 버튼
                scores[player] -= 1
                print(f"[Reaction] {player} pressed wrong button. Penalty! Scores: {scores}")
                broadcast_message(f"{player} pressed wrong button. Penalty! Scores: {scores}")
    else:
        # 이미 승자 나옴
        scores[player] -= 1
        print(f"[Reaction] {player} pressed button after reaction ended. Penalty! Scores: {scores}")
        broadcast_message(f"{player} pressed button after reaction ended. Penalty! Scores: {scores}")

def handle_rhythm_hit(player, button_index, hit_time):
    """
    Rhythm Game 로직:
    - 특정 열(column)에 특정 시간(time_ms)에 노트가 떨어짐
    - 플레이어가 버튼 누른 시점(hit_time)이 노트 시간 근처(±tolerance)면 점수 +1
    - 아니면 -1
    """
    global rhythm_notes, scores
    if not game_active or current_game != "rhythm":
        scores[player] -= 1
        print(f"[Rhythm] {player} pressed button at invalid time. Penalty! Scores: {scores}")
        broadcast_message(f"{player} pressed button at invalid time. Penalty! Scores: {scores}")
        return

    tolerance = 200  # 밀리초 오차 범위
    hit_success = False
    with lock:
        for note in rhythm_notes:
            if note['column'] == button_index:
                if abs(note['time'] - hit_time) <= tolerance:
                    # 노트 적중
                    scores[player] += 1
                    print(f"[Rhythm] {player} hit note at column {button_index + 1} | Scores: {scores}")
                    broadcast_message(f"{player} hit note at column {button_index + 1}")
                    rhythm_notes.remove(note)
                    hit_success = True
                    break
        if not hit_success:
            # Miss
            scores[player] -= 1
            print(f"[Rhythm] {player} missed or hit wrong note at column {button_index + 1}. Penalty! Scores: {scores}")
            broadcast_message(f"{player} missed or hit wrong note at column {button_index + 1}. Penalty! Scores: {scores}")

def wait_after_reaction():
    """
    Reaction Game에서 한 라운드 종료 후 3초 대기하고 다음 라운드를 시작
    """
    global winner_declared, current_led
    time.sleep(3)
    with lock:
        if game_active and current_game == "reaction":
            current_led = random.randint(0, 2)
            winner_declared = False
            print(f"[Reaction] Next LED: {current_led + 1}")
            broadcast_message(f"Next LED: {current_led + 1}")
            control_led(current_led, turn_on=True)

###############################################################################
# 게임 루프
###############################################################################
def game_loop():
    """
    두 가지 게임 모드를 감시/실행하는 루프
    - Reaction: reaction_game_loop 쓰레드
    - Rhythm:   rhythm_game_loop 쓰레드
    """
    threading.Thread(target=reaction_game_loop, daemon=True).start()
    threading.Thread(target=rhythm_game_loop, daemon=True).start()
    while True:
        time.sleep(1)

def reaction_game_loop():
    """
    Reaction 게임 진행 쓰레드:
    - game_active=True & current_game='reaction'이면 LED를 랜덤으로 켬
    - 누가 맞추면 wait_after_reaction()으로 3초 후 다시 LED 켬
    """
    global current_led, winner_declared
    while True:
        if game_active and current_game == "reaction":
            with lock:
                # LED 랜덤 선택
                current_led = random.randint(0, 2)
                winner_declared = False
            print(f"[Reaction] Next LED: {current_led + 1}")
            broadcast_message(f"Next LED: {current_led + 1}")
            control_led(current_led, turn_on=True)

            # 승자가 나올 때까지 대기
            while True:
                with lock:
                    if winner_declared or not game_active or current_game != "reaction":
                        break
                time.sleep(0.1)

            # 다음 라운드를 위한 대기
            time.sleep(3)
            with lock:
                if current_led is not None:
                    control_led(current_led, turn_on=False)
                    current_led = None

        else:
            time.sleep(1)

def rhythm_game_loop():
    """
    Rhythm 게임 진행 쓰레드:
    - 노트 목록(rhythm_notes)의 가장 마지막 시간까지 대기
    - 그 후 game_active=False로 전환
    """
    global rhythm_notes, game_start_time, game_active, current_game
    while True:
        if game_active and current_game == "rhythm":
            with lock:
                # 노트가 있으면 마지막 노트 시간 + 1초까지 대기
                if rhythm_notes:
                    total_time = max(note['time'] for note in rhythm_notes) + 1000
                else:
                    # 노트가 없으면 즉시 종료
                    total_time = 0

            if total_time > 0:
                time.sleep(total_time / 1000.0)

            with lock:
                if game_active and current_game == "rhythm":
                    # 모든 노트가 끝난 후 게임 종료
                    game_active = False
                    current_game = None
                    rhythm_notes.clear()
                print("[Rhythm] Rhythm game ended.")
        else:
            time.sleep(1)

###############################################################################
# 소켓 통신
###############################################################################
def handle_client(player, conn):
    """
    클라이언트(각각 Player 1, Player 2) 연결 스레드
    - 연결 시 "You are {player}" 전송
    - "Button X" 메시지 수신 시 현재 게임 모드에 맞춰 처리
    """
    try:
        welcome_message = f"You are {player}"
        conn.sendall(welcome_message.encode())
    except Exception:
        connections[player] = None
        return

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                print(f"{player} disconnected.")
                connections[player] = None
                broadcast_message(f"{player} has disconnected.")
                break

            if data.startswith("Button"):
                parts = data.split()
                if len(parts) == 2 and parts[0] == "Button":
                    try:
                        button_index = int(parts[1]) - 1  # 1~3 -> 0~2
                        with lock:
                            if current_game == "reaction":
                                handle_reaction_game(player, button_index)
                            elif current_game == "rhythm":
                                # hit_time = 현재시간 - 리듬게임 시작시간
                                if game_start_time is not None:
                                    hit_time = int(time.time() * 1000) - game_start_time
                                    handle_rhythm_hit(player, button_index, hit_time)
                    except ValueError:
                        print(f"[Error] Invalid button index from {player}: {data}")
    except Exception as e:
        print(f"[Error] {player} connection error: {e}")
    finally:
        connections[player] = None
        conn.close()

def accept_connections():
    """
    최대 2명의 플레이어(Player 1, Player 2) 연결을 수락
    2명이 이미 연결되어 있으면 추가 연결 거부
    """
    print("[Server] Waiting for players to connect...")
    while True:
        conn, addr = server_socket.accept()
        if connections["Player 1"] is None:
            connections["Player 1"] = conn
            player = "Player 1"
            print(f"{player} connected from {addr}")
            threading.Thread(target=handle_client, args=(player, conn), daemon=True).start()
            broadcast_message(f"{player} has connected.")
        elif connections["Player 2"] is None:
            connections["Player 2"] = conn
            player = "Player 2"
            print(f"{player} connected from {addr}")
            threading.Thread(target=handle_client, args=(player, conn), daemon=True).start()
            broadcast_message(f"{player} has connected.")
        else:
            print(f"[Server] Connection from {addr} rejected: already two players connected.")
            conn.sendall("Game is full.".encode())
            conn.close()

def main():
    """
    메인 함수:
    - 소켓 서버 초기화
    - 게임 루프 쓰레드 시작
    - Flask 앱 실행
    """
    global server_socket
    HOST = '0.0.0.0'  # 모든 인터페이스에서 수신
    PORT = 12346

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)

    # 게임 루프(Reaction, Rhythm) 시작
    threading.Thread(target=game_loop, daemon=True).start()

    # 플레이어 소켓 연결 수락
    threading.Thread(target=accept_connections, daemon=True).start()

    print(f"[Server] Socket server listening on {HOST}:{PORT}")
    print("[Server] Starting Flask app on port 5000...")

    # Flask 웹 서버 실행
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Flask server interrupted")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[Server] Shutting down due to KeyboardInterrupt")
    finally:
        GPIO.cleanup()
        if server_socket:
            server_socket.close()
        for conn in connections.values():
            if conn:
                conn.close()

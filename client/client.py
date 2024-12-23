"""
client.py
- 라즈베리 파이에서 물리 버튼(3개) 입력을 받아 서버에 전송
- 서버로부터 오는 메시지를 콘솔에 출력
"""

import socket
import threading
import RPi.GPIO as GPIO
import time
import sys

# GPIO 설정
BUTTON_PINS = [15, 18, 23]  # 버튼 GPIO 핀 번호
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for pin in BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# 서버 정보
HOST = '192.168.0.100'  # 서버 IP (환경에 맞게 변경)
PORT = 12346

# 소켓 생성
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
player_id = None  # "Player 1" 또는 "Player 2"

def send_button_press(button_number):
    """
    버튼이 눌렸을 때 서버에 "Button X" 형태로 전송
    """
    message = f"Button {button_number}"
    try:
        client_socket.sendall(message.encode())
        print(f"Sent: {message}")
    except socket.error as e:
        print(f"Error sending button press: {e}")

def monitor_buttons():
    """
    물리 버튼 상태 모니터링 (간단한 디바운스: 0.2초 sleep)
    버튼 눌림 감지 시 서버로 전송
    """
    while True:
        for i, pin in enumerate(BUTTON_PINS):
            if GPIO.input(pin) == GPIO.HIGH:
                send_button_press(i + 1)
                time.sleep(0.2)  # 디바운스
        time.sleep(0.05)

def listen_for_server():
    """
    서버로부터 오는 메시지를 계속 수신하여 콘솔에 출력
    """
    global player_id
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                print("[Client] Server disconnected.")
                break
            print(f"[Server] {data}")
            if data.startswith("You are"):
                # "You are Player X"에서 플레이어 ID 추출
                player_id = data.split(" ")[2]
                print(f"[Client] Assigned as {player_id}")
    except socket.error as e:
        print(f"[Client] Connection error: {e}")
    finally:
        GPIO.cleanup()
        sys.exit(0)

def main():
    """
    클라이언트 메인 함수:
    - 서버에 소켓 연결
    - 서버 수신 쓰레드, 버튼 모니터링 쓰레드 시작
    """
    try:
        client_socket.connect((HOST, PORT))
        print("[Client] Connected to the server!")
    except socket.error as e:
        print(f"[Client] Connection failed: {e}")
        sys.exit(1)

    # 서버 메시지 수신 스레드
    threading.Thread(target=listen_for_server, daemon=True).start()
    # 버튼 모니터링 스레드
    threading.Thread(target=monitor_buttons, daemon=True).start()

    # 메인 스레드는 그냥 대기
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Client] Shutting down client.")
    finally:
        client_socket.close()
        GPIO.cleanup()

if __name__ == '__main__':
    main()

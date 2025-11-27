# test_server.py
import requests
import json
import wave


# 1. 테스트용 더미 WAV 파일 생성 (1초짜리 무음 파일)
def create_dummy_wav(filename="test_audio.wav"):
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        wav_file.writeframes(b'\x00' * 44100 * 2)
    return filename


# 2. 테스트용 게임 상태 JSON (광화문 1395년 설명 시도)
test_game_state = {
    "chat_history": [],
    "current_heritage": {
        "name": "GwangHwaMoon",
        "completed": False,
        "keywords": [
            {
                "keyword": "1395",
                "sample_question": "When was it built?",
                "isDone": False
            },
            {
                "keyword": "King Taejo",
                "sample_question": "Who built it?",
                "isDone": False
            }
        ]
    },
    "retry_count": 0
}

# 3. 요청 보내기
url = "http://127.0.0.1:8000/interact"
dummy_wav = create_dummy_wav()

try:
    with open(dummy_wav, 'rb') as f:
        files = {'audio_file': ('test.wav', f, 'audio/wav')}
        data = {'request_data': json.dumps(test_game_state)}

        print(f"Sending request to {url}...")
        response = requests.post(url, files=files, data=data)

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            res_json = response.json()
            print("\n=== Server Response ===")
            print(f"User STT: {res_json.get('user_stt')}")
            print(f"Score: {res_json.get('pronunciation_score')}")
            print(f"NPC Response: {res_json.get('npc_response')}")
            print(f"Updated State: {res_json.get('updated_game_state')}")
        else:
            print("Error:", response.text)

except Exception as e:
    print(f"Connection Failed: {e}")
    print("Make sure the server is running! (uvicorn main:app --reload)")
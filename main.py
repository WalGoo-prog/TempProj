import time
import json
import whisper
import sounddevice as sd
import numpy as np
from thefuzz import fuzz
from gtts import gTTS
from playsound import playsound
import os  # (추가) 임시 파일 관리를 위함
import tempfile  # (추가) 임시 파일 생성을 위함

# (수정) 딕셔너리 키 오류 수정 ("keywords" -> "facts")
TRUTH_DB = {
    "gyeongbokgung": {
        "keywords": ["when", "who"],
        "facts": {
            "when": {"info": "It was first built in 1395."},
            "who": {"info": "It was built by King Taejo."}
        },
        "question_templates": {
            "when": "That looks amazing! Can you tell me *when* it was built?",
            "who": "I see! And *who* was the king who ordered its construction?"
        }
    }
}


# (수정) 고정된 파일 이름 대신 임시 파일을 사용하도록 변경
def play_npc_speech(text_to_speak, lang='en'):
    """
    gTTS로 고유한 임시 MP3 파일을 생성하고 재생한 뒤 즉시 삭제합니다.
    """
    print(f"NPC : {text_to_speak}")

    temp_file_path = None
    try:
        # 1. (수정) 고유한 이름을 가진 임시 파일을 생성 (delete=False로 설정)
        #    파일이 자동으로 삭제되지 않도록 하여 playsound가 접근할 수 있게 함
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file_path = temp_file.name
        temp_file.close()  # gTTS가 파일을 저장할 수 있도록 핸들을 닫음

        # 2. (수정) gTTS가 이 고유한 임시 파일에 음성을 저장
        tts = gTTS(text=text_to_speak, lang=lang)
        tts.save(temp_file_path)

        # 3. (수정) 임시 파일을 재생
        playsound(temp_file_path)

    except Exception as e:
        print(f"[gTTS/playsound Error] {e}")
        print("인터넷 연결을 확인하거나 gTTS API 제한을 확인하세요.")
        time.sleep(1)

    finally:
        # 4. (추가) 재생이 끝나면 (오류가 나더라도) 임시 파일을 삭제
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


SIMILARITY_THRESHOLD = 80


def get_next_keyword(asset_info, used_keywords):
    for keyword in asset_info["keywords"]:
        if keyword not in used_keywords:
            return keyword
    return None


def generate_npc_response(asset_name, used_keywords, last_user_answer, last_keyword, retry_count):
    asset_name_key = asset_name.lower().replace(" ", "")
    asset_info = TRUTH_DB.get(asset_name_key)
    if not asset_info:
        return {"NPC": "I don't know that asset.", "is_complete": True}

    is_correct = False
    model_answer = ""

    if last_keyword:
        model_answer = asset_info["facts"].get(last_keyword, {}).get("info", "")
        similarity = fuzz.ratio(last_user_answer.lower(), model_answer.lower())

        print(f"[SYSTEM] Similarity: {similarity}% (User: '{last_user_answer}' vs Model: '{model_answer}')")

        if similarity >= SIMILARITY_THRESHOLD:
            is_correct = True
        else:
            retry_count += 1
    else:
        is_correct = True

    if not is_correct and retry_count < 3:
        return {
            "npc_speech": f"That wasn't quite right. Please try saying it again. (Attempt {retry_count}/3)",
            "model_answer_hint": model_answer,
            "is_correct": False,
            "is_complete": False,
            "current_keyword": last_keyword,
            "used_keywords": used_keywords,
            "retry_count": retry_count
        }

    if last_keyword and last_keyword not in used_keywords:
        used_keywords.append(last_keyword)

    next_keyword = get_next_keyword(asset_info, used_keywords)

    if not next_keyword:
        final_speech = "Wow, you did a great job!"
        if not is_correct:
            final_speech = f"The correct answer was: '{model_answer}'. But thanks for trying! Let's move on."

        return {
            "npc_speech": final_speech,
            "model_answer_hint": "",
            "is_correct": True, "is_complete": True,
            "current_keyword": None, "used_keywords": used_keywords, "retry_count": 0
        }

    next_question = asset_info["question_templates"].get(next_keyword)
    next_model_answer = asset_info["facts"].get(next_keyword, {}).get("info")

    npc_speech = ""
    if not is_correct and retry_count >= 3:
        npc_speech = f"The correct answer was: '{model_answer}'. \nLet's try the next one. ... {next_question}"
    else:
        npc_speech = "Great! " + next_question if last_keyword else next_question

    return {
        "npc_speech": npc_speech,
        "model_answer_hint": next_model_answer,
        "is_correct": True,
        "is_complete": False,
        "current_keyword": next_keyword,
        "used_keywords": used_keywords,
        "retry_count": 0
    }


def get_user_speech_as_text(model, duration=5, samplerate=16000):
    print("\n...")
    print("=============== 녹음 시작 =============== ")
    print(f"=============== {duration} 초 동안 말하기 =============== ")
    myrecording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()
    print("=============== 녹음 완료 =============== ")
    audio_data = myrecording.flatten()
    result = model.transcribe(audio_data, language="en", fp16=False)
    text = result["text"].strip()
    if not text or text == ".":
        print("=============== 아무 것도 녹음되지 않음 =============== ")
        return ""
    print(f"녹음된 내용: '{text}'")
    return text


def main_game_loop():
    try:
        model = whisper.load_model("base.en")
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        return

    print("\n플레이어가 'Gyeongbokgung'에 접근했습니다.")

    current_asset = "Gyeongbokgung"
    used_keywords = []
    current_keyword = None
    last_user_answer = ""
    current_retry_count = 0

    print("\n[CLIENT] 페이즈 시작. 첫 질문 요청...")

    response_json = generate_npc_response(
        current_asset,
        used_keywords,
        last_user_answer,
        current_keyword,
        current_retry_count
    )

    npc_text = response_json["npc_speech"]
    current_keyword = response_json["current_keyword"]
    used_keywords = response_json["used_keywords"]
    is_phase_complete = response_json["is_complete"]
    current_retry_count = response_json["retry_count"]
    model_answer_hint = response_json["model_answer_hint"]

    play_npc_speech(npc_text)  # (수정) 변경된 함수 호출

    if model_answer_hint:
        print(f"    [HINT]: {model_answer_hint}")

    while not is_phase_complete:
        last_user_answer = get_user_speech_as_text(model, duration=5)

        if not last_user_answer:
            play_npc_speech("다시 말해주지 않을래?", lang='ko')
            print(f"[HINT]: {model_answer_hint}")
            continue

        print(f"\n[CLIENT] 유저 답변({last_user_answer})을 백엔드로 전송.")

        response_json = generate_npc_response(
            current_asset,
            used_keywords,
            last_user_answer,
            current_keyword,
            current_retry_count
        )

        npc_text = response_json["npc_speech"]
        current_keyword = response_json["current_keyword"]
        used_keywords = response_json["used_keywords"]
        is_phase_complete = response_json["is_complete"]
        current_retry_count = response_json["retry_count"]
        model_answer_hint = response_json["model_answer_hint"]

        play_npc_speech(npc_text)

        if not is_phase_complete and model_answer_hint:
            print(f"[HINT]: {model_answer_hint}")

    print("\n=============== 문화재 설명 페이즈 종료 =============== ")


if __name__ == "__main__":
    main_game_loop()
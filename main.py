# main.py

import os
import tempfile
import traceback
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import asyncio  # asyncio.to_thread 사용을 위해 필요

# ======== [1] 서비스 및 모델 임포트 ========
from models.data_models import GeminiRequestPayload, GeminiResponsePayload, ChatMessage, Heritage, KeywordItem
from services.stt_service import transcribe_audio
from services.gemini_service import generate_structured_reply
from services.azure_service import get_pronunciation_score
from services.tts_service import get_mp3_base64

# ======== [2] 상수 설정 ========
app = FastAPI()

# TTS Bypass: 미리 정의된 답변
PREDEFINED_RESPONSES = {
    "WELL_DONE": "Great, I got it clearly.",
    "WRONG_DESC": "It maybe wrong. Can you explain me again?",
    "NO_MIC": "I can't hear you. Can you say it again?",
    "BAD_PRONOUNCE": "I can't understand what you said. Can you say it again?",
    "DONE": "Well, I think it's enough. Let's move to next heritage."
}
# 발음 점수 임계값 설정 (70점 미만 시 BAD_PRONOUNCE로 간주)
PRONUNCIATION_THRESHOLD = 70


@app.post("/interact_with_json")
async def interact_with_json(
        audio_file: UploadFile = File(...),
        request_data: str = Form(...)  # Unity에서 JSON 문자열을 Form Data로 보냄
):
    """
    유니티에서 음성 파일과 JSON 데이터를 받아 처리하는 메인 엔드포인트.
    TTS Bypass 로직이 포함되어 있어, 특정 조건에서는 Gemini 호출을 건너뜁니다.
    """
    user_wav_path = None

    try:
        # 1. 요청 JSON 파싱 및 유효성 검증
        # Pydantic 모델을 사용하여 데이터 유효성 검사 및 객체화
        request_dict = json.loads(request_data)
        request_payload = GeminiRequestPayload.model_validate(request_dict)

        # 2. 오디오 파일 임시 저장
        user_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        user_wav_path = user_wav.name
        user_wav.write(await audio_file.read())
        user_wav.close()

        # 3. STT 변환 (비동기)
        user_text = await transcribe_audio(user_wav_path)

        # 4. 발음 점수 평가 (비동기)
        score = await get_pronunciation_score(user_wav_path, user_text)

        # 5. TTS Bypass 및 Gemini 호출 로직 분기
        npc_chat = ""
        final_game_status = "CONTINUE"

        # [조건 A: 마이크 입력 및 발음 점수 확인]
        if not user_text.strip() or (score < PRONUNCIATION_THRESHOLD and len(user_text.strip()) < 5):
            # STT 결과가 비었거나(마이크 문제/침묵) 발음이 너무 낮음
            npc_chat = PREDEFINED_RESPONSES["NO_MIC"]
            final_game_status = "BAD_INPUT"

        elif score < PRONUNCIATION_THRESHOLD and user_text.strip():
            # STT는 성공했으나 발음 점수가 임계값 미만
            npc_chat = PREDEFINED_RESPONSES["BAD_PRONOUNCE"]
            final_game_status = "BAD_PRONOUNCE"

        # [조건 B: 정상 입력 -> Gemini 호출]
        else:
            # UserInput을 Payload에 업데이트하고 Gemini에게 전달
            request_payload.user_input_text = user_text

            # 5-1. Gemini 구조화된 답변 생성 (비동기)
            gemini_result: GeminiResponsePayload = await generate_structured_reply(request_payload)

            npc_chat = gemini_result.npc_chat
            final_game_status = gemini_result.conversation_status

            # 클라이언트가 필요로 하는 추가 데이터(is_correct, next_keyword_seq 등)는
            # 이 함수의 반환 값에 명시적으로 추가하여 전달하거나
            # 클라이언트가 game_status를 보고 판단하도록 합니다.
            # 여기서는 편의상 Gemini의 응답 객체 전체를 JSON으로 변환해 함께 보낼 수 있습니다.

            # [추가: Gemini 평가 데이터를 응답에 직접 추가]
            gemini_evaluation = gemini_result.model_dump()

        # 6. 최종 NPC 답변 TTS 생성 및 Base64 인코딩 (비동기)
        audio_base64 = await get_mp3_base64(npc_chat)

        # 7. 최종 응답 반환 (클라이언트가 처리할 데이터)
        return {
            "user_stt": user_text,
            "npc_response": npc_chat,
            "pronunciation_score": score,
            "audio_base64": audio_base64,
            "game_status": final_game_status,
            "gemini_evaluation": gemini_evaluation if 'gemini_evaluation' in locals() else None
        }

    except Exception as e:
        # 예상치 못한 시스템 레벨 에러 발생 시 로그 출력 및 500 에러 반환
        print("================ UNEXPECTED SERVER ERROR ================")
        traceback.print_exc()
        # Clean up in case of unexpected crash before finally block could run fully
        try:
            if user_wav_path and os.path.exists(user_wav_path):
                os.remove(user_wav_path)
        except:
            pass
        raise HTTPException(status_code=500, detail="Unexpected server error occurred. Check server logs.")

    finally:
        # 임시 파일 정리 (try 블록 내부에서 닫았으므로, 삭제만 시도)
        try:
            if user_wav_path and os.path.exists(user_wav_path):
                os.remove(user_wav_path)
        except Exception as cleanup_error:
            print(f"File cleanup warning in finally: {cleanup_error}")

# 실행 명령어: uvicorn main:app --reload
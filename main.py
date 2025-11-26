import os
import tempfile
import traceback
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

from models.data_models import GameState, GeminiEvalRequest, ChatMessage, EvaluationLog
from services.stt_service import transcribe_audio
from services.azure_service import get_pronunciation_score
from services.gemini_service import evaluate_and_respond, generate_opening_question
from services.tts_service import get_mp3_base64
from utils.text_correction import correct_heritage_names
from utils.report_manager import save_heritage_report

app = FastAPI()


# [수정] start_conversation에서 강제 스킵 로직 제거 (클라이언트가 제어함)
@app.post("/start_conversation")
async def start_conversation(request_data: str = Form(...)):
    try:
        game_state = GameState.model_validate_json(request_data)

        # 현재 인덱스의 문화재 정보 가져오기
        current_heritage = game_state.heritages[game_state.current_index]

        # 타겟 키워드 (안 끝난 것)
        target_keyword_obj = next((k for k in current_heritage.keywords if not k.isDone), None)

        npc_text = ""
        if not target_keyword_obj:
            # 이미 다 끝난 곳에 억지로 요청을 보낸 경우 방어 코드
            npc_text = f"We have already finished touring {current_heritage.name}."
        else:
            # 오프닝 질문 생성
            npc_text = await generate_opening_question(
                "Foreign Friend",
                current_heritage.name,
                target_keyword_obj.keyword,
                target_keyword_obj.sample_question
            )

        game_state.chat_history.append(ChatMessage(role="npc", content=npc_text))
        audio_base64 = await get_mp3_base64(npc_text)

        return {
            "npc_response": npc_text,
            "audio_base64": audio_base64,
            "updated_game_state": game_state.model_dump()
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interact")
async def interact(audio_file: UploadFile = File(...), request_data: str = Form(...)):
    user_wav_path = None
    try:
        game_state = GameState.model_validate_json(request_data)
        current_heritage = game_state.heritages[game_state.current_index]
        target_keyword_obj = next((k for k in current_heritage.keywords if not k.isDone), None)

        if not target_keyword_obj:
            return {"npc_response": "This area is clear.", "updated_game_state": game_state.model_dump()}

        # --- (STT, 평가, Gemini 호출 로직은 기존과 동일) ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio_file.read())
            user_wav_path = tmp.name

        raw_stt = await transcribe_audio(user_wav_path)
        user_text = correct_heritage_names(raw_stt, current_heritage.name)
        pron_score = await get_pronunciation_score(user_wav_path, user_text)

        gemini_req = GeminiEvalRequest(
            npc_persona="Foreign Friend",
            user_input=user_text,
            pronunciation_score=pron_score,
            target_keyword=target_keyword_obj.keyword,
            sample_question=target_keyword_obj.sample_question,
            retry_count=game_state.retry_count
        )

        ai_result = await evaluate_and_respond(gemini_req)
        # ------------------------------------------------------

        final_npc_response = ai_result.reaction

        if ai_result.evaluation == "PASS":
            target_keyword_obj.isDone = True
            game_state.retry_count = 0

            # 남은 키워드 확인
            remain_keywords = [k for k in current_heritage.keywords if not k.isDone]

            if remain_keywords:
                # [A] 같은 문화재 내 다음 질문 (계속 진행)
                next_k = remain_keywords[0]
                next_q = await generate_opening_question(
                    "Foreign Friend", current_heritage.name, next_k.keyword, next_k.sample_question
                )
                final_npc_response = f"{ai_result.reaction} {next_q}"
            else:
                # [B] 현재 문화재 완료 -> [수정] 여기서 끝냄 (다음 문화재로 안 넘어감)
                current_heritage.completed = True
                save_heritage_report(game_state, current_heritage.name)

                # 종료 멘트만 생성
                final_npc_response = f"{ai_result.reaction} We learned everything about {current_heritage.name}. Let's move to another place!"

                # [중요] 인덱스 증가시키지 않음.
                # 클라이언트가 'completed=True'를 보고 스스로 UI를 닫게 만듦.
        else:
            # [실패] 기존 로직 유지
            if game_state.retry_count < 3:
                game_state.retry_count += 1
                final_npc_response = f"{ai_result.reaction} Could you say that again?"
            else:
                target_keyword_obj.isDone = True
                game_state.retry_count = 0

                remain_keywords = [k for k in current_heritage.keywords if not k.isDone]
                if remain_keywords:
                    next_k = remain_keywords[0]
                    next_q = await generate_opening_question("Friend", current_heritage.name, next_k.keyword,
                                                             next_k.sample_question)
                    final_npc_response = f"The answer is {target_keyword_obj.keyword}. {next_q}"
                else:
                    # 실패로 끝났지만 마지막 키워드였던 경우 -> 완료 처리
                    current_heritage.completed = True
                    save_heritage_report(game_state, current_heritage.name)
                    final_npc_response = f"The answer is {target_keyword_obj.keyword}. That's all for here."

        # 상태 반환
        game_state.chat_history.append(ChatMessage(role="user", content=user_text))
        game_state.chat_history.append(ChatMessage(role="npc", content=final_npc_response))
        audio_base64 = await get_mp3_base64(final_npc_response)

        return {
            "user_stt": user_text,
            "pronunciation_score": pron_score,
            "npc_response": final_npc_response,
            "feedback": ai_result.feedback_korean,
            "audio_base64": audio_base64,
            "updated_game_state": game_state.model_dump()
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if user_wav_path and os.path.exists(user_wav_path):
            try:
                os.remove(user_wav_path)
            except:
                pass
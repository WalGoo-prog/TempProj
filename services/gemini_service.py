# services/gemini_service.py (수정됨)
import google.generativeai as genai
import asyncio
import json
from models.data_models import GeminiRequestPayload, GeminiResponsePayload

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=GEMINI_API_KEY)

try:
    # JSON Mode를 사용하기 위해 1.5-flash 권장
    GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"CRITICAL: Gemini Model initialization failed. {e}")
    GEMINI_MODEL = None


def blocking_generate_structured_reply(request_payload: GeminiRequestPayload) -> GeminiResponsePayload:
    if GEMINI_MODEL is None:
        # 서비스 불가 시 안전한 응답 반환
        return GeminiResponsePayload(
            npc_chat="Gemini service is unavailable. Please check the API key.",
            is_correct=False,
            feedback_korean="API 서비스 오류",
            conversation_status="ERROR"
        )

    try:
        # Pydantic 객체를 JSON 문자열로 변환하여 Prompt에 포함
        prompt_content = request_payload.model_dump_json(indent=2)

        # 시스템 프롬프트: JSON 분석 및 답변 생성 지시
        system_instruction = f"""
        Analyze the following JSON payload. Your persona is defined in 'your_role'.
        1. Evaluate 'user_input_text' based on the 'heritage' and current 'keyword'.
        2. Generate the next question/reply in English and put it in 'npc_chat'.
        3. Determine if the user's response was correct (set 'is_correct').
        4. Provide brief Korean feedback.
        5. Set 'conversation_status' and 'next_keyword_seq' based on the conversation flow.

        Payload:\n{prompt_content}
        """

        # Gemini 호출 (JSON Mode 사용)
        response = GEMINI_MODEL.generate_content(
            system_instruction,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                # 응답 스키마를 Pydantic 모델에 맞춤
                response_schema=GeminiResponsePayload
            )
        )

        # 응답 문자열을 Pydantic 모델로 파싱하여 반환
        return GeminiResponsePayload.model_validate_json(response.text)

    except Exception as e:
        print(f"Gemini API Error during structured generation: {e}")
        return GeminiResponsePayload(
            npc_chat="I couldn't process the conversation data.",
            is_correct=False,
            feedback_korean=f"처리 중 오류 발생: {str(e)[:50]}",
            conversation_status="ERROR"
        )


async def generate_structured_reply(request_payload: GeminiRequestPayload) -> GeminiResponsePayload:
    return await asyncio.to_thread(blocking_generate_structured_reply, request_payload)
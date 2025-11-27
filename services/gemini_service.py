import google.generativeai as genai
import asyncio
from google.generativeai.types import GenerationConfig
from models.data_models import GeminiEvalRequest, GeminiEvalResponse


GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash')


# =================================================================
# [1] 유저 답변 평가 및 반응 (JSON 반환)
# =================================================================
def blocking_evaluate_and_respond(req: GeminiEvalRequest) -> GeminiEvalResponse:
    try:
        system_prompt = f"""
        You are {req.npc_persona}, a friendly guide.

        Current Goal: User needs to explain "{req.target_keyword}".
        Reference Answer: "{req.sample_question}"
        User Input: "{req.user_input}"
        Pronunciation Score: {req.pronunciation_score} (Threshold: 70)

        Task:
        1. Evaluate Meaning (PASS/FAIL).
           - PASS if user input conveys the meaning of "{req.target_keyword}".
        2. Evaluate Grammar.

        [IMPORTANT Output Rules]
        Return JSON with these keys:
        1. "evaluation": "PASS" or "FAIL"
        2. "reason": Internal reasoning.
        3. "reaction": NPC's VERBAL response. (e.g., "Exactly!", "Hmm...").
           - Keep it short (max 1 sentence). Do NOT include the next question here.
        4. "next_question": Leave empty "". (Logic handles this separately).
        5. "feedback_korean": Educational feedback.
           - If PASS but grammar error: Point it out gently.
           - If FAIL: Explain why without spoilers if possible.
        """

        response = GEMINI_MODEL.generate_content(
            system_prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )

        if not response.text:
            raise ValueError("Empty response")

        return GeminiEvalResponse.model_validate_json(response.text)

    except Exception as e:
        print(f"Gemini Eval Error: {e}")
        return GeminiEvalResponse(
            evaluation="FAIL",
            reason=f"Error: {e}",
            reaction="Sorry, I couldn't hear that clearly.",
            next_question="",
            feedback_korean="오류가 발생했습니다."
        )


# =================================================================
# [2] 오프닝 질문 생성 (첫 만남 / 같은 문화재 내 다음 질문)
# =================================================================
def blocking_generate_opening(persona, heritage, keyword, sample_q):
    try:
        prompt = f"""
        Role: You are {persona} at {heritage}.
        Task: Ask a question about "{keyword}".

        Reference Question: "{sample_q}"

        [STRICT RULES]
        1. Do NOT mention the answer "{keyword}" in your question.
        2. The user must say "{keyword}" to answer.
        3. Keep it simple (1-2 sentences).
        """
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text.strip()
    except:
        return sample_q


# =================================================================
# [3] 전환 질문 생성 (다른 문화재로 이동 시 - Hello 금지)
# =================================================================
def blocking_generate_transition(persona, prev_heritage, curr_heritage, keyword, sample_q):
    try:
        prompt = f"""
        Role: You are {persona}.
        Context: We just finished touring {prev_heritage} and moved to {curr_heritage}.

        Task:
        1. Say a very short transition phrase (e.g., "Now we are at {curr_heritage}").
        2. Immediately ASK a question about the new keyword "{keyword}".

        Reference Question: "{sample_q}"

        [STRICT RULES]
        - Do NOT say "Hello" or "Nice to meet you". We are already talking.
        - Do NOT mention the answer "{keyword}" in your question.
        """
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Now let's look at {curr_heritage}. {sample_q}"


# =================================================================
# [Async Wrappers]
# =================================================================
async def evaluate_and_respond(req):
    return await asyncio.to_thread(blocking_evaluate_and_respond, req)


async def generate_opening_question(persona, heritage, keyword, sample_q):
    return await asyncio.to_thread(blocking_generate_opening, persona, heritage, keyword, sample_q)


async def generate_transition_question(persona, prev_h, curr_h, keyword, sample_q):
    return await asyncio.to_thread(blocking_generate_transition, persona, prev_h, curr_h, keyword, sample_q)
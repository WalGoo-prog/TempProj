# models/data_models.py
from pydantic import BaseModel, Field
from typing import List, Optional


# ====================
# [1] User Chat History 모델
# ====================
class ChatMessage(BaseModel):
    seq: int = Field(description="다이얼로그 순서")
    char: str = Field(description="발화 주체 (user 또는 npc)")
    content: str = Field(description="발화 내용")


# ====================
# [2] Heritage Keywords 모델
# ====================
class KeywordItem(BaseModel):
    seq: int = Field(description="키워드 설명 순서")
    keyword: str = Field(description="설명해야 할 핵심 키워드")
    sample_question: str = Field(description="NPC가 참고할 질문 예시 (한국어)")


# ====================
# [3] Heritage Context 모델
# ====================
class Heritage(BaseModel):
    name: str = Field(description="문화재 이름")
    keywords: List[KeywordItem] = Field(description="설명해야 할 키워드 목록")
    current_keyword_seq: int = Field(description="현재 설명할 키워드의 seq 번호")


# ====================================================
# [4] Server -> Gemini Request Payload (요청 JSON)
# ====================================================
class GeminiRequestPayload(BaseModel):
    your_role: str = Field(description="Gemini의 페르소나 및 지시사항")
    chat_history: List[ChatMessage] = Field(description="현재까지의 대화 기록")
    heritage: Heritage = Field(description="현재 문화재 컨텍스트")
    user_input_text: str = Field(description="STT로 변환된 유저의 최근 발화 내용")  # Gemini가 평가할 내용

    # 예시 JSON과 일치하도록 Field 정의
    # your_roll : "너는 유저의 외국인 친구로서, request.json 의 'chat_history' 를 참고하여..."


# ====================================================
# [5] Gemini -> Server Response Payload (응답 JSON)
# ====================================================
class GeminiResponsePayload(BaseModel):
    # NPC가 유저에게 할 답변
    npc_chat: str = Field(description="Gemini가 생성한 영어 답변")

    # 유저 답변 평가 (로직에 따라 필드 추가 가능)
    is_correct: bool = Field(description="유저의 발화가 키워드 설명에 적절했는지 여부")
    feedback_korean: str = Field(description="유저 답변에 대한 간략한 한국어 피드백")

    # 다음 게임 상태 제어
    next_keyword_seq: Optional[int] = Field(description="설명할 다음 키워드 seq (대화 종료시 None)", default=None)
    conversation_status: str = Field(description="현재 대화 상태 (CONTINUE, KEYWORD_DONE, ASSET_DONE)")
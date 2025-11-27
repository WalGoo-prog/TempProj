from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict


# ==========================================
# [1] 게임 상태 관리 모델 (Unity <-> Server)
# ==========================================

class ChatMessage(BaseModel):
    role: str
    content: str


class EvaluationLog(BaseModel):
    turn_index: int
    user_input: str
    target_keyword: str
    pronunciation_score: float
    grammar_evaluation: str
    feedback: str


class KeywordStatus(BaseModel):
    keyword: str
    sample_question: str
    isDone: bool = False


class HeritageStatus(BaseModel):
    name: str
    completed: bool = False
    keywords: List[KeywordStatus]


class PersonaInfo(BaseModel):
    name: str
    gender: str


class GameState(BaseModel):
    save_slot_name: str = "default"
    last_updated: str = ""

    player_info: Optional[PersonaInfo] = None
    npc_info: Optional[PersonaInfo] = None

    chat_history: List[ChatMessage] = []
    evaluation_logs: List[EvaluationLog] = []
    heritages: List[HeritageStatus]
    current_index: int = 0
    retry_count: int = 0


# ==========================================
# [2] Gemini 서비스 내부 통신용 모델 (Server <-> Gemini)
# ==========================================

class GeminiEvalRequest(BaseModel):
    npc_persona: str
    user_input: str
    pronunciation_score: float
    target_keyword: str
    sample_question: str
    retry_count: int


class GeminiEvalResponse(BaseModel):
    evaluation: str = Field(description="PASS 또는 FAIL")
    reason: str = Field(description="판단 이유")
    reaction: str = Field(description="유저에게 할 말 (리액션)")
    next_question: Optional[str] = Field(default="", description="다음 질문")
    feedback_korean: str = Field(description="한국어 피드백")

    # [핵심 수정 1] evaluation 필드에 Bool 타입이 들어와도 처리하도록 수정
    @field_validator('evaluation', mode='before')
    @classmethod
    def parse_evaluation(cls, v):
        # 불리언(True/False)이 들어오면 문자열로 변환
        if isinstance(v, bool):
            return "PASS" if v else "FAIL"
        # 소문자(pass/fail)가 들어오면 대문자로 변환
        if isinstance(v, str):
            return v.upper()
        return v

    # [핵심 수정 2] next_question 필드에 null이 들어와도 처리하도록 수정
    @field_validator('next_question', mode='before')
    @classmethod
    def allow_none(cls, v):
        if v is None:
            return ""
        return v
using System;
using System.Collections.Generic;

// [1] 서버 응답 최상위 구조
[Serializable]
public class ServerResponse
{
    public string user_stt;
    public float pronunciation_score;
    public string npc_response;
    public string feedback;
    public string audio_base64;
    public GameState updated_game_state; // 서버가 갱신해준 게임 상태
}

// [2] 유저 및 NPC 정보 (세이브 파일용 - 이 부분이 없어서 에러 발생했음)
[Serializable]
public class PersonaInfo
{
    public string name;
    public string gender; // "Male", "Female"

    // 생성자
    public PersonaInfo(string n, string g)
    {
        name = n;
        gender = g;
    }
}

// [3] 게임 상태 (서버로 보내고, 서버에서 받는 핵심 데이터)
[Serializable]
public class GameState
{
    // --- [신규] 세이브 메타데이터 (에러 발생 원인 필드들) ---
    public string save_slot_name; // 예: "Save_Player1_..."
    public string last_updated;

    // --- [신규] 플레이어 & NPC 정보 ---
    public PersonaInfo player_info;
    public PersonaInfo npc_info;

    // --- 기존 게임 진행 데이터 ---
    public List<ChatMessage> chat_history = new List<ChatMessage>();
    public List<EvaluationLog> evaluation_logs = new List<EvaluationLog>();
    public List<HeritageStatus> heritages = new List<HeritageStatus>();
    public int current_index = 0;
    public int retry_count = 0;
}

// [4] 하위 데이터 모델들

[Serializable]
public class ChatMessage
{
    public string role; // "user" or "npc"
    public string content;

    public ChatMessage(string r, string c) { role = r; content = c; }
}

[Serializable]
public class EvaluationLog
{
    public int turn_index;
    public string user_input;
    public string target_keyword;
    public float pronunciation_score;
    public string grammar_evaluation; // PASS/FAIL
    public string feedback;
}

[Serializable]
public class HeritageStatus
{
    public string name;
    public bool completed;
    public List<KeywordStatus> keywords = new List<KeywordStatus>();
}

[Serializable]
public class KeywordStatus
{
    public string keyword;
    public string sample_question;
    public bool isDone;
}
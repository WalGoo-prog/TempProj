import os
from datetime import datetime
from models.data_models import GameState

# 로그 저장 경로
LOG_DIR = "logs/user_speech"

# 폴더가 없으면 생성
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def log_valid_utterance(game_state: GameState, user_text: str, score: float):
    """
    유효한 유저 발화를 텍스트 파일에 기록합니다.
    """
    # 1. 파일명 생성 (플레이어 이름_날짜.txt)
    player_name = "Player"
    if game_state.player_info and game_state.player_info.name:
        player_name = game_state.player_info.name

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{LOG_DIR}/{player_name}_{today}.txt"

    # 2. 현재 문맥 정보 가져오기
    current_heritage_name = "Unknown"
    target_keyword = "None"

    if game_state.current_index < len(game_state.heritages):
        heritage = game_state.heritages[game_state.current_index]
        current_heritage_name = heritage.name
        # 현재 타겟 키워드 찾기
        target_obj = next((k for k in heritage.keywords if not k.isDone), None)
        if target_obj:
            target_keyword = target_obj.keyword

    # 3. 로그 내용 포맷팅
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = (
        f"[{timestamp}] "
        f"Heritage: {current_heritage_name} | "
        f"Target: {target_keyword} | "
        f"Score: {score:.1f} | "
        f"Say: \"{user_text}\"\n"
    )

    # 4. 파일에 추가 (Append 모드)
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(log_line)
        print(f"[Logger] Saved utterance: {user_text}")
    except Exception as e:
        print(f"[Logger Error] Failed to save log: {e}")
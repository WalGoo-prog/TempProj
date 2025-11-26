import json
import os
from datetime import datetime
from models.data_models import GameState

REPORT_DIR = "reports"

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


def save_heritage_report(game_state: GameState, heritage_name: str):
    """
    문화재 투어가 종료되면 대화 기록과 평가 로그를 JSON으로 저장합니다.
    """
    filename = f"{REPORT_DIR}/{heritage_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    report_data = {
        "heritage_name": heritage_name,
        "completion_time": str(datetime.now()),
        "chat_history": [msg.model_dump() for msg in game_state.chat_history],
        "evaluations": [log.model_dump() for log in game_state.evaluation_logs]
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)

    print(f"Report saved: {filename}")
    return filename
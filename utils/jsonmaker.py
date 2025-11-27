import json
from pathlib import Path

file_path = Path(__file__).resolve()


prompt_txt_path = file_path.parent.parent / "models" / "prompt.txt"
request_json_path = file_path.parent.parent / "models" / "make_quest.json"
heritage_json_path = file_path.parent.parent / "models" / "heritage_data.json"

with open(prompt_txt_path, "r", encoding='utf-8') as f:
    prompt = f.read()
    f.close()

print(prompt)




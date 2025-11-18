import json


class Data:
    def __init__(self, chat = None, heritage = None):
        self._chat = chat
        self._heritage = heritage

    def get_chat(self):
        return self._chat

    def get_heritage(self):
        return self._heritage

    def get_data(self):
        res = dict()
        res["chat"] = self._chat
        res["heritage"] = self._heritage
        return res

    def set_heritage(self, heritage):
        self._heritage = heritage

    def set_chat(self, chat):
        self._chat = chat

def receive_resp():
    pass

def data_to_dict(data: Data):
    class_data = vars(data)

def make_req(data: Data):
    a = {
        "heritage" : "거북선",
        "chat" : {
            "id" : 1,
            "name" : "나나",
            "숫자" : [1,2,3]
        }
    }
    res = json.dumps(a, indent=4,ensure_ascii=False)
    return res

def parsing():
    res = dict()
    return res

file_path = 'GeoBukSeon.json'

# 세이브 파일 안에 있는 특정 문화재의 데이터 파일 찾기
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        sample_data = json.load(f)
except Exception as e:
    print(e)

not_used_keyword = sample_data["keywords"]["not_done"]


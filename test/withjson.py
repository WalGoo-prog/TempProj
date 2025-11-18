import json


class Data:
    def __init__(self, chat, keywords, heritage):
        _chat = chat
        _keywords = keywords
        _heritage = heritage


def receive_resp():
    pass


def make_req():
    a = {
        "keywords" : "임진왜란",
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

test_data = Data("반가워요", "keywords", "거북선")
res = make_req()
print(res)
azure_service.py 에 

AZURE_SPEECH_KEY = None
AZURE_REGION = "eastasia"

에 디코에 있는 키 넣으시면 됨

gemini_service.py 에도 키 넣어야됨

서버 실행은 cmd 로 프로젝트 디렉토리까지 가서 uvicorn main:app --reload

이 리포지토리에 키 포함해서 푸쉬하면 보안 그런거 없이 그냥 푸쉬됨 조심 

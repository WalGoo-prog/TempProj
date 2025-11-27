player 생성시 태그에 player

테스트용으로 현재 문화재 데이터는 광화문, 경희루만 존재

유니티 내에서 구역 설정 시 cylinder 생성-> HeritageTrigger.cs 연결 -> Inspector 창에서 Heritage Name 에 광화문, 경희루 영어로 입력 GyeongHoeRu, GwangHwaMoon

GameManager 오브젝트는 
1. 빈 오브젝트 생성, 이름 GameManager 로 설정
2. GameManager 에 VoiceGameManager.cs 연결
3. 하위 오브젝트에 캔버스 생성
4. 캔버스 하위에 3d object -> UI -> Panel 생성, 이름 ConversaitonUI 로 설정
5. 하위 오브젝트에 UI->버튼 2개 생성, UI->Text->Legacy->Text 4개 생성
6. 버튼 2개의 이름을 각각 record, exit 로 설정
7. Text 4개의 이름을  Subtitle, UserSubtitle, Status, Feedback 으로 설정
8. Add component -> Audio Source 추가
9. GameManager 의 Inspector 창에 있는 Voice Game Manager 에 UI Elements 들을 알맞게 설정, Audio Settings 에 GameManager 추가 

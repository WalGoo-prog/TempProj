# utils/text_correction.py
def correct_heritage_names(text: str, heritage_name: str) -> str:
    """
    Whisper STT 결과에서 발음이 비슷한 단어를 올바른 문화재 고유명사로 치환합니다.
    """
    text_lower = text.lower()

    # 예시 매핑 (실제로는 더 많은 데이터 필요)
    corrections = {
        "GwangHwaMoon": ["grand moon", "gwang hwa moon", "gang hwa mun"],
        "GyeongHeoiRu": ["kyung he ru", "gyeong heoi ru"],
        "Geobukseon": ["turtle ship", "go book sun"]
    }

    if heritage_name in corrections:
        for wrong_word in corrections[heritage_name]:
            if wrong_word in text_lower:
                # 대소문자 무시하고 치환 (간단한 구현)
                return text.replace(wrong_word, heritage_name)  # 실제로는 정규식 사용 권장

    return text
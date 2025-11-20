import whisper
import asyncio

# 서버 시작 시 모델 로드 (CPU 부하를 줄이기 위해 1회만 실행)
try:
    WHISPER_MODEL = whisper.load_model("base")
except Exception as e:
    print(f"CRITICAL: Whisper Model failed to load. {e}")
    WHISPER_MODEL = None


# STT 처리는 시간이 걸리는 블로킹 작업이므로, 비동기로 실행될 수 있도록 함수 정의
def blocking_transcribe(audio_path: str) -> str:
    if WHISPER_MODEL is None:
        return ""  # 모델 로드 실패 시 빈 문자열 반환

    try:
        # 실제 Whisper API/모델 호출
        result = WHISPER_MODEL.transcribe(audio_path)
        return result["text"].strip()
    except Exception as e:
        print(f"STT Error: {e}")
        return ""  # 오류 발생 시 빈 문자열 반환


async def transcribe_audio(audio_path: str) -> str:
    # 블로킹 함수를 별도 스레드에서 실행
    return await asyncio.to_thread(blocking_transcribe, audio_path)
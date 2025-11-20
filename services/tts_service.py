from gtts import gTTS
import asyncio
import io
import base64


def blocking_generate_mp3_bytes(text: str) -> bytes:
    if not text:
        return b""  # 텍스트가 없으면 빈 바이트 반환

    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception as e:
        print(f"gTTS Error: {e}")
        return b""  # 오류 발생 시 빈 바이트 반환


async def get_mp3_base64(text: str) -> str:
    mp3_bytes = await asyncio.to_thread(blocking_generate_mp3_bytes, text)
    if not mp3_bytes:
        return ""

    return base64.b64encode(mp3_bytes).decode("utf-8")
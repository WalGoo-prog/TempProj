import azure.cognitiveservices.speech as speechsdk
import asyncio

AZURE_SPEECH_KEY = "YOUR_KEY"
AZURE_REGION = "eastasia"


def blocking_assess_pronunciation(audio_path: str, reference_text: str) -> float:
    if "YOUR" in AZURE_SPEECH_KEY or not reference_text:
        return 0.0

    try:
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)

        # Pronunciation Assessment 설정
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme
        )

        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            return pronunciation_result.pronunciation_score
        else:
            print(f"Azure Recognition Failed: {result.reason}")
            return 0.0

    except Exception as e:
        print(f"Azure Assessment Exception: {e}")
        return 0.0  # 에러 발생 시 0점 반환


async def get_pronunciation_score(audio_path: str, reference_text: str) -> float:
    return await asyncio.to_thread(blocking_assess_pronunciation, audio_path, reference_text)
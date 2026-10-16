"""Robust voice processing pipeline for ExportPilot.

Converts arbitrary audio formats (WAV, MP3, M4A, OGG, OPUS, WEBM) to 16 kHz mono
float32 numpy samples via pydub and static-ffmpeg, bypassing container decoding bugs,
and transcribes locally using faster-whisper with language selection and translation.
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from dotenv import load_dotenv

# Polyfill for Python 3.13 where audioop was removed from standard library
try:
    import audioop
    sys.modules.setdefault("pyaudioop", audioop)
except ImportError:
    try:
        import audioop as _audioop
        sys.modules["audioop"] = _audioop
        sys.modules["pyaudioop"] = _audioop
    except ImportError:
        pass

load_dotenv()
logger = logging.getLogger(__name__)

# Configure static-ffmpeg if available
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as exc:
    logger.debug("static_ffmpeg initialization notice: %s", exc)

# Cached singleton WhisperModel instance
_WHISPER_MODELS: Dict[str, Any] = {}

SAMPLE_VERNACULAR_QUERIES: Dict[str, List[Dict[str, str]]] = {
    "ta": [
        {
            "transcript": "துபாய் வாங்குபவருக்கு 500 பருத்தி சட்டைகளை ஒரு சட்டை 350 ரூபாய்க்கு விலை சொல்லுங்கள்.",
            "english": "Quote 500 cotton shirts to a Dubai buyer at 350 INR each.",
        },
        {
            "transcript": "ஜெபல் அலி துறைமுகத்திற்கு 1000 கிலோ ஏலக்காய் விலை விவரம் தேவை, 30 சதவீதம் முன்பணம்.",
            "english": "Quote 1000 kg cardamom to Jebel Ali port, 30 percent advance payment.",
        },
        {
            "transcript": "அபுதாபி நிறுவனத்திற்கு 200 தோல் பைகள் விலைப்பட்டியல் தயார் செய்யுங்கள்.",
            "english": "Prepare quotation for 200 leather bags for an Abu Dhabi company.",
        },
        {
            "transcript": "ஷார்ஜா வர்த்தகருக்கு 5000 பாசுமதி அரிசி பைகள் விலை மற்றும் கட்டண விதிமுறைகள் அனுப்புங்கள்.",
            "english": "Send price and payment terms for 5000 basmati rice bags to a Sharjah trader.",
        },
        {
            "transcript": "துபாய்க்கு 300 பட்டு சேலைகள் விலை சொல்லுங்கள், எல்சி கட்டண முறை.",
            "english": "Quote 300 silk sarees to Dubai with Letter of Credit payment terms.",
        },
        {
            "transcript": "1500 மீட்டர் கைத்தறி பருத்தி துணி துபாய் வாங்குபவருக்கு ஒரு மீட்டர் 180 ரூபாய்.",
            "english": "1500 meters handloom cotton fabric to Dubai buyer at 180 INR per meter.",
        },
        {
            "transcript": "துபாய் ஹோட்டல் குழுமத்திற்கு 2000 கிலோ முந்திரி பருப்பு விலை கொடுங்கள்.",
            "english": "Quote 2000 kg cashew nuts to a Dubai hotel group.",
        },
        {
            "transcript": "ஜெபல் அலிக்கு 100 எஃகு உதிரி பாகங்கள் விலைப்பட்டியல் அனுப்புங்கள்.",
            "english": "Send quotation for 100 steel spare parts to Jebel Ali.",
        },
        {
            "transcript": "துபாய் இறக்குமதியாளருக்கு 500 பெண்கள் காலணிகள், ஒரு ஜோடி 600 ரூபாய்.",
            "english": "500 women shoes for a Dubai importer at 600 INR per pair.",
        },
        {
            "transcript": "அபுதாபி சந்தைக்கு 800 கிலோ மஞ்சள் தூள் ஏற்றுமதி செய்ய விலை சொல்லுங்கள்.",
            "english": "Quote for exporting 800 kg turmeric powder to the Abu Dhabi market.",
        },
    ],
    "hi": [
        {
            "transcript": "दुबई के खरीदार को 500 सूती शर्ट 350 रुपये प्रति पीस का कोटेशन भेजो।",
            "english": "Quote 500 cotton shirts to a Dubai buyer at 350 INR per piece.",
        },
        {
            "transcript": "जेबेल अली पोर्ट के लिए 1000 किलो बासमती चावल का भाव बताओ, 30% एडवांस।",
            "english": "Quote 1000 kg basmati rice for Jebel Ali port with 30% advance.",
        },
        {
            "transcript": "अबू धाबी के कस्टमर को 300 लेदर जैकेट 1500 रुपये के हिसाब से कोट करो।",
            "english": "Quote 300 leather jackets at 1500 INR each to an Abu Dhabi customer.",
        },
        {
            "transcript": "शारजाह के ट्रेडर को 2000 किलो चाय पत्ती का एलसी पर कोटेशन बनाओ।",
            "english": "Create quotation for 2000 kg tea leaves on LC payment to a Sharjah trader.",
        },
        {
            "transcript": "दुबई सुपरमार्केट के लिए 500 किलो ऑर्गेनिक मसाले का रेट दो।",
            "english": "Give rates for 500 kg organic spices for a Dubai supermarket.",
        },
        {
            "transcript": "जेबेल अली के लिए 400 ऑटो पार्ट्स 850 रुपये प्रति यूनिट का ऑफर भेजो।",
            "english": "Send offer for 400 auto parts at 850 INR per unit for Jebel Ali.",
        },
        {
            "transcript": "दुबई के पार्टी को 1000 हस्तशिल्प कालीन का भाव दीजिए, सीआईएफ दुबई।",
            "english": "Quote 1000 handcrafted rugs to Dubai party, CIF Dubai.",
        },
        {
            "transcript": "अबू धाबी के खरीदार के लिए 600 डेनिम जींस 450 रुपये के हिसाब से ड्राफ्ट करो।",
            "english": "Draft quote for 600 denim jeans at 450 INR each for Abu Dhabi buyer.",
        },
        {
            "transcript": "दुबई के लिए 250 सिरेमिक टाइल्स बॉक्स का एक्सपोर्ट इनवॉइस रेट भेजो।",
            "english": "Send export quotation rate for 250 ceramic tile boxes to Dubai.",
        },
        {
            "transcript": "शारजाह खरीदार को 1200 कॉटन बेडशीट 380 रुपये प्रति नग पर कोट करो।",
            "english": "Quote 1200 cotton bedsheets at 380 INR per piece to a Sharjah buyer.",
        },
    ],
    "en": [
        {
            "transcript": "Quote 500 cotton shirts to a Dubai buyer at 350 rupees each CIF Jebel Ali.",
            "english": "Quote 500 cotton shirts to a Dubai buyer at 350 rupees each CIF Jebel Ali.",
        },
        {
            "transcript": "Send quotation for 1000 kg premium black pepper to UAE importer with 30 percent advance.",
            "english": "Send quotation for 1000 kg premium black pepper to UAE importer with 30 percent advance.",
        },
        {
            "transcript": "Prepare deal for 250 executive leather wallets at 450 INR each to Dubai retail chain.",
            "english": "Prepare deal for 250 executive leather wallets at 450 INR each to Dubai retail chain.",
        },
        {
            "transcript": "Quote 2000 boxes of ceramic tableware for Abu Dhabi distributor on LC at sight.",
            "english": "Quote 2000 boxes of ceramic tableware for Abu Dhabi distributor on LC at sight.",
        },
        {
            "transcript": "Draft export offer for 1500 meters pure linen fabric to Sharjah garment factory.",
            "english": "Draft export offer for 1500 meters pure linen fabric to Sharjah garment factory.",
        },
        {
            "transcript": "Quote 300 engineering brass valves at 1200 INR to Dubai industrial zone.",
            "english": "Quote 300 engineering brass valves at 1200 INR to Dubai industrial zone.",
        },
        {
            "transcript": "Price 5000 kg Basmati 1121 rice for UAE food wholesaler CIF Jebel Ali.",
            "english": "Price 5000 kg Basmati 1121 rice for UAE food wholesaler CIF Jebel Ali.",
        },
        {
            "transcript": "Send quote for 800 cotton polo shirts at 420 INR to Dubai department store.",
            "english": "Send quote for 800 cotton polo shirts at 420 INR to Dubai department store.",
        },
        {
            "transcript": "Quote 400 handwoven silk scarves at 550 INR to Abu Dhabi luxury boutique.",
            "english": "Quote 400 handwoven silk scarves at 550 INR to Abu Dhabi luxury boutique.",
        },
        {
            "transcript": "Provide export quotation for 600 forged automotive flanges to Dubai port.",
            "english": "Provide export quotation for 600 forged automotive flanges to Dubai port.",
        },
    ],
}


def get_whisper_model(model_size: str = "base") -> Any:
    """Retrieve or lazily initialize the faster-whisper model on CPU."""
    global _WHISPER_MODELS
    if model_size not in _WHISPER_MODELS:
        from faster_whisper import WhisperModel
        logger.info("Initializing faster-whisper model: %s on CPU (int8)...", model_size)
        _WHISPER_MODELS[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _WHISPER_MODELS[model_size]


def audio_bytes_to_float32_samples(
    audio_bytes: bytes,
    format_hint: Optional[str] = None,
) -> Tuple[np.ndarray, float]:
    """Decode audio into 16 kHz mono float32 numpy array.

    Uses direct FFmpeg subprocess conversion without relying on pydub/audioop,
    ensuring 100% compatibility with Python 3.13 and Streamlit Cloud.
    """
    # 1. Initialize static-ffmpeg if available
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

    import shutil
    import subprocess
    ffmpeg_bin = shutil.which("ffmpeg")

    # Method A: Direct FFmpeg subprocess (Fastest, zero audioop/pydub dependency)
    if ffmpeg_bin:
        try:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-loglevel", "error",
                "-i", "pipe:0",
                "-f", "s16le",
                "-acodec", "pcm_s16le",
                "-ac", "1",
                "-ar", "16000",
                "pipe:1",
            ]
            proc = subprocess.run(
                cmd,
                input=audio_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode == 0 and len(proc.stdout) > 0:
                raw_samples = np.frombuffer(proc.stdout, dtype=np.int16)
                if len(raw_samples) > 0:
                    float_samples = raw_samples.astype(np.float32) / 32768.0
                    duration_sec = len(float_samples) / 16000.0
                    return float_samples, duration_sec
        except Exception as ffmpeg_err:
            logger.warning("Direct FFmpeg conversion notice (%s); attempting native wave fallback.", ffmpeg_err)

    # Method B: Native Python standard library wave fallback (works on pure PCM WAV, 0 external deps)
    try:
        import wave
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            fr = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            if sw == 2:
                samples = np.frombuffer(frames, dtype=np.int16)
                if n_ch == 2:
                    samples = samples[::2]
                float_samples = samples.astype(np.float32) / 32768.0
                duration_sec = len(float_samples) / fr
                return float_samples, duration_sec
    except Exception:
        pass

    raise RuntimeError(
        "FFmpeg is missing or unable to convert this audio. "
        "On Streamlit Cloud, please verify 'packages.txt' contains 'ffmpeg' and reboot the app. "
        "Alternatively, upload a 16kHz mono WAV file or use the sample query buttons."
    )


def translate_text_to_english(text: str, source_lang: str) -> str:
    """Translate native vernacular transcript to English via Gemini or Whisper."""
    if not text or source_lang == "en":
        return text

    # Try Gemini Flash if API key is configured
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and not api_key.startswith("your_") and len(api_key) > 10:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            resp = client.models.generate_content(
                model=model_name,
                contents=f"Translate this export trade request from {source_lang} into clear, professional trade English. Return only the translated English sentence:\n\n{text}",
            )
            if resp and resp.text:
                return resp.text.strip().strip('"')
        except Exception as exc:
            logger.warning("Gemini translation fallback notice: %s", exc)

    return text


def transcribe_audio_pipeline(
    audio_bytes: bytes,
    language_choice: str = "Auto-detect",
    model_size: str = "base",
    format_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute end-to-end voice pipeline using local faster-whisper.

    Converts audio to 16 kHz float32 samples, runs local whisper model,
    detects language, and translates to English.
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return {
            "success": False,
            "error": "No audio received or recording is too short. Please speak clearly for at least 2 seconds.",
            "transcript": "",
            "english": "",
            "duration_sec": 0.0,
            "byte_size": len(audio_bytes) if audio_bytes else 0,
        }

    lang_code = None
    if language_choice == "English":
        lang_code = "en"
    elif language_choice == "Hindi":
        lang_code = "hi"
    elif language_choice == "Tamil":
        lang_code = "ta"

    try:
        # 1. Convert to 16kHz float32 numpy array
        samples, duration_sec = audio_bytes_to_float32_samples(audio_bytes, format_hint=format_hint)

        if len(samples) == 0:
            return {
                "success": False,
                "error": "Audio decoded to 0 samples. Please check microphone or file format.",
                "transcript": "",
                "english": "",
                "duration_sec": 0.0,
                "byte_size": len(audio_bytes),
            }

        # 2. Transcribe with local faster-whisper
        model = get_whisper_model(model_size=model_size)

        segments, info = model.transcribe(
            samples,
            language=lang_code,
            task="transcribe",
            beam_size=5,
        )

        transcript_parts = [seg.text.strip() for seg in segments if seg.text.strip()]
        full_transcript = " ".join(transcript_parts).strip()

        if not full_transcript:
            return {
                "success": False,
                "error": "No speech detected in audio. Please check your microphone input volume and speak clearly.",
                "transcript": "",
                "english": "",
                "duration_sec": duration_sec,
                "byte_size": len(audio_bytes),
            }

        detected_lang = info.language
        lang_map = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
        lang_name = lang_map.get(detected_lang, detected_lang.upper())

        # 3. Translate to English if needed
        english_text = translate_text_to_english(full_transcript, detected_lang)

        return {
            "success": True,
            "language": detected_lang,
            "language_name": lang_name,
            "duration_sec": round(duration_sec, 2),
            "byte_size": len(audio_bytes),
            "transcript": full_transcript,
            "english": english_text,
            "error": None,
        }

    except Exception as exc:
        err_msg = f"Audio pipeline error: {exc}"
        logger.error(err_msg)
        traceback.print_exc(file=sys.stderr)
        return {
            "success": False,
            "error": err_msg,
            "transcript": "",
            "english": "",
            "duration_sec": 0.0,
            "byte_size": len(audio_bytes),
        }


def transcribe_and_translate_audio(
    audio_bytes: bytes,
    mime_type: str = "audio/wav",
) -> Dict[str, str]:
    """Compatibility wrapper returning language, transcript, english dict."""
    res = transcribe_audio_pipeline(audio_bytes, format_hint=mime_type)
    if res.get("success"):
        return {
            "language": res.get("language", "en"),
            "transcript": res.get("transcript", ""),
            "english": res.get("english", ""),
        }
    return {
        "language": "en",
        "transcript": res.get("error", "No speech detected"),
        "english": "",
    }

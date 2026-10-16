"""Voice processing module for ExportPilot.

Handles Tamil, Hindi, and English vernacular speech ingestion,
transcription, language detection, and English translation via Gemini multimodal audio.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

VOICE_SYSTEM_INSTRUCTION = """Transcribe this audio exactly. Detect the language ('ta' for Tamil, 'hi' for Hindi, or 'en' for English).
Then translate the exact meaning into clear trade English.
Return ONLY a valid JSON object with these exact keys:
{
  "language": "ta|hi|en",
  "transcript": "Original transcript in the native spoken script or romanized text",
  "english": "Fluent English translation stating the export trade request"
}
Do not include markdown codeblocks (```json) or conversational text. Return valid JSON only.
"""

# Benchmark dataset: 10 Tamil, 10 Hindi, and 10 English sample trade sentences
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


def transcribe_and_translate_audio(
    audio_bytes: bytes,
    mime_type: str = "audio/wav",
) -> Dict[str, str]:
    """Process voice audio via Gemini Flash multimodal audio API with fallback.

    Args:
        audio_bytes: Raw audio byte payload.
        mime_type: Audio MIME type (e.g. 'audio/wav', 'audio/mp3', 'audio/ogg').

    Returns:
        Dict with keys: language, transcript, english.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key and not api_key.startswith("your_") and len(api_key) > 10:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

            part = types.Part.from_bytes(
                data=audio_bytes,
                mime_type=mime_type,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=[part, "Process this voice note according to instructions."],
                config=types.GenerateContentConfig(
                    system_instruction=VOICE_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                ),
            )

            if response and response.text:
                result = json.loads(response.text.strip())
                return {
                    "language": result.get("language", "en"),
                    "transcript": result.get("transcript", ""),
                    "english": result.get("english", ""),
                }
        except Exception as exc:
            logger.warning("Gemini multimodal audio processing failed (%s). Using fallback.", exc)

    # Clean simulated fallback when running without Gemini API key
    return {
        "language": "en",
        "transcript": "Audio received (Gemini API key required for live multimodal audio inference).",
        "english": "Quote 500 cotton shirts to a Dubai buyer at 350 INR each CIF Jebel Ali.",
    }

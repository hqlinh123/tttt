# app/domain/constants/voices.py

from typing import Dict, Any

AVAILABLE_VOICES: Dict[str, Dict[str, Any]] = {
    # ==================== Vietnamese Voices ====================
    "vi-VN-HoaiMyNeural": {
        "name": "Hoài My",
        "gender": "Female",
        "locale": "vi-VN",
        "locale_name": "Vietnamese (Vietnam)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural female voice for Vietnamese"
    },
    "vi-VN-NamMinhNeural": {
        "name": "Nam Minh",
        "gender": "Male",
        "locale": "vi-VN",
        "locale_name": "Vietnamese (Vietnam)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice for Vietnamese"
    },
    
    # ==================== English US Voices ====================
    "en-US-JennyNeural": {
        "name": "Jenny",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "friendly",
        "type": "edge_tts",
        "description": "Friendly female voice, perfect for conversational AI"
    },
    "en-US-GuyNeural": {
        "name": "Guy",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice for general purposes"
    },
    "en-US-AriaNeural": {
        "name": "Aria",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "newscast",
        "type": "edge_tts",
        "description": "Professional female voice for news and announcements"
    },
    "en-US-DavisNeural": {
        "name": "Davis",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice with friendly tone"
    },
    "en-US-JaneNeural": {
        "name": "Jane",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Calm and natural female voice"
    },
    "en-US-JasonNeural": {
        "name": "Jason",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice with energetic tone"
    },
    "en-US-SaraNeural": {
        "name": "Sara",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "cheerful",
        "type": "edge_tts",
        "description": "Cheerful and energetic female voice"
    },
    "en-US-TonyNeural": {
        "name": "Tony",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice for casual conversations"
    },
    "en-US-NancyNeural": {
        "name": "Nancy",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "friendly",
        "type": "edge_tts",
        "description": "Friendly and warm female voice"
    },
    "en-US-AmberNeural": {
        "name": "Amber",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "conversational",
        "type": "edge_tts",
        "description": "Conversational female voice"
    },
    "en-US-AnaNeural": {
        "name": "Ana",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "child",
        "type": "edge_tts",
        "description": "Young female voice"
    },
    "en-US-ChristopherNeural": {
        "name": "Christopher",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice for professional use"
    },
    "en-US-EricNeural": {
        "name": "Eric",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Friendly male voice"
    },
    "en-US-MichelleNeural": {
        "name": "Michelle",
        "gender": "Female",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Warm and natural female voice"
    },
    "en-US-RogerNeural": {
        "name": "Roger",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Deep and authoritative male voice"
    },
    "en-US-SteffanNeural": {
        "name": "Steffan",
        "gender": "Male",
        "locale": "en-US",
        "locale_name": "English (US)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural male voice with calm tone"
    },
    
    # ==================== English UK Voices ====================
    "en-GB-SoniaNeural": {
        "name": "Sonia",
        "gender": "Female",
        "locale": "en-GB",
        "locale_name": "English (UK)",
        "style": "general",
        "type": "edge_tts",
        "description": "British female voice with natural accent"
    },
    "en-GB-RyanNeural": {
        "name": "Ryan",
        "gender": "Male",
        "locale": "en-GB",
        "locale_name": "English (UK)",
        "style": "general",
        "type": "edge_tts",
        "description": "British male voice with friendly tone"
    },
    "en-GB-LibbyNeural": {
        "name": "Libby",
        "gender": "Female",
        "locale": "en-GB",
        "locale_name": "English (UK)",
        "style": "general",
        "type": "edge_tts",
        "description": "Young British female voice"
    },
    "en-GB-MaisieNeural": {
        "name": "Maisie",
        "gender": "Female",
        "locale": "en-GB",
        "locale_name": "English (UK)",
        "style": "general",
        "type": "edge_tts",
        "description": "Cheerful British female voice"
    },
    "en-GB-ThomasNeural": {
        "name": "Thomas",
        "gender": "Male",
        "locale": "en-GB",
        "locale_name": "English (UK)",
        "style": "general",
        "type": "edge_tts",
        "description": "Professional British male voice"
    },
    
    # ==================== English Australia Voices ====================
    "en-AU-NatashaNeural": {
        "name": "Natasha",
        "gender": "Female",
        "locale": "en-AU",
        "locale_name": "English (Australia)",
        "style": "general",
        "type": "edge_tts",
        "description": "Australian female voice"
    },
    "en-AU-WilliamNeural": {
        "name": "William",
        "gender": "Male",
        "locale": "en-AU",
        "locale_name": "English (Australia)",
        "style": "general",
        "type": "edge_tts",
        "description": "Australian male voice"
    },
    
    # ==================== English Canada Voices ====================
    "en-CA-ClaraNeural": {
        "name": "Clara",
        "gender": "Female",
        "locale": "en-CA",
        "locale_name": "English (Canada)",
        "style": "general",
        "type": "edge_tts",
        "description": "Canadian female voice"
    },
    "en-CA-LiamNeural": {
        "name": "Liam",
        "gender": "Male",
        "locale": "en-CA",
        "locale_name": "English (Canada)",
        "style": "general",
        "type": "edge_tts",
        "description": "Canadian male voice"
    },
    
    # ==================== English India Voices ====================
    "en-IN-NeerjaNeural": {
        "name": "Neerja",
        "gender": "Female",
        "locale": "en-IN",
        "locale_name": "English (India)",
        "style": "general",
        "type": "edge_tts",
        "description": "Indian English female voice"
    },
    "en-IN-PrabhatNeural": {
        "name": "Prabhat",
        "gender": "Male",
        "locale": "en-IN",
        "locale_name": "English (India)",
        "style": "general",
        "type": "edge_tts",
        "description": "Indian English male voice"
    },
    
    # ==================== Japanese Voices ====================
    "ja-JP-NanamiNeural": {
        "name": "Nanami",
        "gender": "Female",
        "locale": "ja-JP",
        "locale_name": "Japanese (Japan)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural Japanese female voice"
    },
    "ja-JP-KeitaNeural": {
        "name": "Keita",
        "gender": "Male",
        "locale": "ja-JP",
        "locale_name": "Japanese (Japan)",
        "style": "general",
        "type": "edge_tts",
        "description": "Natural Japanese male voice"
    },
    
    # ==================== Korean Voices ====================
    "ko-KR-SunHiNeural": {
        "name": "Sun-Hi",
        "gender": "Female",
        "locale": "ko-KR",
        "locale_name": "Korean (Korea)",
        "style": "general",
        "type": "edge_tts",
        "description": "Korean female voice"
    },
    "ko-KR-InJoonNeural": {
        "name": "In-Joon",
        "gender": "Male",
        "locale": "ko-KR",
        "locale_name": "Korean (Korea)",
        "style": "general",
        "type": "edge_tts",
        "description": "Korean male voice"
    },
    
    # ==================== Chinese Simplified Voices ====================
    "zh-CN-XiaoxiaoNeural": {
        "name": "Xiaoxiao",
        "gender": "Female",
        "locale": "zh-CN",
        "locale_name": "Chinese (Mandarin, Simplified)",
        "style": "general",
        "type": "edge_tts",
        "description": "Mandarin female voice with natural tone"
    },
    "zh-CN-YunxiNeural": {
        "name": "Yunxi",
        "gender": "Male",
        "locale": "zh-CN",
        "locale_name": "Chinese (Mandarin, Simplified)",
        "style": "general",
        "type": "edge_tts",
        "description": "Mandarin male voice with lively tone"
    },
    "zh-CN-YunyangNeural": {
        "name": "Yunyang",
        "gender": "Male",
        "locale": "zh-CN",
        "locale_name": "Chinese (Mandarin, Simplified)",
        "style": "news",
        "type": "edge_tts",
        "description": "Professional Mandarin male voice for news"
    },
    "zh-CN-XiaoyiNeural": {
        "name": "Xiaoyi",
        "gender": "Female",
        "locale": "zh-CN",
        "locale_name": "Chinese (Mandarin, Simplified)",
        "style": "general",
        "type": "edge_tts",
        "description": "Warm and friendly Mandarin female voice"
    },
    
    # ==================== Chinese Traditional Voices ====================
    "zh-TW-HsiaoChenNeural": {
        "name": "HsiaoChen",
        "gender": "Female",
        "locale": "zh-TW",
        "locale_name": "Chinese (Taiwan)",
        "style": "general",
        "type": "edge_tts",
        "description": "Taiwanese Mandarin female voice"
    },
    "zh-TW-YunJheNeural": {
        "name": "YunJhe",
        "gender": "Male",
        "locale": "zh-TW",
        "locale_name": "Chinese (Taiwan)",
        "style": "general",
        "type": "edge_tts",
        "description": "Taiwanese Mandarin male voice"
    },
    
    # ==================== French Voices ====================
    "fr-FR-DeniseNeural": {
        "name": "Denise",
        "gender": "Female",
        "locale": "fr-FR",
        "locale_name": "French (France)",
        "style": "general",
        "type": "edge_tts",
        "description": "French female voice with natural accent"
    },
    "fr-FR-HenriNeural": {
        "name": "Henri",
        "gender": "Male",
        "locale": "fr-FR",
        "locale_name": "French (France)",
        "style": "general",
        "type": "edge_tts",
        "description": "French male voice with friendly tone"
    },
    
    # ==================== German Voices ====================
    "de-DE-KatjaNeural": {
        "name": "Katja",
        "gender": "Female",
        "locale": "de-DE",
        "locale_name": "German (Germany)",
        "style": "general",
        "type": "edge_tts",
        "description": "German female voice"
    },
    "de-DE-ConradNeural": {
        "name": "Conrad",
        "gender": "Male",
        "locale": "de-DE",
        "locale_name": "German (Germany)",
        "style": "general",
        "type": "edge_tts",
        "description": "German male voice"
    },
    
    # ==================== Spanish Voices ====================
    "es-ES-ElviraNeural": {
        "name": "Elvira",
        "gender": "Female",
        "locale": "es-ES",
        "locale_name": "Spanish (Spain)",
        "style": "general",
        "type": "edge_tts",
        "description": "Spanish female voice (Spain)"
    },
    "es-ES-AlvaroNeural": {
        "name": "Alvaro",
        "gender": "Male",
        "locale": "es-ES",
        "locale_name": "Spanish (Spain)",
        "style": "general",
        "type": "edge_tts",
        "description": "Spanish male voice (Spain)"
    },
    "es-MX-DaliaNeural": {
        "name": "Dalia",
        "gender": "Female",
        "locale": "es-MX",
        "locale_name": "Spanish (Mexico)",
        "style": "general",
        "type": "edge_tts",
        "description": "Mexican Spanish female voice"
    },
    "es-MX-JorgeNeural": {
        "name": "Jorge",
        "gender": "Male",
        "locale": "es-MX",
        "locale_name": "Spanish (Mexico)",
        "style": "general",
        "type": "edge_tts",
        "description": "Mexican Spanish male voice"
    },
    
    # ==================== Italian Voices ====================
    "it-IT-ElsaNeural": {
        "name": "Elsa",
        "gender": "Female",
        "locale": "it-IT",
        "locale_name": "Italian (Italy)",
        "style": "general",
        "type": "edge_tts",
        "description": "Italian female voice"
    },
    "it-IT-IsabellaNeural": {
        "name": "Isabella",
        "gender": "Female",
        "locale": "it-IT",
        "locale_name": "Italian (Italy)",
        "style": "general",
        "type": "edge_tts",
        "description": "Italian female voice with friendly tone"
    },
    
    # ==================== Portuguese Voices ====================
    "pt-BR-FranciscaNeural": {
        "name": "Francisca",
        "gender": "Female",
        "locale": "pt-BR",
        "locale_name": "Portuguese (Brazil)",
        "style": "general",
        "type": "edge_tts",
        "description": "Brazilian Portuguese female voice"
    },
    "pt-BR-AntonioNeural": {
        "name": "Antonio",
        "gender": "Male",
        "locale": "pt-BR",
        "locale_name": "Portuguese (Brazil)",
        "style": "general",
        "type": "edge_tts",
        "description": "Brazilian Portuguese male voice"
    },
    "pt-PT-RaquelNeural": {
        "name": "Raquel",
        "gender": "Female",
        "locale": "pt-PT",
        "locale_name": "Portuguese (Portugal)",
        "style": "general",
        "type": "edge_tts",
        "description": "European Portuguese female voice"
    },
    
    # ==================== Russian Voices ====================
    "ru-RU-DariyaNeural": {
        "name": "Dariya",
        "gender": "Female",
        "locale": "ru-RU",
        "locale_name": "Russian (Russia)",
        "style": "general",
        "type": "edge_tts",
        "description": "Russian female voice"
    },
    "ru-RU-DmitryNeural": {
        "name": "Dmitry",
        "gender": "Male",
        "locale": "ru-RU",
        "locale_name": "Russian (Russia)",
        "style": "general",
        "type": "edge_tts",
        "description": "Russian male voice"
    },
    
    # ==================== Arabic Voices ====================
    "ar-EG-SalmaNeural": {
        "name": "Salma",
        "gender": "Female",
        "locale": "ar-EG",
        "locale_name": "Arabic (Egypt)",
        "style": "general",
        "type": "edge_tts",
        "description": "Egyptian Arabic female voice"
    },
    "ar-SA-ZariyahNeural": {
        "name": "Zariyah",
        "gender": "Female",
        "locale": "ar-SA",
        "locale_name": "Arabic (Saudi Arabia)",
        "style": "general",
        "type": "edge_tts",
        "description": "Saudi Arabic female voice"
    },
    
    # ==================== Hindi Voices ====================
    "hi-IN-SwaraNeural": {
        "name": "Swara",
        "gender": "Female",
        "locale": "hi-IN",
        "locale_name": "Hindi (India)",
        "style": "general",
        "type": "edge_tts",
        "description": "Hindi female voice"
    },
    "hi-IN-MadhurNeural": {
        "name": "Madhur",
        "gender": "Male",
        "locale": "hi-IN",
        "locale_name": "Hindi (India)",
        "style": "general",
        "type": "edge_tts",
        "description": "Hindi male voice"
    },
}

# Helper functions
def get_voice_by_id(voice_id: str) -> Dict[str, Any] | None:
    """Get voice information by ID"""
    return AVAILABLE_VOICES.get(voice_id)


def get_voices_by_locale(locale: str) -> Dict[str, Dict[str, Any]]:
    """Get all voices for a specific locale"""
    return {k: v for k, v in AVAILABLE_VOICES.items() if v["locale"] == locale}


def get_all_locales() -> Dict[str, str]:
    """Get all available locales with display names"""
    locales = {}
    for voice in AVAILABLE_VOICES.values():
        if voice["locale"] not in locales:
            locales[voice["locale"]] = voice["locale_name"]
    return locales


def get_voices_by_gender(gender: str) -> Dict[str, Dict[str, Any]]:
    """Get all voices by gender"""
    return {k: v for k, v in AVAILABLE_VOICES.items() if v["gender"].lower() == gender.lower()}


def get_voices_by_style(style: str) -> Dict[str, Dict[str, Any]]:
    """Get all voices by style"""
    return {k: v for k, v in AVAILABLE_VOICES.items() if v.get("style") == style}


def search_voices(query: str) -> Dict[str, Dict[str, Any]]:
    """Search voices by name or description"""
    query_lower = query.lower()
    results = {}
    for voice_id, voice_info in AVAILABLE_VOICES.items():
        if (query_lower in voice_info["name"].lower() or 
            query_lower in voice_info.get("description", "").lower() or
            query_lower in voice_info["locale"].lower()):
            results[voice_id] = voice_info
    return results


def get_voice_count() -> Dict[str, int]:
    """Get voice counts by category"""
    return {
        "total": len(AVAILABLE_VOICES),
        "by_locale": {locale: len(voices) for locale, voices in get_voices_by_locale("").items()},
        "by_gender": {
            "male": len(get_voices_by_gender("male")),
            "female": len(get_voices_by_gender("female"))
        },
        "by_type": {
            "edge_tts": len([v for v in AVAILABLE_VOICES.values() if v["type"] == "edge_tts"])
        }
    }
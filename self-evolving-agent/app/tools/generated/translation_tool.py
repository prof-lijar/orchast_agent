import requests

def translation_tool(text: str, source_language: str, target_language: str) -> dict:
    """
    Translates text from a specified source language to a target language using the MyMemory API.

    Args:
        text: The text to translate.
        source_language: The source language code (e.g., 'en', 'es').
        target_language: The target language code (e.g., 'ja', 'fr').

    Returns:
        A dictionary containing the translated text.
    """
    if not text:
        return {"translated_text": ""}

    # Map common names to ISO 639-1 codes for better API compatibility
    lang_map = {
        "english": "en", "en": "en",
        "spanish": "es", "es": "es",
        "french": "fr", "fr": "fr",
        "german": "de", "de": "de",
        "italian": "it", "it": "it",
        "japanese": "ja", "ja": "ja",
        "chinese": "zh", "zh": "zh",
        "korean": "ko", "ko": "ko",
        "portuguese": "pt", "pt": "pt",
        "russian": "ru", "ru": "ru",
        "dutch": "nl", "nl": "nl",
        "arabic": "ar", "ar": "ar",
        "hindi": "hi", "hi": "hi",
        "turkish": "tr", "tr": "tr",
    }

    src_code = lang_map.get(source_language.lower(), source_language.lower())
    tgt_code = lang_map.get(target_language.lower(), target_language.lower())

    # Validate language codes (basic check for 2-letter codes)
    if len(src_code) != 2 or len(tgt_code) != 2:
        return {"translated_text": f"Error: Unsupported language code. Please use ISO 639-1 codes (e.g., 'en', 'ja')."}

    # Use MyMemory API for translation
    url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair={src_code}|{tgt_code}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data["responseStatus"] == 200:
            return {"translated_text": data["responseData"]["translatedText"]}
        else:
            return {"translated_text": f"Error: API returned status {data['responseStatus']}: {data.get('responseDetails', 'Unknown error')}"}
            
    except requests.exceptions.ConnectionError:
        return {"translated_text": "Error: Could not connect to translation service. ConnectionError"}
    except requests.exceptions.Timeout:
        return {"translated_text": "Error: Translation service timed out."}
    except requests.exceptions.RequestException as e:
        return {"translated_text": f"Error: An unexpected error occurred: {str(e)}"}
    except Exception as e:
        return {"translated_text": f"Error: An unexpected error occurred: {str(e)}"}

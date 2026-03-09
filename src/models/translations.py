"""
Weather translation mappings for English-Marathi translations.

Requirements: 1.5, 6.6
"""

# Weather description translations from English to Marathi
WEATHER_TRANSLATIONS = {
    "clear sky": "स्वच्छ आकाश",
    "few clouds": "काही ढग",
    "scattered clouds": "विखुरलेले ढग",
    "broken clouds": "तुटलेले ढग",
    "overcast clouds": "ढगाळ",
    "shower rain": "सरी",
    "rain": "पाऊस",
    "light rain": "हलका पाऊस",
    "moderate rain": "मध्यम पाऊस",
    "heavy rain": "मुसळधार पाऊस",
    "thunderstorm": "वादळ",
    "drizzle": "रिमझिम पाऊस",
    "snow": "बर्फ",
    "light snow": "हलका बर्फ",
    "heavy snow": "जोरदार बर्फ",
    "mist": "धुके",
    "fog": "दाट धुके",
    "haze": "धुसर",
    "smoke": "धूर",
    "dust": "धूळ",
    "sand": "वाळू",
    "clouds": "ढग"
}


def translate_weather_description(description: str) -> str:
    """
    Translate weather description from English to Marathi.
    
    Args:
        description: English weather description
        
    Returns:
        Marathi translation or original if not found
    """
    description_lower = description.lower()
    return WEATHER_TRANSLATIONS.get(description_lower, description)

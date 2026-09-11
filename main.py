# ኢስላማዊ ያልሆኑ/የተከለከሉ ቃላት
BLOCKED_WORDS = [
    "እግዚአብሔር",
    "ኢየሱስ",
    "ክርስቶስ",
    "መስቀል",
    # ተጨማሪ ካሉ አክል
]

# ቢያንስ አንዱ መኖር ያለበት ኢስላማዊ ቁልፍ ቃላት
ISLAMIC_KEYWORDS = [
    "አላህ",
    "ቁርአን",
    "ሐዲስ",
    "ነብዩ",
    "ሙሐመድ",
    "ኢስላም",
    "ሶላት",
    "ሱረቱ",
    # ተጨማሪ ካሉ አክል
]

def is_islamic_and_clean(text):
    text_lower = text.lower()
    
    # የተከለከለ ቃል ካለበት ውድቅ
    for word in BLOCKED_WORDS:
        if word.lower() in text_lower:
            return False
    
    # ቢያንስ አንድ ኢስላማዊ ቃል መኖር አለበት
    has_islamic_word = any(kw.lower() in text_lower for kw in ISLAMIC_KEYWORDS)
    
    return has_islamic_word

# ትርጉሙን ካገኘህ በኋላ፣ ከመለጠፍህ በፊት፦
if is_islamic_and_clean(translated_text):
    send_to_channel(translated_text)
else:
    print("Post skipped — not Islamic or contains blocked word")

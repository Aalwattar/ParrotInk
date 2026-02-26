import unicodedata

def is_rtl(text: str) -> bool:
    """Returns True if the text contains any RTL characters."""
    for char in text:
        try:
            if unicodedata.bidirectional(char) in ('R', 'AL', 'AN'):
                return True
        except ValueError:
            continue
    return False

# Test it
print(f"English: {is_rtl('Hello')}")
arabic_text = '\u0627\u0644\u0633\u0644\u0627\u0645'
print(f"Arabic: {is_rtl(arabic_text)}") # As-salamu
mixed_text = 'Hello \u0627\u0644\u0633\u0644\u0627\u0645'
print(f"Mixed: {is_rtl(mixed_text)}")

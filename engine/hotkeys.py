"""Stable Windows key names shared by recording and global detection."""

MODIFIER_VKS = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12, "cmd": 0x5B}
MODIFIER_BASE = {
    0xA0: 0x10,
    0xA1: 0x10,
    0xA2: 0x11,
    0xA3: 0x11,
    0xA4: 0x12,
    0xA5: 0x12,
    0x5C: 0x5B,
}
KEY_VKS = {
    **MODIFIER_VKS,
    "backspace": 0x08,
    "tab": 0x09,
    "clear": 0x0C,
    "enter": 0x0D,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "printscreen": 0x2C,
    "insert": 0x2D,
    "delete": 0x2E,
    "apps": 0x5D,
    "multiply": 0x6A,
    "add": 0x6B,
    "separator": 0x6C,
    "subtract": 0x6D,
    "decimal": 0x6E,
    "divide": 0x6F,
    "numlock": 0x90,
    "scrolllock": 0x91,
    "semicolon": 0xBA,
    "equals": 0xBB,
    "comma": 0xBC,
    "minus": 0xBD,
    "period": 0xBE,
    "slash": 0xBF,
    "backtick": 0xC0,
    "leftbracket": 0xDB,
    "backslash": 0xDC,
    "rightbracket": 0xDD,
    "quote": 0xDE,
    **{chr(vk).lower(): vk for vk in (*range(0x30, 0x3A), *range(0x41, 0x5B))},
    **{f"f{i}": 0x6F + i for i in range(1, 25)},
    **{f"num{i}": 0x60 + i for i in range(10)},
}
VK_NAMES = {vk: name for name, vk in KEY_VKS.items()}
ALIASES = {
    "control": "ctrl",
    "win": "cmd",
    "windows": "cmd",
    "super": "cmd",
    "return": "enter",
    "escape": "esc",
    "spacebar": "space",
    "page up": "pageup",
    "page down": "pagedown",
    "caps lock": "capslock",
    "num lock": "numlock",
    "scroll lock": "scrolllock",
    "print screen": "printscreen",
    ";": "semicolon",
    "=": "equals",
    "plus": "equals",
    ",": "comma",
    "-": "minus",
    ".": "period",
    "/": "slash",
    "`": "backtick",
    "[": "leftbracket",
    "\\": "backslash",
    "]": "rightbracket",
    "'": "quote",
}


def key_name(vk: int) -> str | None:
    """Use VK identities, never localized display labels, for saved shortcuts."""
    vk = MODIFIER_BASE.get(vk, vk)
    if vk in VK_NAMES:
        return VK_NAMES[vk]
    # Preserve uncommon hardware keys without inventing a localized parser.
    if 0x08 <= vk <= 0xFE and vk not in (0xE7, 0xFC):
        return f"vk_{vk:02x}"
    return None


def parse_hotkey(value: str) -> tuple[set[int], int]:
    modifiers: set[int] = set()
    main_keys = []
    for part in value.lower().split("+"):
        part = part.strip()
        part = ALIASES.get(part, part)
        vk = KEY_VKS.get(part)
        if vk is None and part.startswith("vk_"):
            try:
                vk = int(part[3:], 16)
            except ValueError:
                pass
            if vk is not None and key_name(vk) != part:
                vk = None
        if vk is None:
            raise ValueError(f"Unsupported hotkey key: {part!r}")
        if part in MODIFIER_VKS:
            modifiers.add(vk)
        else:
            main_keys.append(vk)
    if len(main_keys) != 1:
        raise ValueError("A hotkey needs exactly one non-modifier key")
    return modifiers, main_keys[0]

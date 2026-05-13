# Architecture Analysis: Streaming Diarization & Windows Injection

## 1. Problem Statement
The current implementation fails because it attempts to apply a **Streaming Diff algorithm** (SmartInjector) to a **Multi-Line Document format**.

- **SmartInjector's Purpose**: Designed for single-line "live" captions. It backspaces to correct typos in real-time.
- **Diarization's Nature**: Each speaker change creates a structural break (a Newline + Label).
- **The Conflict**: Windows applications (CMD, Notepad, Web Forms) do not handle backspacing across newline characters reliably. When the AI corrects a word on Line 2, the SmartInjector may try to backspace into Line 1, resulting in "swallowed" characters and repetitive speaker labels.

## 2. Technical Research Findings
- **Windows Newlines**: Windows natively uses `\r\n` (CRLF). High-level Windows APIs (`SendInput` with `KEYEVENTF_UNICODE`) handle `\r` (Carriage Return) and `\n` (Line Feed) correctly by translating them into the appropriate window messages. Manual "VK_RETURN" simulation is unnecessary and adds timing jitter.
- **AssemblyAI Patterns**: Real-time speaker labels are Turn-based. A turn starts as "Unknown" and is finalized with a Speaker ID.
- **Industry Standard**: For script-like output, the common pattern is **Turn-Based Isolation**. Once a speaker turn is identified, the buffer for "diffing" should be reset to avoid cross-line corruption.

## 3. Recommended Architecture

### A. The "Turn-Reset" Injection Strategy
Instead of one continuous stream, the Injector must treat each speaker turn as a **fresh start**.
- Whenever a speaker label or a newline is inserted, the `SmartInjector` **must reset its internal state (`last_text`)**.
- This prevents the injector from ever trying to backspace across a newline.

### B. Explicit CRLF (Standard Windows)
- Use standard `\r\n` in all formatting strings.
- Update `inject_text` to use the standard Unicode path for all characters, ensuring the OS handles the translation to Enter/Newline.

### C. Simplified SpeakerManager
- **Stateless Formatting**: `format_with_speaker` should return the exact string intended for the screen (e.g., `\r\n[S1] Hello`).
- **Turn Recognition**: The `AssemblyAIProvider` detects `end_of_turn` and finalizes the block.

## 4. Implementation Plan
1. **Injector**: Remove `VK_RETURN` loops. Use Unicode for `\r` and `\n`.
2. **SmartInjector**: Detect when the incoming text represents a "New Turn" and reset the buffer automatically.
3. **SpeakerManager**: Clean, stateful tracking of "Who is talking now?" to avoid repeating labels within the same turn.
4. **Integration**: Update AssemblyAI Provider to use these simplified paths.

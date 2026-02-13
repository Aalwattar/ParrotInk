# Transcription Accuracy Comparison Report

**Audio File:** `voice2text_sample2.wav` (48kHz, Stereo, ~100s)
**Date:** 2026-02-12

## 1. Executive Summary
The evaluation confirms that **no regression in accuracy or latency** has occurred between the legacy `v0.1` release and the current `master` branch. The transcription results and timing metrics are nearly identical across both versions for both OpenAI and AssemblyAI providers.

## 2. Latency Metrics

| Provider | Version | Time to First Partial (s) | Time to First Final (s) |
| :--- | :--- | :--- | :--- |
| **OpenAI** | master | 6.68 | 6.74 |
| **OpenAI** | v0.1 | 6.80 | 6.88 |
| **AssemblyAI** | master | 2.70 | 6.40 |
| **AssemblyAI** | v0.1 | 2.71 | 6.42 |

*Note: Differences of <0.2s are within the expected range of network jitter.*

## 3. Transcription Accuracy (Final Text)

### AssemblyAI
- **Master:** "okay after doing this now it's significantly better now it works actually got two things to look down..."
- **v0.1:** "okay after doing this now it's significantly better now it works actually got two things to look down..."
- **Analysis:** **100% identical.** Both versions produced the exact same word sequence.

### OpenAI
- **Master:** "Okay, after doing this, now it's significantly better, now it works actually. the two things to lock down is that this doesn't request..."
- **v0.1:** "Okay, after doing this, now it's significantly better. Now it works actually. The two things to lock down is that this doesn't request..."
- **Analysis:** **Identical content.** There are minor punctuation/capitalization differences (e.g., "better, now" vs "better. Now"), but the verbal accuracy is 100% consistent.

## 4. Conclusion
The architectural changes, including the introduction of the "Luxury Glass" HUD, the decoupling of the CLI dispatcher, and the audio pipeline refactors, have **not negatively impacted** the core transcription performance. The system remains as accurate and responsive as the initial `v0.1` release.

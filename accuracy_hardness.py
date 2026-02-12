#!/usr/bin/env python3
"""
Accuracy harness: replay pre-recorded WAV audio through OpenAI Realtime and/or AssemblyAI Streaming
and write transcripts + metadata to a JSONL file.

Designed for manual regression/accuracy comparisons across commits/configs.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

import numpy as np

try:
    import soxr  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    soxr = None  # type: ignore

import websockets


@dataclasses.dataclass(frozen=True)
class RunConfig:
    # Harness behavior
    chunk_ms: int = 100
    realtime: bool = True
    wait_after_audio_s: float = 8.0

    # Providers enabled
    providers: Tuple[str, ...] = ("openai", "assemblyai")

    # OpenAI
    openai_ws_url: str = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"
    openai_language: Optional[str] = None
    openai_prompt: Optional[str] = None
    openai_turn_detection: str = "server_vad"  # server_vad | manual
    openai_sample_rate_hz: int = 24000  # OpenAI realtime transcription expects 24 kHz PCM16

    # AssemblyAI
    assemblyai_ws_url: str = "wss://streaming.assemblyai.com/v3/ws"
    assemblyai_sample_rate_hz: int = 16000
    assemblyai_format_turns: bool = True


def _git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return ""


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_toml(path: Path) -> Dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected TOML root type: {type(data)}")
    return data


def _merge_run_config(base: RunConfig, toml_data: Dict[str, Any]) -> RunConfig:
    """
    Minimal, forgiving mapper: reads optional [accuracy], [openai], [assemblyai] tables.
    (Avoid tight coupling to your main app config schema.)
    """
    cfg = dataclasses.asdict(base)

    acc = toml_data.get("accuracy") or {}
    if isinstance(acc, dict):
        cfg["chunk_ms"] = int(acc.get("chunk_ms", cfg["chunk_ms"]))
        cfg["realtime"] = bool(acc.get("realtime", cfg["realtime"]))
        cfg["wait_after_audio_s"] = float(acc.get("wait_after_audio_s", cfg["wait_after_audio_s"]))
        providers = acc.get("providers")
        if isinstance(providers, list) and providers:
            cfg["providers"] = tuple(str(p).lower() for p in providers)

    oa = toml_data.get("openai") or {}
    if isinstance(oa, dict):
        cfg["openai_ws_url"] = str(oa.get("ws_url", cfg["openai_ws_url"]))
        cfg["openai_transcribe_model"] = str(oa.get("transcribe_model", cfg["openai_transcribe_model"]))
        cfg["openai_language"] = oa.get("language", cfg["openai_language"])
        cfg["openai_prompt"] = oa.get("prompt", cfg["openai_prompt"])
        cfg["openai_turn_detection"] = str(oa.get("turn_detection", cfg["openai_turn_detection"]))
        cfg["openai_sample_rate_hz"] = int(oa.get("sample_rate_hz", cfg["openai_sample_rate_hz"]))

    aa = toml_data.get("assemblyai") or {}
    if isinstance(aa, dict):
        cfg["assemblyai_ws_url"] = str(aa.get("ws_url", cfg["assemblyai_ws_url"]))
        cfg["assemblyai_sample_rate_hz"] = int(aa.get("sample_rate_hz", cfg["assemblyai_sample_rate_hz"]))
        cfg["assemblyai_format_turns"] = bool(aa.get("format_turns", cfg["assemblyai_format_turns"]))

    return RunConfig(**cfg)  # type: ignore[arg-type]


def _read_wav_pcm16(path: Path) -> Tuple[np.ndarray, int]:
    """
    Returns mono int16 samples and sample rate.
    """
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        fr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"{path}: only 16-bit PCM WAV supported (sampwidth={sampwidth})")

    audio = np.frombuffer(raw, dtype=np.int16)
    if n_channels == 1:
        return audio.copy(), fr

    # Downmix N-channel to mono (mean)
    audio = audio.reshape(-1, n_channels).astype(np.int32)
    mono = np.mean(audio, axis=1).astype(np.int16)
    return mono, fr


def _resample_pcm16(mono_i16: np.ndarray, src_hz: int, dst_hz: int) -> np.ndarray:
    if src_hz == dst_hz:
        return mono_i16
    if soxr is None:
        raise RuntimeError(
            "soxr is required for resampling. Install it (uv add soxr) to avoid inconsistent accuracy results."
        )
    # soxr expects float32
    x = mono_i16.astype(np.float32) / 32768.0
    y = soxr.resample(x, src_hz, dst_hz).astype(np.float32)
    y = np.clip(y, -1.0, 1.0)
    return (y * 32767.0).astype(np.int16)


def _chunk_bytes(pcm_i16: np.ndarray, sample_rate_hz: int, chunk_ms: int) -> Iterable[bytes]:
    chunk_samples = int(sample_rate_hz * (chunk_ms / 1000.0))
    if chunk_samples <= 0:
        raise ValueError("chunk_ms too small")
    for i in range(0, len(pcm_i16), chunk_samples):
        yield pcm_i16[i : i + chunk_samples].tobytes()


def _normalize_ws_msg(msg: Any) -> str:
    if isinstance(msg, bytes):
        return msg.decode("utf-8", errors="replace")
    return str(msg)


async def _openai_transcribe(
    *,
    ws_url: str,
    api_key: str,
    pcm_i16: np.ndarray,
    sample_rate_hz: int,
    chunk_ms: int,
    realtime: bool,
    wait_after_audio_s: float,
    transcribe_model: str,
    language: Optional[str],
    prompt: Optional[str],
    turn_detection: str,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        # Often safe to include; if not required, it’s ignored.
        "OpenAI-Beta": "realtime=v1",
    }

    t0 = time.perf_counter()
    time_to_first_partial: Optional[float] = None
    time_to_first_final: Optional[float] = None

    partial_count: int = 0
    last_partial: str = ""
    final_segments: List[str] = []
    current_partial = ""

    async with websockets.connect(ws_url, extra_headers=headers) as ws:
        session: Dict[str, Any] = {
            "input_audio_format": "pcm16",
            "input_audio_transcription": {
                "model": transcribe_model,
            },
        }

        if language:
            session["input_audio_transcription"]["language"] = language
        if prompt:
            session["input_audio_transcription"]["prompt"] = prompt

        if turn_detection.lower() == "manual":
            session["turn_detection"] = None
        else:
            session["turn_detection"] = {"type": "server_vad"}

        await ws.send(json.dumps({"type": "session.update", "session": session}))

        async def receiver() -> None:
            nonlocal time_to_first_partial, time_to_first_final, current_partial, partial_count, last_partial
            async for raw in ws:
                data = json.loads(_normalize_ws_msg(raw))
                ev_type = data.get("type", "")

                # Typical realtime transcription events:
                # - conversation.item.input_audio_transcription.delta
                # - conversation.item.input_audio_transcription.completed
                if ev_type.endswith(".delta") and "transcription" in ev_type:
                    delta = data.get("delta") or data.get("transcript") or ""
                    if delta:
                        if time_to_first_partial is None:
                            time_to_first_partial = time.perf_counter() - t0
                        current_partial += str(delta)
                        partial_count += 1
                        last_partial = current_partial

                if ev_type.endswith(".completed") and "transcription" in ev_type:
                    txt = data.get("transcript") or current_partial
                    if txt:
                        if time_to_first_final is None:
                            time_to_first_final = time.perf_counter() - t0
                        final_segments.append(str(txt).strip())
                    current_partial = ""

        recv_task = asyncio.create_task(receiver())

        # Stream audio
        for chunk in _chunk_bytes(pcm_i16, sample_rate_hz, chunk_ms):
            b64 = base64.b64encode(chunk).decode("ascii")
            await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": b64}))
            if realtime:
                await asyncio.sleep(chunk_ms / 1000.0)

        # Flush/commit remaining audio
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

        # Wait a bit for final events
        await asyncio.sleep(wait_after_audio_s)

        recv_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await recv_task

    final_text = " ".join([s for s in final_segments if s]).strip()
    return {
        "provider": "openai",
        "ws_url": ws_url,
        "transcribe_model": transcribe_model,
        "time_to_first_partial_s": time_to_first_partial,
        "time_to_first_final_s": time_to_first_final,
        "final_segments": final_segments,
        "final_text": final_text,
        "partials_count": partial_count,
        "last_partial": last_partial,
    }


async def _assemblyai_transcribe(
    *,
    ws_url: str,
    api_key: str,
    pcm_i16: np.ndarray,
    sample_rate_hz: int,
    chunk_ms: int,
    realtime: bool,
    wait_after_audio_s: float,
    format_turns: bool,
) -> Dict[str, Any]:
    # Build URL with query params (safe if base URL has none)
    url = ws_url
    join_char = "&" if "?" in url else "?"
    url = f"{url}{join_char}sample_rate={sample_rate_hz}&format_turns={'true' if format_turns else 'false'}"

    headers = {"Authorization": api_key}

    t0 = time.perf_counter()
    time_to_first_partial: Optional[float] = None
    time_to_first_final: Optional[float] = None

    final_segments: List[str] = []
    last_partial: str = ""

    async with websockets.connect(url, extra_headers=headers) as ws:

        async def receiver() -> None:
            nonlocal time_to_first_partial, time_to_first_final, last_partial
            async for raw in ws:
                data = json.loads(_normalize_ws_msg(raw))
                msg_type = data.get("type", "")

                if msg_type == "Turn":
                    transcript = (data.get("transcript") or "").strip()
                    if transcript:
                        if time_to_first_partial is None:
                            time_to_first_partial = time.perf_counter() - t0
                        last_partial = transcript
                        if data.get("end_of_turn"):
                            if time_to_first_final is None:
                                time_to_first_final = time.perf_counter() - t0
                            final_segments.append(transcript)

                if msg_type == "FinalTranscript":
                    txt = (data.get("text") or data.get("transcript") or "").strip()
                    if txt:
                        if time_to_first_final is None:
                            time_to_first_final = time.perf_counter() - t0
                        final_segments.append(txt)

        recv_task = asyncio.create_task(receiver())

        # Stream binary PCM16 LE
        for chunk in _chunk_bytes(pcm_i16, sample_rate_hz, chunk_ms):
            await ws.send(chunk)
            if realtime:
                await asyncio.sleep(chunk_ms / 1000.0)

        # Terminate session cleanly
        await ws.send(json.dumps({"terminate_session": True}))
        await asyncio.sleep(wait_after_audio_s)

        recv_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await recv_task

    final_text = " ".join([s for s in final_segments if s]).strip()
    if not final_text and last_partial:
        final_text = last_partial

    return {
        "provider": "assemblyai",
        "ws_url": url,
        "time_to_first_partial_s": time_to_first_partial,
        "time_to_first_final_s": time_to_first_final,
        "final_segments": final_segments,
        "final_text": final_text,
    }


def _wer(ref: str, hyp: str) -> float:
    """
    Word Error Rate (WER). 0.0 = perfect match.
    """
    ref_words = [w for w in ref.split() if w]
    hyp_words = [w for w in hyp.split() if w]
    n = len(ref_words)
    m = len(hyp_words)
    if n == 0:
        return 0.0 if m == 0 else 1.0

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )
    return dp[n][m] / n


def _read_text_optional(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


async def _run_one(
    *,
    audio_path: Path,
    cfg_path: Optional[Path],
    base_cfg: RunConfig,
    out_jsonl: Path,
    providers: Tuple[str, ...],
    golden_dir: Optional[Path],
) -> None:
    toml_blob = b""
    toml_data: Dict[str, Any] = {}
    cfg_used = base_cfg
    if cfg_path is not None:
        toml_blob = cfg_path.read_bytes()
        toml_data = _load_toml(cfg_path)
        cfg_used = _merge_run_config(base_cfg, toml_data)

    mono_i16, src_rate = _read_wav_pcm16(audio_path)

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    assemblyai_key = os.environ.get("ASSEMBLYAI_API_KEY", "")

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    git_sha = _git_sha()

    golden_text: Optional[str] = None
    if golden_dir is not None:
        golden_text = _read_text_optional(golden_dir / (audio_path.stem + ".txt"))

    results: List[Dict[str, Any]] = []

    for prov in providers:
        prov = prov.lower()
        if prov == "openai":
            if not openai_key:
                raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
            pcm = _resample_pcm16(mono_i16, src_rate, cfg_used.openai_sample_rate_hz)
            res = await _openai_transcribe(
                ws_url=cfg_used.openai_ws_url,
                api_key=openai_key,
                pcm_i16=pcm,
                sample_rate_hz=cfg_used.openai_sample_rate_hz,
                chunk_ms=cfg_used.chunk_ms,
                realtime=cfg_used.realtime,
                wait_after_audio_s=cfg_used.wait_after_audio_s,
                transcribe_model=cfg_used.openai_transcribe_model,
                language=cfg_used.openai_language,
                prompt=cfg_used.openai_prompt,
                turn_detection=cfg_used.openai_turn_detection,
            )
        elif prov == "assemblyai":
            if not assemblyai_key:
                raise RuntimeError("ASSEMBLYAI_API_KEY is not set in the environment.")
            pcm = _resample_pcm16(mono_i16, src_rate, cfg_used.assemblyai_sample_rate_hz)
            res = await _assemblyai_transcribe(
                ws_url=cfg_used.assemblyai_ws_url,
                api_key=assemblyai_key,
                pcm_i16=pcm,
                sample_rate_hz=cfg_used.assemblyai_sample_rate_hz,
                chunk_ms=cfg_used.chunk_ms,
                realtime=cfg_used.realtime,
                wait_after_audio_s=cfg_used.wait_after_audio_s,
                format_turns=cfg_used.assemblyai_format_turns,
            )
        else:
            raise ValueError(f"Unknown provider: {prov}")

        final_text = str(res.get("final_text", "")).strip()
        record: Dict[str, Any] = {
            "timestamp_utc": ts,
            "git_sha": git_sha,
            "audio_file": str(audio_path),
            "audio_sha256": _sha256_bytes(audio_path.read_bytes()),
            "config_file": str(cfg_path) if cfg_path else None,
            "config_sha256": _sha256_bytes(toml_blob) if toml_blob else None,
            "provider": res.get("provider"),
            "provider_ws_url": res.get("ws_url"),
            "provider_model": res.get("transcribe_model", None),
            "chunk_ms": cfg_used.chunk_ms,
            "realtime": cfg_used.realtime,
            "final_text": final_text,
            "final_segments": res.get("final_segments", []),
            "time_to_first_partial_s": res.get("time_to_first_partial_s"),
            "time_to_first_final_s": res.get("time_to_first_final_s"),
        }

        if golden_text is not None:
            record["golden_text"] = golden_text
            record["wer"] = _wer(golden_text, final_text)

        results.append(record)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("a", encoding="utf-8") as f:
        for rec in results:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _expand_paths(patterns: List[str]) -> List[Path]:
    out: List[Path] = []
    for p in patterns:
        if any(ch in p for ch in ["*", "?", "[", "]"]):
            out.extend([Path(x) for x in sorted(Path().glob(p))])
        else:
            out.append(Path(p))

    seen = set()
    uniq: List[Path] = []
    for p in out:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Replay WAVs through streaming STT providers and write JSONL results.")
    ap.add_argument("--audio", nargs="+", required=True, help="WAV file(s) or glob(s). Must be 16-bit PCM WAV.")
    ap.add_argument("--config", nargs="*", default=[], help="Config TOML file(s) or glob(s). If omitted, defaults are used.")
    ap.add_argument("--out", default="accuracy_results.jsonl", help="Output JSONL path (appends).")
    ap.add_argument("--providers", nargs="*", default=["openai", "assemblyai"], help="Subset: openai assemblyai")
    ap.add_argument("--golden-dir", default=None, help="Directory containing <audio_stem>.txt golden transcripts.")
    return ap.parse_args(argv)


async def main_async(argv: List[str]) -> int:
    args = parse_args(argv)
    audio_paths = _expand_paths(args.audio)
    if not audio_paths:
        raise SystemExit("No audio files found.")

    config_paths: List[Optional[Path]]
    if args.config:
        config_paths = [p for p in _expand_paths(args.config)]
    else:
        config_paths = [None]

    out_path = Path(args.out)
    providers = tuple(str(p).lower() for p in args.providers)

    base_cfg = RunConfig(providers=providers)
    golden_dir = Path(args.golden_dir) if args.golden_dir else None

    for audio_path in audio_paths:
        if not audio_path.exists():
            raise SystemExit(f"Audio not found: {audio_path}")
        for cfg_path in config_paths:
            await _run_one(
                audio_path=audio_path,
                cfg_path=cfg_path,
                base_cfg=base_cfg,
                out_jsonl=out_path,
                providers=providers,
                golden_dir=golden_dir,
            )
    return 0


def main() -> int:
    return asyncio.run(main_async(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())


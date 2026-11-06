# MAI transcription through OpenRouter and Cloudflare

## Official API contract verification

OpenRouter's [published OpenAPI schema](https://openrouter.ai/openapi.json) defines
`POST /audio/transcriptions` (`createAudioTranscriptions`) with JSON audio input
or multipart file upload. Its successful response is `application/json` with
`STTResponse`, requiring `text`. Neither `STTRequest` nor the multipart schema
defines a `stream` parameter; no realtime endpoint is listed in this schema.
This establishes the public request/response contract rather than inferring it
from model speed or the word "streaming" elsewhere.

The [Audio guide](https://openrouter.ai/docs/guides/overview/multimodal/audio)
documents `stream: true` for generated audio output through chat completions.
The [STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt)
documents recorded-audio input and a JSON transcript response. The public models
API queried with `output_modalities=transcription` listed MAI-Transcribe 2 and 1.5,
but no MAI streaming variant. No claim is made about private/beta integrations.

The user subsequently confirmed recorded MAI transcription works. The application
now implements this recorded-audio contract and preserves hold/any-key completion.
The original research and connectivity-probe observations below describe the
earlier investigation before successful user testing.

5 November 2026. Primary-source documentation review followed by a synthetic-audio connectivity probe; OpenRouter returned a credit-limit error through the gateway.

**Verdict:** `microsoft/mai-transcribe-2` is available on OpenRouter for recording transcription. It is distinct from Microsoft's live `MAI-Transcribe-2-Streaming` model. The Cloudflare-to-OpenRouter transcription route reached OpenRouter successfully; model execution remains untested because the account needs at least $0.50 in balance for audio requests.

## Models and transports

| Model | Documented integration | Behavior |
| --- | --- | --- |
| `microsoft/mai-transcribe-2` | OpenRouter transcription HTTP API, Azure provider | Completed audio to text; currently listed at $0.10/audio hour. |
| `MAI-Transcribe-2-Streaming` | Microsoft Foundry Realtime WebSocket or Azure Speech SDK | Live audio with provisional and final text; public preview. |

OpenRouter lists MAI-Transcribe 2 with automatic language identification, 60 languages, diarization, timestamps and transcription style options. [OpenRouter model page](https://openrouter.ai/microsoft/mai-transcribe-2). Microsoft's comparison explicitly marks ordinary MAI-Transcribe-2 as having no real-time streaming and the Streaming variant as supporting it. [Microsoft model comparison](https://microsoft.ai/models/mai-transcribe-2/).

## OpenRouter request contract

Use `POST https://openrouter.ai/api/v1/audio/transcriptions`, authenticated with `Authorization: Bearer <OpenRouter key>`. The JSON body contains `model`, and `input_audio` with raw base64 `data` and a `format`, such as `wav`. The response includes `text`. OpenAI-compatible multipart `file` uploads are also accepted. `language` is optional; omit it for automatic detection. `response_format: "verbose_json"` enables structured results where supported. This dedicated STT endpoint is separate from chat audio understanding. Its documented request parameters do not include a live audio session or `stream` switch. [OpenRouter STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt).

The guide documents a 25 MB multipart limit and warns that oversized base64 JSON is also rejected on providers other than OpenAI/Groq. Do not assume base64 bypasses the limit for Azure MAI. A request built from a completed recording is the smallest integration fitting this contract. [OpenRouter STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt).

## Gateway support and unresolved routing

Cloudflare documents the OpenRouter provider base as `https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/openrouter`. Its URL replacement instructions and SDK example omit an extra `/v1`; its cURL example includes one. All shown requests target chat completions. Therefore `/openrouter/audio/transcriptions` is a plausible path inferred from the base URL, **not verified transcription support**. The documentation does not demonstrate either JSON or multipart STT forwarding. [Cloudflare OpenRouter provider](https://developers.cloudflare.com/ai-gateway/usage/providers/openrouter/).

Cloudflare's realtime WebSocket provider list includes OpenAI, Google AI Studio, Cartesia, ElevenLabs, Fal AI, and Deepgram (Workers AI), but does not list OpenRouter or Azure MAI. Absence from this list is not proof that every custom route is impossible, but it is insufficient evidence to claim this chain supports native MAI streaming. [Cloudflare realtime API](https://developers.cloudflare.com/ai-gateway/usage/websockets-api/realtime-api/).

Cloudflare's non-realtime WebSocket API carries complete `universal.create` requests and relays provider response chunks. It does not document converting file transcription into an incremental microphone session. Reusing a persistent socket does not change the upstream model's input contract. [Cloudflare non-realtime API](https://developers.cloudflare.com/ai-gateway/usage/websockets-api/non-realtime-api/).

The newer Cloudflare REST API supports ASR via `/ai/run` and Cloudflare billing, but its documentation does not establish MAI availability or an OpenRouter transcription route. It is a different integration, not evidence for the proposed provider-native path. [Cloudflare REST API](https://developers.cloudflare.com/ai-gateway/usage/rest-api/).

Cloudflare Custom Providers support HTTPS upstream APIs and offer a fallback if the native OpenRouter route rejects transcription. Configuring an OpenRouter custom provider would still require a real end-to-end test; this review did not configure or test one. [Cloudflare custom providers](https://developers.cloudflare.com/ai-gateway/configuration/custom-providers/).

## If live MAI transcription is required

Microsoft documents `wss://{resource}.services.ai.azure.com/mai/v1/realtime?intent=transcription`, using a Foundry deployment and Azure API key or Entra token. Configure a transcription session, then send base64 PCM16 mono audio at 16 or 24 kHz with `input_audio_buffer.append`. There is no WAV header. `delta` adds finalized text; MAI-specific `intermediate` replaces the provisional suffix; `completed` supplies the final transcript after explicit `input_audio_buffer.commit`. Server turn detection is unavailable, and session settings cannot change after audio starts. [Microsoft Realtime guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-realtime).

This is a separate public-preview integration. No first-party OpenRouter documentation confirming availability of the Streaming variant was found in this review. [Microsoft streaming overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming).

## Verification still needed

- A successful transcription after funding, confirming model execution, request limits and response shape. The synthetic-audio probe below established routing to OpenRouter's credit check.
- Error handling and recording retention behavior in any proposed app integration.
- If native live transcription is wanted, a distinct Azure integration decision; neither a model-picker entry nor a `stream: true` flag establishes support.

No application changes, paid API calls, gateway configuration changes, or live microphone capture were performed for this research.

## Connectivity probe (5 November 2026)

A one-second synthetic silent WAV was sent as JSON to the configured Cloudflare gateway's `/openrouter/audio/transcriptions` path for `microsoft/mai-transcribe-2`, using the gateway token and stored provider credentials. Provider authorization was omitted and payload logging disabled. The request returned HTTP 402 with `limit_source: openrouter_credits` and a message that audio requires at least $0.50 in balance; this is a minimum balance requirement, not a stated per-request fee. This establishes that the request reached OpenRouter through the gateway; it does not establish successful model execution or transcription response shape.

The initial Python requests returned Cloudflare HTTP 403 error 1010. A descriptive application User-Agent resolved that block, consistent with [Cloudflare's error 1010 documentation](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/). No application code, account settings, or funds were changed.

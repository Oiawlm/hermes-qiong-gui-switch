# Agnes Unified Proxy Design

## Goal

Allow `agnes-2.0-flash` to be selected as a Hermes main model while keeping image handling reliable. Any Hermes slot configured to use Agnes should point at the local Agnes-compatible proxy, so text requests pass through unchanged and base64 image requests are converted to public image URLs before reaching the official Agnes API.

## Context

The current switcher only exposes `agnes-2.0-flash` as a vision model. The reason is local catalog metadata: `agnes-2.0-flash` is marked as `vision`, and main model choices only include `text` and `multimodal` models.

Agnes official docs show `agnes-2.0-flash` as a chat-completions model suitable for Hermes main-model configuration with `https://apihub.agnes-ai.com/v1`. The same docs describe image input as `image_url` with a publicly accessible URL. Hermes image paste sends images to vision-capable models as OpenAI-style `data:image/...;base64,...` content blocks. Therefore, direct Agnes main-model configuration is enough for text, but not the safest path for image prompts.

## Design

### Model Catalog

`agnes-2.0-flash` should be treated as `multimodal`, because it can be a main chat model and can understand images. Its image mode remains `url`, because Agnes requires publicly accessible image URLs for image input.

The Agnes built-in provider should expose the local proxy as the endpoint used by Hermes:

```text
http://localhost:8899/v1
```

The proxy remains responsible for forwarding to the official upstream:

```text
https://apihub.agnes-ai.com/v1
```

This keeps Hermes slot configuration simple: any selected Agnes slot uses the same OpenAI-compatible local endpoint.

### Proxy Behavior

The existing proxy already forwards OpenAI-compatible `/v1/chat/completions` requests and converts base64 images embedded in `messages[].content[].image_url.url`. This behavior should become the supported path for both main-model and vision-auxiliary Agnes requests.

Pure text requests should pass through without image conversion. Image conversion should run only when a request contains `data:image/...;base64,...`.

### Slot Selection

Agnes should appear in both:

- Main model choices.
- Vision model choices.

When the user selects Agnes in either slot, the switcher should start the proxy if it is not already running.

When the user selects non-Agnes models in both slots, the written Hermes config should not retain an Agnes proxy endpoint in any changed slot.

### Vision Slot Auto Mode

The current second prompt only supports selecting a vision model or pressing Enter to keep the existing vision configuration. That can accidentally keep an old Agnes proxy config after the user switches the main model to a vision-capable model such as Doubao.

The vision prompt should offer a clear reset option:

```text
0 = 跟随主模型 / 自动
```

Choosing it should write the vision auxiliary slot as auto/main-following instead of keeping a stale explicit proxy config. The exact config shape should follow Hermes conventions:

```yaml
auxiliary:
  vision:
    provider: auto
    model: ""
    base_url: ""
    api_key: ""
```

This lets Hermes decide whether to send images directly to the current main model or fall back to auxiliary handling.

Pressing Enter should still mean "do not change the vision slot".

### Proxy Lifecycle

The switcher should start the Agnes proxy when the final pending config references Agnes through the local proxy in the main model or vision auxiliary slot.

The switcher should not force-kill unknown processes on port 8899. Process cleanup is limited to ensuring the written Hermes config no longer references the Agnes proxy when Agnes is not selected. PID-file based cleanup is outside this feature.

## Data Flow

### Agnes as Main Model

```text
Hermes main model
-> http://localhost:8899/v1/chat/completions
-> proxy optionally converts base64 image data URLs to public URLs
-> https://apihub.agnes-ai.com/v1/chat/completions
```

### Agnes as Vision Auxiliary

```text
Hermes auxiliary.vision
-> http://localhost:8899/v1/chat/completions
-> proxy converts base64 image data URLs to public URLs
-> https://apihub.agnes-ai.com/v1/chat/completions
```

### Non-Agnes Main Model with Vision Auto

```text
Hermes current main model
-> Hermes native vision routing if supported
-> otherwise Hermes auxiliary auto/fallback routing
```

## Error Handling

- If the proxy is required and not running, the switcher should attempt to start it before writing the final success message.
- If startup fails, the switcher should warn the user that Agnes requests may fail, but still write the requested config so the failure is visible and repeatable.
- The proxy should continue returning upstream HTTP errors as JSON responses when Agnes rejects a request.
- The switcher should not print API keys.

## Testing

Tests should cover local behavior only and avoid live Agnes API calls.

- Catalog test: `agnes-2.0-flash` appears in both main and vision slots and has `image_mode: "url"`.
- Config test: choosing Agnes as main writes `model.base_url: http://localhost:8899/v1`.
- Config test: choosing Agnes as vision writes `auxiliary.vision.base_url: http://localhost:8899/v1`.
- Config test: choosing vision auto resets stale explicit vision model, base URL, and API key values.
- Proxy-start test: selecting Agnes in main or vision starts the proxy; selecting no Agnes does not.
- Existing GLM and proxy tests should continue to pass.

## Non-Goals

- Do not build a full Hermes auxiliary-model manager.
- Do not kill arbitrary processes on port 8899.
- Do not call Agnes live in unit tests.
- Do not change provider key file format.
- Do not expose or log API keys.

## References

- Agnes Hermes configuration docs: `https://agnes-ai.com/doc/cid2`
- Agnes 2.0 Flash docs: `https://agnes-ai.com/doc/agnes-20-flash`
- Hermes vision routing docs: `https://hermes-agent.nousresearch.com/docs/user-guide/features/vision`

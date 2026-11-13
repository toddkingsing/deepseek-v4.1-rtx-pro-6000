# KINGSING Connects Self-Hosted DeepSeek-V4.1-Flash-1017 to Claude Code, Codex, OpenCode and Antigravity

[Original publication: KINGSING Company News](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Flash_CLI_Integration.html)

This GitHub document mirrors the technical configuration in the KINGSING article. It contains complete examples for Claude Code, Codex, OpenCode and Antigravity, plus the validation and operational limits behind the integration.

KINGSING has published and validated a repeatable way to connect its self-hosted DeepSeek-V4.1-Flash-1017 service to four coding agents: Claude Code, Codex CLI, OpenCode and Antigravity CLI. The clients remain the normal vendor-signed tools. A single KINGSING gateway provides their native APIs, a stable model alias and the server-side adaptations needed for real coding work.

Replacing a cloud endpoint with a local model is usually described as changing a base URL. In practice, streaming, tool calls, context metadata, PDFs, images, web search and error reporting all have protocol-specific behavior. Our connection package keeps those details in the gateway and client configuration instead of asking users to use a patched or forked CLI.

## One gateway, four native protocols

| Client | Protocol used by the client | KINGSING endpoint | Important adaptation |
| --- | --- | --- | --- |
| Claude Code | Anthropic Messages | /v1/messages | PDF document blocks, deferred tool references, count_tokens |
| Codex CLI | OpenAI Responses | /v1/responses | Custom provider and model catalog; free-form apply_patch instructions |
| OpenCode | OpenAI Chat Completions | /v1/chat/completions | Provider/model capabilities, PDF and image input, max reasoning variant |
| Antigravity CLI | Gemini generateContent | /v1beta/models/<model>:generateContent | GenAI wire keeps images and PDFs from tool results; explicit model limits |

All four clients use the model alias kingsing. The alias intentionally does not contain a checkpoint name. When KINGSING changes the deployed model, routing can change on the server without editing every developer workstation. The current alias maps to the local DeepSeek-V4.1-Flash-1017 deployment and exposes a configured 1,048,576-token window.

## Inside the gateway

The gateway is a protocol and capability layer, not a transparent reverse proxy. It keeps one routing table for the model alias while accepting Anthropic, OpenAI Responses, OpenAI Chat and Gemini requests. Streaming is forwarded without buffering the complete answer, tool call IDs and JSON object/array shapes survive translation, and usage is recorded as metadata without storing message content or keys.

Several adaptations are specifically important to coding agents. Claude Code sends PDF document blocks and deferred tool references; Codex uses Responses items and a custom free-form apply_patch grammar; OpenCode declares media capabilities before sending file parts; Antigravity can retain images and PDFs from tool results only through its GenAI wire. KINGSING handles these differences at the endpoint boundary so the same self-hosted model serves all four clients.

Search and auxiliary tools are separated from the model protocol. A Dify-backed adapter serves Claude Code and Antigravity search, while the MCP endpoint exposes web_search, web_fetch and generate_image to clients that need explicit tools. Context-overflow errors are rewritten into each protocol's native form, allowing the CLI to compact or report the limit in the way its user interface expects.

## Claude Code

Claude Code uses the Anthropic Messages format. Point ANTHROPIC_BASE_URL at the gateway root, not /v1, because the client appends its own /v1/messages path. The KINGSING adapter converts PDF document blocks into page text and images, implements deferred tool references used by Claude Code's tool search, and provides count_tokens.

```json
{
  "model": "kingsing",
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.kingsing.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_KINGSING_API_KEY",
    "ANTHROPIC_MODEL": "kingsing",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "kingsing",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "kingsing",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "kingsing",
    "ANTHROPIC_DEFAULT_FABLE_MODEL": "kingsing",
    "CLAUDE_CODE_SUBAGENT_MODEL": "kingsing",
    "CLAUDE_CODE_EFFORT_LEVEL": "max",
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "1048576",
    "CLAUDE_CODE_AUTO_MODE_SERVER": "0"
  }
}
```

The setting CLAUDE_CODE_AUTO_MODE_SERVER is set to 0 because this gateway does not provide Anthropic's optional server-side auto-mode action classifier. Auto mode still works through the client classifier; this switch only prevents requests for a server capability the gateway does not expose. Claude Code may print an unrecognized_model message for the custom alias. It is informational when generation succeeds.

## Codex CLI

Codex uses the Responses protocol for custom providers. The provider definition, model catalog and MCP server must stay in user-level Codex configuration because project-level configuration cannot override provider routing. Keep built-in web_search disabled: the local backend does not implement OpenAI's hosted search, and our MCP endpoint supplies web_search, web_fetch and generate_image instead.

```toml
model = "kingsing"
model_provider = "kingsing"
model_context_window = 1048576
model_reasoning_effort = "max"
plan_mode_reasoning_effort = "max"
web_search = "disabled"
model_catalog_json = "C:/Users/YOU/.codex/models-kingsing.json"

[model_providers.kingsing]
name = "kingsing"
base_url = "https://api.kingsing.com/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
experimental_bearer_token = "YOUR_KINGSING_API_KEY"

[mcp_servers.kingsing]
url = "https://api.kingsing.com/v1/mcp"
startup_timeout_sec = 30
tool_timeout_sec = 330

[mcp_servers.kingsing.http_headers]
Authorization = "Bearer YOUR_KINGSING_API_KEY"

[memories]
extract_model = "kingsing"
consolidation_model = "kingsing"
```

The complete models-kingsing.json file is included in the GitHub connection package. It declares max reasoning, the one-million-token context and image input. The adapter turns Codex's grammar-constrained apply_patch tool into text instructions, while Codex still validates the resulting patch locally.

## OpenCode

The tested OpenCode configuration uses the providers v2 schema, not the retired singular provider object. The openai-compatible provider carries the gateway URL and key; model capabilities tell OpenCode which attachments and reasoning controls to send.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "kingsing/kingsing#max",
  "providers": {
    "kingsing": {
      "name": "KINGSING",
      "package": "@opencode/ai/providers/openai-compatible",
      "settings": {
        "baseURL": "https://api.kingsing.com/v1",
        "apiKey": "YOUR_KINGSING_API_KEY"
      },
      "models": {
        "kingsing": {
          "modelID": "kingsing",
          "name": "kingsing",
          "capabilities": {
            "tools": true,
            "input": [
              "text",
              "image",
              "pdf"
            ],
            "output": [
              "text"
            ],
            "reasoning": {
              "supported": true
            }
          },
          "compatibility": {
            "reasoningField": "reasoning",
            "requireReasoning": true,
            "maxTokensField": "max_tokens"
          },
          "limit": {
            "context": 1048576,
            "output": 32768
          },
          "variants": [
            {
              "id": "max",
              "body": {
                "reasoning_effort": "max",
                "thinking": {
                  "type": "enabled"
                }
              }
            }
          ],
          "body": {
            "reasoning_effort": "max",
            "thinking": {
              "type": "enabled"
            }
          }
        }
      }
    }
  },
  "mcp": {
    "servers": {
      "kingsing": {
        "type": "remote",
        "url": "https://api.kingsing.com/v1/mcp",
        "headers": {
          "Authorization": "Bearer YOUR_KINGSING_API_KEY"
        }
      }
    }
  }
}
```

The pdf capability is required if you want OpenCode's read tool to send PDF files. The gateway then converts the file into page text and images. The max variant enables reasoning and sends reasoning_effort=max. OpenCode's title and compaction helpers use the same model; no separate small-model endpoint is required.

## Antigravity CLI

Antigravity needs two kinds of configuration: gateway environment variables and an administrator model table that declares the real context, output and media limits. Use the GenAI wire. On its OpenAI-compatible path, Antigravity drops images and PDFs from tool results before sending the request, so a model that can see images still receives only a binary-file placeholder.

```powershell
$env:AGY_LLM_GATEWAY_URL = "https://api.kingsing.com"
$env:AGY_LLM_GATEWAY_API_KEY = "YOUR_KINGSING_API_KEY"
$env:AGY_LLM_GATEWAY_WIRE_PROTOCOL = "genai"
$env:AGY_LLM_GATEWAY_MODELS = "kingsing"
$env:AGY_LLM_GATEWAY_HEADERS = '{"X-Kingsing-Reasoning-Effort":"max","X-Kingsing-Web-Search":"dify"}'
agy --model kingsing
```

Antigravity reads model limits from %ProgramData%\Antigravity\admin_settings.json. The file below prevents its unknown-model fallback of 32K context and 4K output. Keep the file inside an isolated profile and point ProgramData there for the agy process, otherwise the model list can also affect other Antigravity accounts on the same machine.

```json
{
  "models": {
    "defaultModelId": "kingsing",
    "list": [
      {
        "modelId": "kingsing",
        "displayName": "kingsing",
        "maxTokens": 1048576,
        "maxOutputTokens": 32768,
        "supportsImages": true,
        "supportsPdf": true
      }
    ],
    "tiers": {
      "flash": [
        "kingsing"
      ],
      "flashLite": [
        "kingsing"
      ],
      "pro": [
        "kingsing"
      ]
    }
  }
}
```

MCP tools are configured separately in Antigravity's mcp_config.json. The tested profile uses KINGSING search through the request-header adapter and takes only web_fetch and generate_image from MCP so the model does not see duplicate search tools.

```json
{
  "mcpServers": {
    "kingsing": {
      "disabled": false,
      "serverUrl": "https://api.kingsing.com/v1/mcp?tools=web_fetch,generate_image",
      "headers": {
        "Authorization": "Bearer YOUR_KINGSING_API_KEY"
      }
    }
  }
}
```

## Measured validation

We ran the connection package in an isolated configuration root on November 12, 2026. The test used the installed official binaries, not stub clients. Each CLI received the same arithmetic prompt and returned 121938972. The gateway probes also passed for Dify search, MCP tool discovery, PDF document delivery, Claude Code deferred tool references and the Gemini-compatible entry used by Antigravity.

| Check | Result | Evidence |
| --- | --- | --- |
| Claude Code 2.1.318 | Pass | One-shot model call returned the expected number |
| Codex CLI 0.167.1 | Pass | Responses provider returned the expected number |
| OpenCode 2.2.7 | Pass | Custom provider and max variant returned the expected number |
| Antigravity 1.5.6 | Pass | GenAI route returned the expected number |
| Dify search adapter | Pass | Server-reported web_search_requests > 0 |
| MCP endpoint | Pass | web_search, web_fetch and generate_image listed |
| PDF adaptation | Pass | Model read the marker from a test PDF |
| Deferred tools | Pass | Claude tool_reference request accepted |
| Gemini entry | Pass | generateContent returned the expected marker |

These are compatibility checks, not a new model-quality benchmark. The performance and quality measurements for the four-GPU and eight-GPU deployments remain in our earlier publications. The connection test did not alter the inference service or the model weights.

## What changes from a vendor-hosted model

- Claude Code may display an unrecognized_model notice. Features tied to an Anthropic account, such as remote control, voice and fast mode, are not available through this gateway.
- Codex built-in web search is disabled; MCP replaces it. The model catalog also adds an image-input declaration so Codex can use view_image.
- OpenCode provider fields are version-sensitive. The tested package targets the providers v2 schema in OpenCode 2.2.7.
- Antigravity model limits and media capability are not inferred from the alias. They must be declared in admin_settings.json, and the GenAI route must be used for image and PDF tool results.
- A large local context is not the same as low cold-start latency. Million-token prefill can take about one minute on the single-request path, and concurrent long requests contend for compute.
- The gateway is the compatibility layer. When a CLI adds a new request block or tool type, the gateway must be updated before clients can rely on it.

## Reproduce it

The GitHub package contains complete per-client files, the full Codex model catalog, a sanitized validation snapshot and an offline checker. The Chinese guide provides the same configuration with more troubleshooting notes. Replace the placeholder key, restart each CLI in a new session and verify the actual request path before treating a configuration as live.

- [Chinese CLI integration guide on GitHub](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000/blob/main/文档/CLI接入指南.md)
- [English CLI integration guide on GitHub](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000/blob/main/文档/cli-integration.md)
- [Complete client configuration files](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000/tree/main/配置/CLI)
- [Sanitized validation data](https://github.com/toddkingsing/deepseek-v4.1-rtx-pro-6000/blob/main/数据/2026-11-13-cli-validation.json)
- [Previous eight-GPU DeepSeek article](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Eight_GPU_24_Million_Token_Contexts.html)
- [Original four-GPU DeepSeek article](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Local_AI_Deployment.html)
- [Claude Code gateway documentation](https://code.claude.com/docs/en/llm-gateway)
- [Codex configuration reference](https://developers.openai.com/codex/config-reference/)
- [OpenCode provider documentation](https://opencode.ai/docs/providers/)
- [Antigravity CLI documentation](https://antigravity.google/docs/cli/gcli-migration)

Original publication: KINGSING Company News, November 13, 2026. Claude Code, Codex, OpenCode and Antigravity are products of their respective owners. KINGSING does not claim affiliation with those projects, and the compatibility results describe the versions and gateway build tested here.

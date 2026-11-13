# KINGSING 本地 DeepSeek 接入四个 CLI

[官网英文原文](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Flash_CLI_Integration.html) · [English guide](cli-integration.md)

本文是 KINGSING 官网文章的完整中文技术版。四个客户端均使用官方程序；示例密钥需要替换，不要提交真实密钥到仓库。

本文给出 KINGSING 自部署 DeepSeek-V4.1-Flash-1017 接入 Claude Code、Codex CLI、OpenCode 和 Antigravity CLI 的完整方法。四个客户端都使用官方程序，不修改客户端源码；统一模型别名为 `kingsing`，推理档位为 `max`。

实际接入不只是替换 Base URL。不同客户端分别使用 Anthropic Messages、OpenAI Responses、OpenAI Chat Completions 和 Gemini generateContent；流式输出、工具调用、PDF、图片、联网搜索和上下文超限错误的处理方式都不同。KINGSING 网关负责协议转换，客户端只保存自己的配置和访问密钥。

## 服务参数

| 项目 | 值 |
| --- | --- |
| 模型别名 | kingsing |
| OpenAI 兼容地址 | https://api.kingsing.com/v1 |
| Anthropic 根地址 | https://api.kingsing.com |
| Gemini 根地址 | https://api.kingsing.com |
| MCP 工具端点 | https://api.kingsing.com/v1/mcp |
| 上下文窗口 | 1,048,576 tokens |
| 单次输出上限 | 32,768 tokens |
| 输入能力 | text、image、PDF（由服务端转换） |
| 服务访问密钥 | 由账户提供，示例中统一写作 YOUR_KINGSING_API_KEY |

`kingsing` 是不带模型版本号的稳定别名。后端更换模型时只修改网关路由，不要求四个 CLI 重新写入新的实际模型名。不要把别名改成某个检查点名称，否则客户端配置文件会与后端版本耦合。

## 网关做了什么

KINGSING 网关不是简单的反向代理。它在同一个模型别名下接收 Anthropic Messages、OpenAI Responses、OpenAI Chat Completions 和 Gemini generateContent 四类请求，保留流式输出、工具调用 ID、JSON 对象与数组的区别，并把每个请求的客户端、协议、耗时、首字延迟和令牌用量写入元数据日志。日志不保存消息正文和密钥。

针对编码 CLI，最关键的是能力适配：Claude Code 的 PDF `document` 块和延迟工具引用、Codex 的 Responses item 与自由格式 `apply_patch`、OpenCode 的图片和 PDF 能力声明、Antigravity 的 GenAI 工具结果传递，都在服务端处理。客户端因此可以保持官方二进制，不用维护 fork 或本地补丁。

搜索和辅助工具与模型协议分开：Claude Code 和 Antigravity 的搜索由请求头触发 Dify 适配；需要显式工具的客户端使用 `/v1/mcp` 的 `web_search`、`web_fetch` 和 `generate_image`。上下文超限错误会改写成各协议的原生形式，客户端才能正常压缩或提示。

## Claude Code

Claude Code 走 `/v1/messages`。`ANTHROPIC_BASE_URL` 填域名根地址，不要手工加 `/v1`，客户端会自己拼接接口路径。服务端适配 Claude Code 的 PDF `document` 块、工具延迟加载（`defer_loading` / `tool_reference`）和 `count_tokens`。

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

当前网关没有实现 Anthropic 可选的服务端 auto 模式动作检查，因此设置 `CLAUDE_CODE_AUTO_MODE_SERVER=0`。auto 模式本身仍可使用，动作由客户端分类器检查。自定义模型别名可能触发一行 `unrecognized_model` 提示；只要请求返回正常，这不是失败。需要图像生成时，可额外把 MCP 端点以 `generate_image` 工具加入 Claude Code。

## Codex CLI

Codex 使用 OpenAI Responses 协议。自定义 provider、模型目录和 MCP 服务必须放在用户级 `~/.codex/config.toml`；项目级配置不能覆盖 provider 路由。当前 Codex 的 `wire_api` 只支持 `responses`。本地后端没有 OpenAI 托管搜索，因此把内置 `web_search` 关掉，统一使用 MCP。

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

完整的 `models-kingsing.json` 已随仓库提供，包含 max 档位、上下文和图片输入声明。Codex 的自由格式 `apply_patch` 语法约束由中间层改成文字说明，补丁仍由 Codex 在本地校验。如果启用记忆功能，`[memories]` 的两个模型也必须指向 `kingsing`，否则后台会请求不存在的 OpenAI 模型名。

## OpenCode

以下配置使用 OpenCode 2.x 的 `providers` v2 schema，不是旧的单数 `provider` 字段。模型能力必须显式声明 `image` 和 `pdf`，否则客户端不会把附件发给网关。

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

`model` 的完整引用是 `kingsing/kingsing#max`：第一段是 provider，第二段是模型，`#max` 选择启用思考和 `reasoning_effort=max` 的变体。标题、会话压缩等辅助请求会复用当前模型，不需要再配置一个小模型。配置变化后退出旧会话，重新打开 OpenCode。

## Antigravity CLI

Antigravity 需要两部分配置：网关环境变量，以及声明上下文、输出、图片和 PDF 能力的管理员模型表。必须使用 `genai` 线路；走 OpenAI 兼容线路时，Antigravity 会在客户端丢弃工具结果中的图片和 PDF，只给模型留下 `Showing binary file` 一类占位文字。

```powershell
$env:AGY_LLM_GATEWAY_URL = "https://api.kingsing.com"
$env:AGY_LLM_GATEWAY_API_KEY = "YOUR_KINGSING_API_KEY"
$env:AGY_LLM_GATEWAY_WIRE_PROTOCOL = "genai"
$env:AGY_LLM_GATEWAY_MODELS = "kingsing"
$env:AGY_LLM_GATEWAY_HEADERS = '{"X-Kingsing-Reasoning-Effort":"max","X-Kingsing-Web-Search":"dify"}'
agy --model kingsing
```

`%ProgramData%\Antigravity\admin_settings.json` 用来告诉 Antigravity 真实模型上限。如果不提供，它会把未知模型按 32,768 上下文、4,096 输出处理，长文件会提前截断。为避免影响同一台电脑上的其他 Antigravity 账号，建议给该 agy 进程单独设置 `ProgramData`。

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

MCP 配置放在 `.gemini/config/mcp_config.json`。本方案默认从 MCP 只取 `web_fetch` 和 `generate_image`，搜索则由 `X-Kingsing-Web-Search: dify` 请求头触发，避免模型看到两套搜索工具。

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

## 启动与验证

| 客户端 | 验证命令示例 | 预期 |
| --- | --- | --- |
| Claude Code | claude -p "Calculate 12347 * 9876. Reply with the number only." | 121938972 |
| Codex | codex exec --ephemeral "Calculate 12347 * 9876. Reply with the number only." | 121938972 |
| OpenCode | opencode run "Calculate 12347 * 9876. Reply with the number only." | 121938972 |
| Antigravity | agy --print "Calculate 12347 * 9876. Reply with the number only." | 121938972 |

2026-11-12 的隔离验收使用了 Codex CLI 0.167.1、Claude Code 2.1.318、OpenCode 2.2.7 和 Antigravity 1.5.6。四个 CLI 均返回 121938972；Dify 搜索、MCP 工具列表、PDF 文档适配、Claude Code 延迟工具和 Gemini 入口也全部通过。该测试验证的是接入兼容性，不是新的模型质量或性能评测。

## 常见问题

| 现象 | 检查 |
| --- | --- |
| Claude 显示 unrecognized_model | 自定义别名允许出现提示；看实际回答是否正常，不要为了消提示改回官方模型名 |
| Claude auto mode 提示分类器请求 | 确认 `CLAUDE_CODE_AUTO_MODE_SERVER=0`，然后新开会话 |
| Codex 的搜索只输出文字没有结果 | 保持内置 `web_search=disabled`，检查 MCP 的 `kingsing` 服务 |
| Codex 提示模型目录解析失败 | 核对 `model_catalog_json` 绝对路径和完整目录文件 |
| OpenCode 不发送 PDF | 核对模型 `capabilities.input` 是否包含 `pdf`，并确认版本为 2.x |
| OpenCode 出现旧 provider schema 错误 | 删除或迁移旧的 `provider` 字段，改用 `providers` |
| agy 只看到 32K / 4K 上限 | 检查 admin_settings.json，以及启动时 ProgramData 是否指向槽位目录 |
| agy 读图片得到 Showing binary file | 改回 `genai` 线路，确认 `genai_base_url` 是域名根地址 |
| agy 搜索返回接口错误 | 确认请求头带 `X-Kingsing-Web-Search: dify`，并重新启动 agy |
| MCP 返回 401 | 检查 `Authorization: Bearer ...`；这个端点不使用 OAuth |
| 提示 Prompt is too long | 请求超过后端上下文；客户端通常会自动压缩，单条输入本身超限时需要拆分 |

## 边界

- Claude Code 的远程控制、语音和 fast mode 等绑定 Anthropic 账号的功能不可用；自定义模型提示不影响基本编码。
- Codex 内置托管搜索不可用，搜索、网页读取和图像生成由 KINGSING MCP 提供。
- OpenCode 的 provider schema 会随版本调整。升级 CLI 后先用 `opencode debug config --standalone` 查看实际配置。
- Antigravity 对工具结果中的图片和 PDF 只有 GenAI 线路能完整传递；管理员设置也必须同步声明能力。
- 1,048,576 token 是容量上限，不代表冷启动没有等待；百万输入的单路冷首字等待约一分钟，长请求并发还会互相争用计算。
- 这些结果描述上述版本和当前网关。CLI 升级新增请求块或工具类型后，应重新核对中间层适配。

## 文件与来源

- [官网英文原文](https://www.kingsing.com/news/KINGSING_DeepSeek_V41_Flash_CLI_Integration.html)
- [完整英文指南](cli-integration.md)
- [四套客户端配置](../配置/CLI/README.md)
- [脱敏验收数据](../数据/2026-11-13-cli-validation.json)
- [Claude Code gateway 文档](https://code.claude.com/docs/en/llm-gateway)
- [Codex configuration reference](https://developers.openai.com/codex/config-reference/)
- [OpenCode providers 文档](https://opencode.ai/docs/providers/)
- [Antigravity CLI 文档](https://antigravity.google/docs/cli/gcli-migration)

Original publication: KINGSING Company News, November 13, 2026. 各 CLI、协议和第三方软件归其各自所有者；本文描述的是 KINGSING 当前部署和上述版本的实测结果。

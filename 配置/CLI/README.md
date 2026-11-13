# CLI connection files

[Chinese guide](../../文档/CLI接入指南.md) · [English guide](../../文档/cli-integration.md) · [Project home](../../README.md)

These files are sanitized examples for connecting the official Claude Code, Codex, OpenCode and Antigravity CLIs to the KINGSING gateway. Replace `YOUR_KINGSING_API_KEY` before use. Do not commit a real key.

| File | Purpose |
|---|---|
| `claude-settings.json` | Claude Code user or profile `settings.json` |
| `codex-config.toml` | Codex user-level `~/.codex/config.toml` |
| `codex-models-kingsing.json` | Complete Codex model catalog referenced by `model_catalog_json` |
| `opencode.jsonc` | OpenCode 2.x providers-v2 configuration |
| `agy-gateway.json` | Inputs used by the example Antigravity launcher |
| `agy-admin_settings.json` | Antigravity model limits and media capabilities |
| `agy-mcp_config.json` | Antigravity MCP tool profile |
| `launch-agy.ps1` | Example process-scoped Antigravity launcher for Windows |

The Codex catalog path and the Antigravity `ProgramData` location must be absolute on the target machine. The example launcher keeps Antigravity's profile under its own directory so other accounts on the same computer are not affected.

The tested versions and endpoint checks are recorded in [the validation snapshot](../../数据/2026-11-13-cli-validation.json). Run `python 工具/核验CLI配置.py` from the repository root for an offline consistency check.

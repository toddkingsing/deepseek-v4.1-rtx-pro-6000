from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "配置" / "2026-11-13-cli-integration.json"
DATA = ROOT / "数据" / "2026-11-13-cli-validation.json"
CLI = ROOT / "配置" / "CLI"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_no_private_pattern(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    patterns = [
        r"\b10\.168\.\d+\.\d+\b",
        r"\b192\.168\.\d+\.\d+\b",
        r"/home/todd\b",
        r"/root/",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"\bghp_[A-Za-z0-9]{20,}\b",
        r"\bsk-[A-Za-z0-9]{20,}\b",
    ]
    for pattern in patterns:
        assert not re.search(pattern, text), f"private-looking value in {path}: {pattern}"


def check_links(path: Path) -> int:
    count = 0
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        relative = unquote(target.split("#", 1)[0])
        if not relative:
            continue
        destination = (path.parent / relative).resolve()
        assert destination.is_relative_to(ROOT.resolve()), (path, target)
        assert destination.exists(), (path, target)
        count += 1
    return count


def main() -> None:
    snapshot = read_json(CONFIG)
    validation = read_json(DATA)
    claude = read_json(CLI / "claude-settings.json")
    opencode = read_json(CLI / "opencode.jsonc")
    agy_gateway = read_json(CLI / "agy-gateway.json")
    agy_admin = read_json(CLI / "agy-admin_settings.json")
    agy_mcp = read_json(CLI / "agy-mcp_config.json")
    catalog = read_json(CLI / "codex-models-kingsing.json")
    codex = tomllib.loads((CLI / "codex-config.toml").read_text(encoding="utf-8"))

    service = snapshot["service"]
    assert snapshot["model_alias"] == "kingsing"
    assert service["openai_base_url"] == "https://api.kingsing.com/v1"
    assert service["anthropic_base_url"] == "https://api.kingsing.com"
    assert service["genai_base_url"] == "https://api.kingsing.com"
    assert service["context_window"] == 1048576
    assert service["max_output_tokens"] == 32768

    assert claude["model"] == "kingsing"
    assert claude["env"]["ANTHROPIC_BASE_URL"] == service["anthropic_base_url"]
    assert claude["env"]["ANTHROPIC_MODEL"] == "kingsing"
    assert claude["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "max"
    assert claude["env"]["CLAUDE_CODE_AUTO_MODE_SERVER"] == "0"

    assert codex["model"] == "kingsing"
    assert codex["model_provider"] == "kingsing"
    assert codex["model_context_window"] == 1048576
    assert codex["model_reasoning_effort"] == "max"
    assert codex["web_search"] == "disabled"
    assert codex["model_providers"]["kingsing"]["base_url"] == service["openai_base_url"]
    assert codex["model_providers"]["kingsing"]["wire_api"] == "responses"
    assert codex["mcp_servers"]["kingsing"]["url"] == service["mcp_url"]
    assert codex["memories"]["extract_model"] == "kingsing"
    assert catalog["models"][0]["slug"] == "kingsing"
    assert catalog["models"][0]["context_window"] == 1048576
    assert "image" in catalog["models"][0]["input_modalities"]

    assert opencode["model"] == "kingsing/kingsing#max"
    provider = opencode["providers"]["kingsing"]
    assert provider["settings"]["baseURL"] == service["openai_base_url"]
    model = provider["models"]["kingsing"]
    assert model["modelID"] == "kingsing"
    assert model["limit"]["context"] == 1048576
    assert model["limit"]["output"] == 32768
    assert {"text", "image", "pdf"}.issubset(set(model["capabilities"]["input"]))
    assert model["body"]["reasoning_effort"] == "max"

    assert agy_gateway["wire_protocol"] == "genai"
    assert agy_gateway["genai_base_url"] == service["genai_base_url"]
    assert agy_gateway["reasoning_effort"] == "max"
    assert agy_gateway["web_search"] == "dify"
    entry = agy_admin["models"]["list"][0]
    assert entry["modelId"] == "kingsing"
    assert entry["maxTokens"] == 1048576
    assert entry["maxOutputTokens"] == 32768
    assert entry["supportsImages"] is True
    assert entry["supportsPdf"] is True
    assert agy_mcp["mcpServers"]["kingsing"]["serverUrl"].endswith("?tools=web_fetch,generate_image")

    assert validation["model_alias"] == "kingsing"
    assert all(client["passed"] for client in validation["clients"].values())
    assert all(probe["passed"] for probe in validation["gateway_probes"].values())
    assert set(validation["gateway_probes"]["mcp_tools"]["tools"]) == {
        "web_search",
        "web_fetch",
        "generate_image",
    }

    checked_links = 0
    for path in [
        ROOT / "README.md",
        ROOT / "文档" / "CLI接入指南.md",
        ROOT / "文档" / "cli-integration.md",
        ROOT / "配置" / "CLI" / "README.md",
    ]:
        check_links(path)
        assert_no_private_pattern(path)
        checked_links += 1

    for path in CLI.iterdir():
        if path.is_file():
            assert_no_private_pattern(path)

    result = {
        "passed": True,
        "checked_configs": 8,
        "checked_documents": checked_links,
        "version": validation["tested_versions"],
        "endpoint": service["openai_base_url"],
        "model": "kingsing",
        "context_window": service["context_window"],
        "validation_date": validation["date"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

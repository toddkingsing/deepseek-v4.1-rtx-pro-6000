# Example launcher. Keep this file and agy-admin_settings.json in the agy profile.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$AgyArgs)
$ErrorActionPreference = 'Stop'
$profile = $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $profile 'agy-gateway.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$headers = @{
    'X-Kingsing-Reasoning-Effort' = [string]$config.reasoning_effort
    'X-Kingsing-Web-Search' = [string]$config.web_search
} | ConvertTo-Json -Compress
$keys = @(
    'USERPROFILE', 'ProgramData',
    'AGY_LLM_GATEWAY_URL', 'AGY_LLM_GATEWAY_API_KEY',
    'AGY_LLM_GATEWAY_WIRE_PROTOCOL', 'AGY_LLM_GATEWAY_MODELS',
    'AGY_LLM_GATEWAY_HEADERS'
)
$saved = @{}
try {
    foreach ($key in $keys) {
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
    }
    $env:USERPROFILE = $profile
    $env:ProgramData = Join-Path $profile 'ProgramData'
    $env:AGY_LLM_GATEWAY_URL = [string]$config.genai_base_url
    $env:AGY_LLM_GATEWAY_API_KEY = [string]$config.api_key
    $env:AGY_LLM_GATEWAY_WIRE_PROTOCOL = 'genai'
    $env:AGY_LLM_GATEWAY_MODELS = [string]$config.model
    $env:AGY_LLM_GATEWAY_HEADERS = $headers
    & agy --model $config.model @AgyArgs
    exit $LASTEXITCODE
}
finally {
    foreach ($key in $keys) {
        [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process')
    }
}

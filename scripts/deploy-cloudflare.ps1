<#
.SYNOPSIS
    Deploy Banana Slides Backend Container (Cloudflare Workers + Containers) and verify live endpoints.

.EXAMPLE
    .\scripts\deploy-cloudflare.ps1
    .\scripts\deploy-cloudflare.ps1 -BackendUrl "https://banana-slides-backend.<subdomain>.workers.dev"
    .\scripts\deploy-cloudflare.ps1 -VerifyOnly -FrontendUrl "https://banana-slides-4h7.pages.dev"
#>

[CmdletBinding()]
param(
    [switch]$VerifyOnly,
    [switch]$SkipTypecheck,
    [string]$FrontendUrl = "https://banana-slides-4h7.pages.dev",
    [string]$BackendUrl = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RepoRoot "cloudflare-backend"
$FrontendUrl = $FrontendUrl.TrimEnd("/")
$BackendUrl = $BackendUrl.TrimEnd("/")

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-EndpointCheck {
    param(
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [string]$Method = "GET",
        [string]$Body = "",
        [int]$TimeoutSeconds = 30
    )

    $curlArgs = @("-sS", "-o", "NUL", "-w", "%{http_code}", "--max-time", "$TimeoutSeconds", "-X", $Method)
    if ($Method -ne "GET" -and $Method -ne "HEAD") {
        $curlArgs += @("-H", "Content-Type: application/json", "-d", $Body)
    }
    $curlArgs += $Url

    $statusRaw = & curl.exe @curlArgs
    if ($LASTEXITCODE -ne 0) {
        throw "curl failed when requesting $Method $Url (exit code $LASTEXITCODE)"
    }

    $statusCode = 0
    if (-not [int]::TryParse(($statusRaw | Out-String).Trim(), [ref]$statusCode)) {
        throw "Unexpected HTTP status output for $Method ${Url}: $statusRaw"
    }

    if ($statusCode -ne $ExpectedStatus) {
        throw "Expected HTTP $ExpectedStatus for $Method $Url, got HTTP $statusCode"
    }

    Write-Host "  [OK] $Method $Url -> HTTP $statusCode" -ForegroundColor Green
}

if (-not $VerifyOnly) {
    Write-Step "1/4 Checking Docker Desktop availability"
    $dockerVersion = & docker info --format "{{.ServerVersion}}" 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($dockerVersion)) {
        throw "Docker Desktop is not running. Start Docker Desktop before deploying Cloudflare Containers."
    }
    Write-Host "  [OK] Docker Engine $dockerVersion" -ForegroundColor Green

    Write-Step "2/4 Verifying LF line endings on cloudflare-backend/entrypoint.sh"
    $entrypointPath = Join-Path $BackendDir "entrypoint.sh"
    if (-not (Test-Path $entrypointPath)) {
        throw "Missing $entrypointPath"
    }
    $entrypointBytes = [System.IO.File]::ReadAllBytes($entrypointPath)
    if ($entrypointBytes -contains 13) {
        throw "CRLF detected in $entrypointPath. Convert it to LF line endings before building the Linux container image."
    }
    Write-Host "  [OK] entrypoint.sh uses LF line endings" -ForegroundColor Green

    if (-not $SkipTypecheck) {
        Write-Step "3/4 Running TypeScript check in cloudflare-backend"
        & npm --prefix $BackendDir run typecheck
        if ($LASTEXITCODE -ne 0) {
            throw "TypeScript typecheck failed in $BackendDir"
        }
        Write-Host "  [OK] TypeScript check passed" -ForegroundColor Green
    } else {
        Write-Step "3/4 Skipping TypeScript check (-SkipTypecheck)"
    }

    Write-Step "4/4 Deploying Cloudflare Worker & Container (wrangler deploy)"
    Push-Location $BackendDir
    try {
        & npx wrangler deploy
        if ($LASTEXITCODE -ne 0) {
            throw "wrangler deploy failed with exit code $LASTEXITCODE"
        }
    } finally {
        Pop-Location
    }
}

Write-Step "Verifying live endpoints on $FrontendUrl"
# Allow up to 75s on /health in case the backend container is waking from sleep.
Invoke-EndpointCheck -Url "$FrontendUrl/" -ExpectedStatus 200 -TimeoutSeconds 30
Invoke-EndpointCheck -Url "$FrontendUrl/health" -ExpectedStatus 200 -TimeoutSeconds 75
Invoke-EndpointCheck -Url "$FrontendUrl/api/auth/config" -ExpectedStatus 200 -TimeoutSeconds 30
Invoke-EndpointCheck -Url "$FrontendUrl/api/output-language" -ExpectedStatus 200 -TimeoutSeconds 30
Invoke-EndpointCheck -Url "$FrontendUrl/llms.txt" -ExpectedStatus 200 -TimeoutSeconds 30
Invoke-EndpointCheck -Url "$FrontendUrl/robots.txt" -ExpectedStatus 200 -TimeoutSeconds 30

if (-not [string]::IsNullOrWhiteSpace($BackendUrl)) {
    Write-Step "Verifying direct Backend Worker endpoints on $BackendUrl"
    Invoke-EndpointCheck -Url "$BackendUrl/health" -ExpectedStatus 200 -TimeoutSeconds 75
    Invoke-EndpointCheck -Url "$BackendUrl/api/auth/dev-login" -Method "POST" -Body "{}" -ExpectedStatus 403 -TimeoutSeconds 30
} else {
    Write-Host "`n  [INFO] Direct backend checks skipped (pass -BackendUrl `"https://banana-slides-backend.<subdomain>.workers.dev`" to verify directly)." -ForegroundColor Yellow
}

Write-Host "`nAll checks completed successfully." -ForegroundColor Green

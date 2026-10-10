param()

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$script:testsPassed = 0
$script:testsFailed = 0

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$File,
        [string[]]$Arguments = @(),
        [int[]]$ExpectedExitCodes = @(0)
    )

    $output = @(& $File @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { "$_" }) -join [Environment]::NewLine
    if ($null -eq $exitCode -or $ExpectedExitCodes -notcontains $exitCode) {
        throw "$File $($Arguments -join ' ') exited $exitCode; expected $($ExpectedExitCodes -join ', ').`n$text"
    }

    return [pscustomobject]@{ ExitCode = $exitCode; Output = $text }
}

function Test-Step {
    param([string]$Name, [scriptblock]$Action)

    Write-Host "`n[TEST] $Name" -ForegroundColor Yellow
    try {
        & $Action
        $script:testsPassed += 1
        Write-Host "[PASS]" -ForegroundColor Green
    } catch {
        $script:testsFailed += 1
        Write-Host "[FAIL] $_" -ForegroundColor Red
    }
}

function New-LoopbackListener {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    return $listener
}

Write-Host "PortReach v0.1.0 - Release Verification" -ForegroundColor Cyan

Test-Step "Ruff lint" {
    Invoke-Native -File ruff -Arguments @("check", "src", "tests") | Out-Null
}

Test-Step "Ruff format" {
    Invoke-Native -File ruff -Arguments @("format", "--check", "src", "tests") | Out-Null
}

Test-Step "Mypy" {
    Invoke-Native -File mypy -Arguments @("src", "tests") | Out-Null
}

Test-Step "Unit tests" {
    Invoke-Native -File python -Arguments @("-m", "pytest", "tests", "-q") | Out-Null
}

Test-Step "Clean package build" {
    foreach ($generatedPath in @("build", "dist", "src/portreach.egg-info")) {
        if (Test-Path $generatedPath) {
            Remove-Item $generatedPath -Recurse -Force
        }
    }
    Invoke-Native -File python -Arguments @("-m", "build") | Out-Null
    $expected = @(
        "dist/portreach-0.1.0.tar.gz",
        "dist/portreach-0.1.0-py3-none-any.whl"
    )
    foreach ($artifact in $expected) {
        if (-not (Test-Path $artifact -PathType Leaf)) {
            throw "Expected build artifact is missing: $artifact"
        }
    }
}

Test-Step "Twine package validation" {
    $artifacts = @(
        (Resolve-Path "dist/portreach-0.1.0.tar.gz").Path,
        (Resolve-Path "dist/portreach-0.1.0-py3-none-any.whl").Path
    )
    Invoke-Native -File python -Arguments (@("-m", "twine", "check") + $artifacts) | Out-Null
}

Test-Step "Version command" {
    $result = Invoke-Native -File python -Arguments @("-m", "portreach", "--version")
    if ($result.Output -notmatch "(?m)^portreach 0\.1\.0$") {
        throw "Unexpected version output: $($result.Output)"
    }
}

Test-Step "Help command" {
    $result = Invoke-Native -File python -Arguments @("-m", "portreach", "--help")
    if ($result.Output -notmatch "(?m)^usage: portreach\b") {
        throw "Help output did not identify portreach"
    }
}

Test-Step "Open loopback port and exit code 0" {
    $listener = New-LoopbackListener
    try {
        $port = $listener.LocalEndpoint.Port
        $result = Invoke-Native -File python -Arguments @("-m", "portreach", "127.0.0.1", "$port", "--quiet")
        if ($result.ExitCode -ne 0) { throw "Open-port check returned $($result.ExitCode)" }
    } finally {
        $listener.Stop()
    }
}

Test-Step "Closed loopback port and exit code 1" {
    $listener = New-LoopbackListener
    $port = $listener.LocalEndpoint.Port
    $listener.Stop()
    $result = Invoke-Native -File python -Arguments @("-m", "portreach", "127.0.0.1", "$port", "--quiet") -ExpectedExitCodes @(1)
    if ($result.ExitCode -ne 1) { throw "Closed-port check returned $($result.ExitCode)" }
}

Test-Step "Invalid port and exit code 2" {
    $result = Invoke-Native -File python -Arguments @("-m", "portreach", "127.0.0.1", "99999", "--quiet") -ExpectedExitCodes @(2)
    if ($result.ExitCode -ne 2) { throw "Invalid-input check returned $($result.ExitCode)" }
}

Test-Step "JSON output parses" {
    $listener = New-LoopbackListener
    try {
        $port = $listener.LocalEndpoint.Port
        $result = Invoke-Native -File python -Arguments @("-m", "portreach", "127.0.0.1", "$port", "--json")
        $document = ConvertFrom-Json -InputObject $result.Output -ErrorAction Stop
        if ($document.host -ne "127.0.0.1" -or $document.results.Count -ne 1 -or $document.results[0].status -ne "open") {
            throw "JSON result did not describe the expected open loopback port"
        }
    } finally {
        $listener.Stop()
    }
}

Write-Host "`nRelease verification: $script:testsPassed passed, $script:testsFailed failed, $($script:testsPassed + $script:testsFailed) total"
if ($script:testsFailed -gt 0) {
    exit 1
}
exit 0

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $projectRoot
try {
    & python scripts\run_harness.py
    $harnessExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($harnessExitCode -ne 0) {
    exit $harnessExitCode
}

exit 0

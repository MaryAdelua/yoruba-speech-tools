# Forward CLI arguments without changing any execution policy or storing secrets.
$voiceEvalPython = Get-Command python -ErrorAction SilentlyContinue
$voiceEvalBundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if ($voiceEvalPython) {
    & $voiceEvalPython.Source (Join-Path $PSScriptRoot 'scripts\evaluate_interaction.py') @args
} elseif (Test-Path -LiteralPath $voiceEvalBundled) {
    & $voiceEvalBundled (Join-Path $PSScriptRoot 'scripts\evaluate_interaction.py') @args
} else {
    Write-Error 'Python 3.10+ is required. Install it or use an existing interpreter.'
    exit 2
}
exit $LASTEXITCODE

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$dir = Join-Path $root 'kindle-ai-usage'

git -c core.autocrlf=false clone https://github.com/Kuberwastaken/kindle-ai-usage.git $dir
git -C $dir checkout b647f5f35638818b4b9e332522fbbbda8fafb52f
git -C $dir apply (Join-Path $root 'kindle-ai-usage.patch')
Push-Location $dir
npm ci
npm test
Pop-Location
if (-not (Test-Path (Join-Path $dir '.env'))) {
  $bytes = New-Object byte[] 32
  [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $token = -join ($bytes | ForEach-Object { '{0:x2}' -f $_ })
  $bunx = (Join-Path $env:APPDATA 'npm\node_modules\bun\bin\bunx.exe') -replace '\\', '/'
  (Get-Content (Join-Path $root 'kindle-ai-usage.env.example')) `
    -replace '^KINDLETOKEN_INGEST_TOKEN=.*', "KINDLETOKEN_INGEST_TOKEN=$token" `
    -replace '^KINDLETOKEN_CCUSAGE_COMMAND=BUNX', "KINDLETOKEN_CCUSAGE_COMMAND=$bunx" |
    Set-Content -Encoding ascii (Join-Path $dir '.env')
}

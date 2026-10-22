$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { py -3 scripts/install.py } else { python scripts/install.py }

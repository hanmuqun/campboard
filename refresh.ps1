# One refresh cycle: pull Recreation.gov, diff against the last snapshot, push to D1.
# The website reads D1 at request time, so nothing needs rebuilding or redeploying here.
#
#   .\refresh.ps1          normal run (honours the 20-minute disk cache)
#   .\refresh.ps1 -Force   ignore the cache and hit the network for every campground
param([switch]$Force)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Without this the child process's output gets decoded with the OEM code page and
# Chinese paths in the log turn into mojibake.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$py = "D:\python\python.exe"
$log = Join-Path $PSScriptRoot "data\refresh.log"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$fetchArgs = @("fetch.py", "--workers", "2")
if ($Force) { $fetchArgs += "--no-cache" }

try {
	$fetch = & $py @fetchArgs 2>&1
	$push = & $py push_d1.py 2>&1
	$tail = ($fetch | Select-Object -Last 2) -join " | "
	"$stamp OK  $tail" | Add-Content -Path $log -Encoding utf8
} catch {
	"$stamp FAIL  $($_.Exception.Message)" | Add-Content -Path $log -Encoding utf8
	exit 1
}

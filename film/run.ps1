param([string]$Script, [string[]]$Rest)
$film = Split-Path -Parent $MyInvocation.MyCommand.Path
$sw = [Diagnostics.Stopwatch]::StartNew()
$out = & "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b --factory-startup -P (Join-Path $film $Script) -- @Rest 2>&1
$out | Select-String -Pattern "Traceback|Error|error:|KeyError|AttributeError|TypeError|ValueError|NameError|line \d+|AF:" | Select-Object -Last 30 | ForEach-Object { $_.Line }
"elapsed s: {0:N1}" -f $sw.Elapsed.TotalSeconds

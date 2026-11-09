# keep background renders at below-normal priority so the laptop stays responsive
while ($true) {
  Get-CimInstance Win32_Process -Filter "name='blender.exe'" | Where-Object { $_.CommandLine -match ' -b ' } | ForEach-Object {
    try { $p = Get-Process -Id $_.ProcessId -ErrorAction Stop; if ($p.PriorityClass -ne 'BelowNormal') { $p.PriorityClass = 'BelowNormal' } } catch {}
  }
  Start-Sleep -Seconds 10
}

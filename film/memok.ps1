$c = (Get-Counter '\Memory\Available MBytes','\Memory\Committed Bytes','\Memory\Commit Limit' -ErrorAction SilentlyContinue).CounterSamples
$avail = $c[0].CookedValue
$head = ($c[2].CookedValue - $c[1].CookedValue) / 1MB
if ($avail -gt 4500 -and $head -gt 7000) { exit 0 } else { exit 1 }

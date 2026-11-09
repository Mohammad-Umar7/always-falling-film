# exit 0 when commit headroom is above $args[0] MB (default 3500)
$need = if ($args.Count -gt 0) { [int]$args[0] } else { 3500 }
$c = (Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit' -ErrorAction SilentlyContinue).CounterSamples
$head = ($c[1].CookedValue - $c[0].CookedValue) / 1MB
if ($head -gt $need) { exit 0 } else { exit 1 }

param(
    [string]$CommandFile = (Join-Path $PSScriptRoot "commands\sakura_estate_full.txt"),
    [string]$Center = "408.5 69 -230.5",
    [ValidateSet("SAFE", "NORMAL", "FAST")][string]$Speed = "NORMAL",
    [string]$EndMode = "survival",
    [ValidateSet("YES", "NO")][string]$Sunset = "YES",
    [string]$ChatKey = "t",
    [string]$ConfirmWord = "SAKURA",
    [string]$Title = "SAKURA SHOGUN ESTATE  -  complete build",
    [ValidateSet("BUILD", "REPAIR")][string]$Mode = "BUILD"
)
# ============================================================================
#  Sakura Shogun Estate - chat automation engine
#  Types every command into Minecraft chat for you, in order.
#   * pauses automatically whenever Minecraft is not the active window
#   * saves progress after every command so an interrupted run can resume
# ============================================================================
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class SakuraW32 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$profiles = @{
    "SAFE"   = @{ Open = 120; Paste = 90; Base = 260; PerVol = 40;  Cap = 1600; Every = 40; Rest = 1500 }
    "NORMAL" = @{ Open = 70;  Paste = 45; Base = 110; PerVol = 80;  Cap = 900;  Every = 60; Rest = 800 }
    "FAST"   = @{ Open = 50;  Paste = 35; Base = 70;  PerVol = 110; Cap = 700;  Every = 80; Rest = 600 }
}
$P = $profiles[$Speed]
$progressFile = Join-Path $PSScriptRoot ("progress_" + [IO.Path]::GetFileNameWithoutExtension($CommandFile) + ".txt")

function Write-Line([string]$text, [string]$color = "Gray") { Write-Host $text -ForegroundColor $color }

if (-not (Test-Path -LiteralPath $CommandFile)) {
    Write-Line "Command file not found: $CommandFile" Red; Read-Host "Press Enter to close"; exit 1
}
$Center = ($Center -replace '\s+', ' ').Trim()
if ($Center.Split(' ').Count -ne 3) {
    Write-Line "CENTER must be three numbers, e.g. 408.5 69 -230.5  (got '$Center')" Red; Read-Host; exit 1
}

# ------------------------------------------------------------------ parse the plan
$steps = New-Object System.Collections.Generic.List[object]
$setup = New-Object System.Collections.Generic.List[object]
$inSetup = $false
foreach ($raw in Get-Content -LiteralPath $CommandFile) {
    $line = $raw.Trim()
    if ($line.Length -eq 0) { continue }
    if ($line -eq "#SETUP") { $inSetup = $true; continue }
    if ($line -eq "#ENDSETUP") { $inSetup = $false; continue }
    $step = $null
    if ($line.StartsWith("#WAIT ")) { $step = @{ T = "wait"; V = [int]$line.Substring(6) } }
    elseif ($line.StartsWith("#SECTION ")) { $step = @{ T = "section"; V = $line.Substring(9) } }
    elseif ($line.StartsWith("#IF SUNSET ")) {
        if ($Sunset -eq "YES") { $step = @{ T = "cmd"; V = $line.Substring(11) } }
    }
    elseif ($line.StartsWith("#")) { continue }
    else { $step = @{ T = "cmd"; V = $line } }
    if ($null -eq $step) { continue }
    if ($step.T -eq "cmd") {
        $step.V = $step.V.Replace("{C}", $Center).Replace("{MODE}", $EndMode)
        if ($step.V.Length -gt 256) { Write-Line "Command too long for chat: $($step.V)" Red; Read-Host; exit 1 }
    }
    if ($inSetup) { $setup.Add($step) } else { $steps.Add($step) }
}
$total = ($steps | Where-Object { $_.T -eq "cmd" }).Count + ($setup | Where-Object { $_.T -eq "cmd" }).Count

function Get-Delay([string]$cmd) {
    $m = [regex]::Match($cmd, 'fill ~(-?\d*) ~(-?\d*) ~(-?\d*) ~(-?\d*) ~(-?\d*) ~(-?\d*) ')
    if ($m.Success) {
        $v = @()
        for ($i = 1; $i -le 6; $i++) { $s = $m.Groups[$i].Value; if ($s -eq "") { $v += 0 } else { $v += [int]$s } }
        $vol = ([math]::Abs($v[3] - $v[0]) + 1) * ([math]::Abs($v[4] - $v[1]) + 1) * ([math]::Abs($v[5] - $v[2]) + 1)
        return [int]($P.Base + [math]::Min($P.Cap, $vol / $P.PerVol))
    }
    if ($cmd -match ' kill | forceload | summon ') { return $P.Base + 150 }
    return $P.Base
}

# ------------------------------------------------------------------ resume?
$startIndex = 0
if (Test-Path -LiteralPath $progressFile) {
    $saved = (Get-Content -LiteralPath $progressFile -Raw).Trim().Split('|')
    if ($saved.Count -ge 2 -and $saved[1] -eq $Center -and [int]$saved[0] -gt 0 -and [int]$saved[0] -lt $steps.Count) {
        Write-Line ""
        Write-Line "A previous run stopped part-way (step $($saved[0]) of $($steps.Count))." Yellow
        $ans = Read-Host "Resume from there? Y = resume, N = start over"
        if ($ans -match '^[Yy]') { $startIndex = [int]$saved[0] }
    }
}

# ------------------------------------------------------------------ estimate
$estMs = 0
for ($i = $startIndex; $i -lt $steps.Count; $i++) {
    $s = $steps[$i]
    if ($s.T -eq "cmd") { $estMs += $P.Open + $P.Paste + (Get-Delay $s.V) }
    elseif ($s.T -eq "wait") { $estMs += $s.V }
}
$estMs += [int]($total / $P.Every) * $P.Rest

Write-Line ""
Write-Line ("  " + $Title) Magenta
Write-Line "  ----------------------------------------" DarkMagenta
Write-Line ("  Centre           : {0}" -f $Center) Yellow
Write-Line ("  Commands         : {0}" -f $total)
Write-Line ("  Speed profile    : {0}" -f $Speed)
Write-Line ("  Estimated time   : about {0} minutes" -f [math]::Ceiling($estMs / 60000.0)) Cyan
Write-Line ("  Finish gamemode  : {0}   Sunset on finish: {1}" -f $EndMode, $Sunset)
if ($startIndex -gt 0) { Write-Line ("  Resuming at step : {0}" -f $startIndex) Yellow }
Write-Line ""
if ($Mode -eq "REPAIR") {
    Write-Line "  REPAIR PASS: only the blocks that need fixing are changed; nothing else is cleared." Green
    Write-Line "  Run this on an estate built with the first release. Operator permission (level 3+) needed." Yellow
} else {
    Write-Line "  This CLEARS and REBUILDS a 141 x 181 area around the centre (the old estate)." Red
    Write-Line "  Back up the world first if you can. You need operator permission (level 3+)." Red
}
Write-Line ""
Write-Line "  Before you continue:" White
Write-Line "   1. Join the world/server and stand anywhere (you will be moved automatically)."
Write-Line "   2. Close every menu and chat so you are looking at the world."
Write-Line "   3. Chat must open with the '$ChatKey' key."
Write-Line "   4. Once it starts, do not type or click. If you need the PC, just click away:"
Write-Line "      the build PAUSES by itself and continues when you click back into Minecraft."
Write-Line ""
$confirm = Read-Host ("Type " + $ConfirmWord + " to begin")
if ($confirm -ne $ConfirmWord) { Write-Line "Cancelled." Yellow; exit 0 }

# ------------------------------------------------------------------ find Minecraft
function Find-Minecraft {
    $cands = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'Minecraft' -and $_.MainWindowTitle -notmatch 'Launcher' }
    $java = $cands | Where-Object { $_.ProcessName -match '^javaw?$' } | Select-Object -First 1
    if ($java) { return $java }
    return ($cands | Select-Object -First 1)
}
$mc = Find-Minecraft
while (-not $mc) {
    Write-Line "Minecraft (the game window, not the launcher) was not found. Open it, then press Enter." Yellow
    Read-Host | Out-Null
    $mc = Find-Minecraft
}
Write-Line ("Found: {0}" -f $mc.MainWindowTitle) Green

function Test-Focus {
    $h = [SakuraW32]::GetForegroundWindow()
    $procId = 0
    [SakuraW32]::GetWindowThreadProcessId($h, [ref]$procId) | Out-Null
    return ($procId -eq $mc.Id)
}
function Wait-Focus {
    if (Test-Focus) { return }
    Write-Line ""
    Write-Line "  PAUSED - Minecraft is not the active window." Yellow
    Write-Line "  Click back into Minecraft (in-world, no menu or chat open) to continue..." Yellow
    while (-not (Test-Focus)) { Start-Sleep -Milliseconds 400 }
    Write-Line "  Minecraft is active again - continuing in 2 seconds." Green
    Start-Sleep -Milliseconds 2000
}
function Send-MC([string]$cmd) {
    Wait-Focus
    Set-Clipboard -Value $cmd
    [System.Windows.Forms.SendKeys]::SendWait($ChatKey)
    Start-Sleep -Milliseconds $P.Open
    Wait-Focus
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds $P.Paste
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds (Get-Delay $cmd)
}

for ($i = 8; $i -ge 1; $i--) { Write-Host ("Starting in {0}...  (click into Minecraft now)" -f $i); Start-Sleep -Seconds 1 }
[SakuraW32]::ShowWindow($mc.MainWindowHandle, 9) | Out-Null
[SakuraW32]::SetForegroundWindow($mc.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 1500

$sent = 0
$t0 = Get-Date
$finished = $false
try {
    foreach ($s in $setup) {
        if ($s.T -eq "cmd") { Send-MC $s.V; $sent++ }
        elseif ($s.T -eq "wait") { Start-Sleep -Milliseconds $s.V }
    }
    for ($i = $startIndex; $i -lt $steps.Count; $i++) {
        $s = $steps[$i]
        if ($s.T -eq "section") { Write-Line ""; Write-Line ("== {0}" -f $s.V) Magenta; continue }
        if ($s.T -eq "wait") { Start-Sleep -Milliseconds $s.V; continue }
        Send-MC $s.V
        $sent++
        Set-Content -LiteralPath $progressFile -Value ("{0}|{1}" -f ($i + 1), $Center)
        if (($sent % $P.Every) -eq 0) { Start-Sleep -Milliseconds $P.Rest }
        if (($sent % 50) -eq 0) {
            $el = (Get-Date) - $t0
            $done = [double]($i + 1) / $steps.Count
            $left = if ($done -gt 0.01) { [TimeSpan]::FromSeconds($el.TotalSeconds / $done * (1 - $done)) } else { [TimeSpan]::Zero }
            Write-Host ("  {0,6} / {1}  ({2,5:N1}%)   elapsed {3:hh\:mm\:ss}   remaining ~{4:hh\:mm\:ss}" -f `
                    ($i + 1), $steps.Count, ($done * 100), $el, $left)
        }
    }
    $finished = $true
}
finally {
    if ($finished) {
        Remove-Item -LiteralPath $progressFile -ErrorAction SilentlyContinue
        $el = (Get-Date) - $t0
        Write-Line ""
        Write-Line ("Finished in {0:hh\:mm\:ss}." -f $el) Green
        Write-Line "Scroll up in Minecraft chat if you want to check for any red error lines." Gray
    }
    else {
        Write-Line ""
        Write-Line "The build was stopped before it finished." Red
        Write-Line "Progress is saved - run the same .bat again and choose Y to resume." Yellow
        Write-Line "If you are NOT resuming right away, type these in Minecraft so the world runs normally:" Yellow
        Write-Line "   /tick unfreeze" White
        Write-Line ("   /execute positioned {0} run forceload remove ~-74 ~-74 ~74 ~112" -f $Center) White
        Write-Line "   /gamemode survival" White
    }
}
Read-Host "Press Enter to close"

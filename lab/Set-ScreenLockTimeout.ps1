# Run only after approving the exact change and verifying a recoverable VM snapshot.
[CmdletBinding(SupportsShouldProcess, ConfirmImpact='High')]
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9-]{1,15}$')][string]$AllowedComputer,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_.-]{1,32}$')][string]$AllowedUser,
    [Parameter(Mandatory)][ValidateRange(60,900)][int]$Seconds,
    [Parameter(Mandatory)][ValidateRange(60,900)][int]$ExpectedPreviousSeconds,
    [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string]$SnapshotReference,
    [switch]$Approved
)

$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ine $AllowedComputer -or $env:USERNAME -ine $AllowedUser) {
    throw 'Target computer or test user does not match the allowlist.'
}
if ($Seconds -gt $ExpectedPreviousSeconds) {
    throw 'This handler only allows tightening the timeout. Restore via the approved VM snapshot.'
}
$path = 'HKCU:\Control Panel\Desktop'
$watched = Get-ItemProperty -LiteralPath $path
if ($watched.ScreenSaveTimeOut -ne [string]$ExpectedPreviousSeconds -or
    $watched.ScreenSaveActive -ne '1' -or $watched.ScreenSaverIsSecure -ne '1') {
    throw 'Baseline changed or secure screen saver is not enabled. Recheck the VM.'
}
if (!$WhatIfPreference -and !$Approved) {
    throw 'Explicit operator approval is required.'
}
if ($PSCmdlet.ShouldProcess("$AllowedComputer/$AllowedUser", "Set screen saver timeout to $Seconds")) {
    Set-ItemProperty -LiteralPath $path -Name ScreenSaveTimeOut -Value ([string]$Seconds)
    Write-Output "Timeout written. Use a new read and validate observed lock behavior. Snapshot: $SnapshotReference."
}

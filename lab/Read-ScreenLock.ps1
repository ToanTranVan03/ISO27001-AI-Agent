# Run in the disposable VM under the designated test user's session.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9-]{1,15}$')][string]$AllowedComputer,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_.-]{1,32}$')][string]$AllowedUser
)

$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ine $AllowedComputer -or $env:USERNAME -ine $AllowedUser) {
    throw 'Target computer or test user does not match the allowlist.'
}

$path = 'HKCU:\Control Panel\Desktop'
$configuration = Get-ItemProperty -LiteralPath $path
[pscustomobject]@{
    source = 'windows_hkcu_screen_saver'
    computer = $env:COMPUTERNAME
    user = $env:USERNAME
    observed_at = [DateTimeOffset]::UtcNow.ToString('o')
    timeout_seconds = $configuration.ScreenSaveTimeOut
    screen_saver_active = $configuration.ScreenSaveActive
    password_protected = $configuration.ScreenSaverIsSecure
} | ConvertTo-Json -Compress

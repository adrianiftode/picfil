<#
.SYNOPSIS
    Extract every .zip in a folder that has not been extracted yet.

.DESCRIPTION
    For each *.zip directly in -Root, extracts it into a subfolder named after the
    archive (e.g. "photos.zip" -> ".\photos\"). Archives whose target folder already
    exists are skipped, so it is safe to run repeatedly (e.g. for fresh downloads).

    Uses Windows' built-in tar.exe (bsdtar); no extra software required.

.PARAMETER Root
    Folder that contains the .zip files.

.EXAMPLE
    .\extract_zips.ps1 -Root "D:\photos"

.EXAMPLE
    .\extract_zips.ps1 -Root "D:\photos" -ExtractFolderName "unpacked"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Root
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path

$zips = Get-ChildItem -LiteralPath $Root -Filter '*.zip' -File | Sort-Object Name
Write-Host "Found $($zips.Count) zip archive(s) in $Root"

$i = 0
foreach ($zip in $zips) {
    $i++
    $dest = Join-Path $Root ([System.IO.Path]::GetFileNameWithoutExtension($zip.Name))

    if (Test-Path -LiteralPath $dest) {
        Write-Host "[$i/$($zips.Count)] skip (already extracted): $($zip.Name)"
        continue
    }

    Write-Host "[$i/$($zips.Count)] extract: $($zip.Name)"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & tar.exe -xf $zip.FullName -C $dest
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "tar failed ($LASTEXITCODE) for $($zip.Name)"
    }
}

Write-Host "Done. Extracted folders are next to the archives in $Root"

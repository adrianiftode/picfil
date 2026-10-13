<#
.SYNOPSIS
    Gather all images from a folder tree into a single flat folder.

.DESCRIPTION
    Walks -Root (including subfolders, e.g. the folders produced by extract_zips.ps1)
    and collects every image into one output folder.

    Duplicate handling:
      * If a file with the same name and identical content already exists, it is
        skipped (and removed from the source when -Move is used).
      * If a file with the same name but different content exists, it is renamed
        with a _1, _2, ... suffix instead of overwriting anything.

.PARAMETER Root
    Folder to scan (recursively).

.PARAMETER Output
    Name of the destination folder, created inside -Root. Default: "all images".

.PARAMETER Move
    Move files instead of copying them (saves disk space; empties the sources).

.EXAMPLE
    .\group_images.ps1 -Root "D:\photos"

.EXAMPLE
    .\group_images.ps1 -Root "D:\photos" -Output "gathered" -Move
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string]$Output = 'all images',
    [switch]$Move
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
$group = Join-Path $Root $Output
New-Item -ItemType Directory -Force -Path $group | Out-Null

$imageExt = @('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif',
              '.heic', '.heif', '.webp', '.cr2', '.nef', '.arw', '.raf',
              '.orf', '.dng', '.psd')

$added = 0
$dups = 0
$renamed = 0

function Add-Image {
    param([string]$Src, [bool]$DoMove)

    $name = [System.IO.Path]::GetFileName($Src)
    $ext = [System.IO.Path]::GetExtension($Src).ToLower()
    if ($imageExt -notcontains $ext) { return }

    $target = Join-Path $group $name

    if (Test-Path -LiteralPath $target) {
        $si = Get-Item -LiteralPath $Src
        $ti = Get-Item -LiteralPath $target
        if ($si.Length -eq $ti.Length) {
            $h1 = (Get-FileHash -LiteralPath $Src -Algorithm SHA256).Hash
            $h2 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
            if ($h1 -eq $h2) {
                if ($DoMove) { Remove-Item -LiteralPath $Src -Force }
                Write-Host "duplicate skipped: $name"
                $script:dups++
                return
            }
        }
        $base = [System.IO.Path]::GetFileNameWithoutExtension($name)
        $n = 1
        do {
            $candidate = Join-Path $group ("{0}_{1}{2}" -f $base, $n, $ext)
            $n++
        } while (Test-Path -LiteralPath $candidate)
        $target = $candidate
        Write-Host "name collision renamed: $name -> $([System.IO.Path]::GetFileName($target))"
        $script:renamed++
    }

    if ($DoMove) { Move-Item -LiteralPath $Src -Destination $target }
    else         { Copy-Item -LiteralPath $Src -Destination $target }
    $script:added++
}

$files = Get-ChildItem -LiteralPath $Root -Recurse -File |
         Where-Object { $_.DirectoryName -notlike "$group*" }

Write-Host "Found $($files.Count) file(s); gathering images into '$Output'..."
foreach ($f in $files) { Add-Image -Src $f.FullName -DoMove:$Move }

Write-Host "Done. added=$added  duplicates=$dups  renamed=$renamed"
Write-Host "Output: $group"

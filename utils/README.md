# utils

Helper scripts for the photo pipeline. These are independent of the face-filtering
scripts in the repo root.

| Script | Language | What it does |
|---|---|---|
| `resize_images.py` | Python | Create lightweight, share-ready JPEG copies (WhatsApp / social media). |
| `extract_zips.ps1` | PowerShell | Extract every `.zip` that hasn't been extracted yet. |
| `group_images.ps1` | PowerShell | Gather all images from a folder tree into one flat, deduplicated folder. |

---

## `resize_images.py`

Resizes so the longest edge is at most `--max-dim` (never upscales), re-encodes as a
progressive JPEG, applies EXIF orientation, and **strips metadata** (including GPS) for
privacy. The ICC color profile is kept.

```powershell
# 2048 px long edge, quality 85 (good default for sharing)
python resize_images.py --input "person-DSC00477" --output "person-DSC00477-share"

# smaller, for faster messaging
python resize_images.py --input photos --output photos-small --max-dim 1600 --quality 80
```

| Option | Default | Description |
|---|---|---|
| `--input` | — | Folder with the full-size photos |
| `--output` | — | Folder for the light versions |
| `--max-dim` | `2048` | Max length of the longest edge in px |
| `--quality` | `85` | JPEG quality (1–95) |
| `--suffix` | *(empty)* | Suffix before the extension, e.g. `_share` |

Typical result: ~20 MB photos become ~250 KB each (about 1% of the original).

---

## `extract_zips.ps1`

For each `*.zip` in a folder, extracts it into a subfolder named after the archive
(`photos.zip` → `.\photos\`). Archives whose folder already exists are **skipped**, so
it's safe to run again after adding new downloads. Uses Windows' built-in `tar.exe`.

```powershell
.\extract_zips.ps1 -Root "D:\photos"
```

| Parameter | Required | Description |
|---|---|---|
| `-Root` | yes | Folder containing the `.zip` files |

---

## `group_images.ps1`

Walks a folder tree (e.g. the folders produced by `extract_zips.ps1`) and gathers every
image into a single flat output folder.

- Duplicate files (identical content) are skipped.
- Name collisions with **different** content are renamed with a `_1`, `_2`, ... suffix —
  nothing is ever overwritten.

```powershell
# copy everything into "all images"
.\group_images.ps1 -Root "D:\photos"

# move instead of copy (saves disk space, empties the source folders)
.\group_images.ps1 -Root "D:\photos" -Output "gathered" -Move
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `-Root` | yes | — | Folder to scan (recursively) |
| `-Output` | no | `all images` | Destination folder name, created inside `-Root` |
| `-Move` | no | *(copy)* | Move files instead of copying |

---

## Typical full pipeline

```powershell
# 1) unpack all downloaded archives
.\extract_zips.ps1 -Root "D:\photos"

# 2) put every image in one place
.\group_images.ps1 -Root "D:\photos" -Move

# 3) then use the root scripts to filter by person, and
python ..\..\picfil\utils\resize_images.py --input "..\person-DSC00477" --output "..\person-DSC00477-share"
```

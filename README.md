# picfil

Local, offline **photo filtering by person**. Point it at a folder of photos and a
single reference photo of someone, and it finds every photo that person appears in —
no cloud, no accounts, nothing uploaded.

Built on [InsightFace](https://github.com/deepinsight/insightface) (SCRFD face detection +
ArcFace recognition) running through ONNX Runtime. 100% free and open source, runs on CPU.

## Features

- **Filter by person** from one reference photo (or several).
- **Two-step workflow**: scan once, then experiment with thresholds as much as you like
  without rescanning (results are cached in a CSV).
- **Duplicate-safe**: identical photos are detected by hash, name collisions are renamed.
- **Offline & private**: everything runs locally; the only download is the face model,
  fetched once on first run.

## Requirements

- Python 3.9+ (tested on 3.11)
- ~500 MB disk for dependencies + models (CPU only; no GPU required)

## Install

```powershell
git clone https://github.com/adrianiftode/picfil picfil
cd picfil

py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On first run, the `buffalo_l` models (~280 MB) are downloaded automatically to
`~/.insightface/models/buffalo_l`. After that, everything works offline.

## Quick start

Say your photos are in `D:\photos` and you have a clear photo of the person in mind.

```powershell
# 0) optional: check the reference photo is usable
.\.venv\Scripts\python.exe filter_by_person.py --reference "D:\photos\DSC00477.jpg" --inspect

# 1) scan the whole folder once (detects faces + computes similarity)
.\.venv\Scripts\python.exe filter_by_person.py --input "D:\photos" ^
    --reference "D:\photos\DSC00477.jpg" --report scan.csv --scan-only

# 2) copy the matches into a folder
.\.venv\Scripts\python.exe apply_report.py --report scan.csv --threshold 0.40 --output "person-DSC00477"
```

The scan prints a similarity histogram so you can see the natural gap between the
person (usually > 0.6) and everyone else (< 0.3). Pick a threshold inside that gap.

## Choosing a threshold

| Similarity | Meaning |
|---|---|
| `>= 0.6` | Very confident match |
| `0.4 - 0.6` | Likely match |
| `0.3 - 0.4` | Uncertain — inspect these |
| `< 0.3` | Different person |

Re-apply a different threshold without rescanning:

```powershell
.\.venv\Scripts\python.exe apply_report.py --report scan.csv --threshold 0.45 --output "person-DSC00477" --clean
```

## Options

### `filter_by_person.py`

| Option | Description |
|---|---|
| `--input` | Folder of photos to scan |
| `--reference` | One or more reference photos of the person (required) |
| `--report` | Where to write the CSV (default `scan.csv`) |
| `--scan-only` | Only scan + write CSV, don't copy |
| `--output` / `--threshold` / `--move` | Copy/move matches directly at this threshold |
| `--recursive` | Also scan subfolders |
| `--ref-face N` | Use only face index N from the reference (when it has several) |
| `--provider CUDAExecutionProvider` | Use an NVIDIA GPU for much faster scans |
| `--inspect` | Just report faces found in the reference photo |

### `apply_report.py`

| Option | Description |
|---|---|
| `--report` | The `scan.csv` to read |
| `--threshold` | Minimum best-similarity to include (default `0.40`) |
| `--output` | Destination folder |
| `--move` | Move instead of copy |
| `--clean` | Empty the output folder first |
| `--min-faces` | Require at least N faces in the photo |

## Repo layout

```
picfil/
├── filter_by_person.py     # scan photos, detect faces, compare to a reference
├── apply_report.py         # turn a scan.csv into a folder of matches at any threshold
├── requirements.txt
└── utils/
    ├── resize_images.py    # make lightweight share-ready JPEGs
    ├── extract_zips.ps1    # extract all not-yet-extracted .zip files
    ├── group_images.ps1    # gather all images into one flat, deduplicated folder
    └── README.md
```

## Privacy & notes

- All processing is local. No image ever leaves your machine.
- Face recognition can miss profile shots, sunglasses, low light, or small faces —
  always spot-check results, and add more reference photos of the person to improve recall.
- The `buffalo_l` model weights are free for non-commercial use; check InsightFace's
  model license before commercial use.

## License

Released under the [MIT License](LICENSE).

> **Note on models:** the code in this repo is MIT-licensed, but the pretrained
> **buffalo_l** face models downloaded at runtime are distributed by InsightFace for
> **non-commercial use** only. If you intend to use this commercially, swap in models
> licensed for your case.

#!/usr/bin/env python
"""
Filter a folder of photos by a person, using a reference photo (offline, InsightFace ArcFace).

Workflow
--------
1) Inspect the reference photo (optional, shows how many faces were found):
     python filter_by_person.py --reference "photos/DSC00477.jpg" --inspect

2) Scan the whole folder once (detects faces, computes similarity, writes a CSV):
     python filter_by_person.py --input "photos" --reference "photos/DSC00477.jpg" --report scan.csv --scan-only

3) Apply a threshold (copies/moves matches) without rescanning:
     python apply_report.py --report scan.csv --threshold 0.40 --output "person-DSC00477"

Everything runs offline. On first run the buffalo_l models are downloaded once
to ~/.insightface/models/buffalo_l (about 280 MB).
"""
import argparse
import csv
import os
import shutil
import time

import cv2
import numpy as np


def imread_unicode(path):
    """cv2.imread fails on some non-ASCII paths; decode bytes instead."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def build_app(model, provider, det_size):
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name=model, providers=[provider], allowed_modules=["detection", "recognition"])
    app.prepare(ctx_id=0 if provider != "CPUExecutionProvider" else -1, det_size=(det_size, det_size))
    return app


def get_faces(app, img):
    faces = app.get(img)
    # largest faces first
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces


def load_reference_embeddings(app, ref_paths, ref_face):
    embs = []
    for rp in ref_paths:
        img = imread_unicode(rp)
        if img is None:
            print(f"[WARN] cannot read reference: {rp}")
            continue
        faces = get_faces(app, img)
        if not faces:
            print(f"[WARN] no face detected in reference: {rp}")
            continue
        print(f"[REF] {os.path.basename(rp)}: {len(faces)} face(s) detected")
        for i, f in enumerate(faces):
            area = (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
            print(f"      face #{i}  det_score={f.det_score:.3f}  area={int(area)}")
        if ref_face is not None and 0 <= ref_face < len(faces):
            chosen = [faces[ref_face]]
        elif ref_face is None:
            chosen = faces
        else:
            chosen = [faces[0]]
        for f in chosen:
            embs.append(np.asarray(f.normed_embedding, dtype=np.float32))
    if not embs:
        raise SystemExit("No usable reference faces. Provide a clearer photo of the person.")
    return np.vstack(embs)


def list_images(folder, recursive):
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".heif", ".gif"}
    out = []
    if recursive:
        for root, _, files in os.walk(folder):
            for fn in files:
                if os.path.splitext(fn)[1].lower() in exts:
                    out.append(os.path.join(root, fn))
    else:
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            if os.path.isfile(p) and os.path.splitext(fn)[1].lower() in exts:
                out.append(p)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="Filter photos by person using a reference image (offline).")
    ap.add_argument("--input", help="folder containing the photos to scan")
    ap.add_argument("--reference", nargs="+", required=True, help="one or more reference photos of the person")
    ap.add_argument("--output", help="output folder for matching photos")
    ap.add_argument("--threshold", type=float, default=0.40, help="cosine similarity threshold (default 0.40)")
    ap.add_argument("--move", action="store_true", help="move matches instead of copying")
    ap.add_argument("--recursive", action="store_true", help="scan subfolders of --input")
    ap.add_argument("--model", default="buffalo_l", help="InsightFace model pack (default buffalo_l)")
    ap.add_argument("--provider", default="CPUExecutionProvider", help="onnxruntime provider (e.g. CUDAExecutionProvider)")
    ap.add_argument("--det-size", type=int, default=640, help="face detector input size")
    ap.add_argument("--ref-face", type=int, default=None, help="which face index in the reference to use (default: all)")
    ap.add_argument("--inspect", action="store_true", help="only inspect the reference photo(s), do not scan")
    ap.add_argument("--report", default="scan.csv", help="write the scan CSV to this path (default scan.csv)")
    ap.add_argument("--scan-only", action="store_true", help="scan and write report, do not copy anything")
    args = ap.parse_args()

    t0 = time.time()
    print("[*] loading models (first run downloads them, may take a minute)...")
    app = build_app(args.model, args.provider, args.det_size)
    print(f"[*] model ready ({time.time() - t0:.1f}s)")

    ref_embs = load_reference_embeddings(app, args.reference, args.ref_face)
    print(f"[*] using {len(ref_embs)} reference embedding(s)")

    if args.inspect:
        return
    if not args.input:
        raise SystemExit("--input is required unless --inspect is used.")

    images = list_images(args.input, args.recursive)
    print(f"[*] scanning {len(images)} image(s)...")

    if not args.scan_only and args.output:
        os.makedirs(args.output, exist_ok=True)

    rows = []
    matches = 0
    for i, path in enumerate(images, 1):
        img = imread_unicode(path)
        if img is None:
            rows.append((path, 0, ""))
            print(f"[{i}/{len(images)}] unreadable {os.path.basename(path)}")
            continue
        faces = get_faces(app, img)
        if not faces:
            rows.append((path, 0, ""))
            continue
        best = -1.0
        for f in faces:
            emb = np.asarray(f.normed_embedding, dtype=np.float32)
            sim = float(np.max(ref_embs @ emb))
            if sim > best:
                best = sim
        rows.append((path, len(faces), f"{best:.4f}"))
        if best >= args.threshold:
            matches += 1
            if not args.scan_only and args.output:
                dest = os.path.join(args.output, os.path.basename(path))
                if args.move:
                    shutil.move(path, dest)
                else:
                    shutil.copy2(path, dest)
            print(f"[{i}/{len(images)}] MATCH {os.path.basename(path)} sim={best:.3f} ({matches})")
        elif i % 25 == 0:
            print(f"[{i}/{len(images)}] ... scanning ({matches} matches so far)")

    with open(args.report, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "n_faces", "best_similarity"])
        w.writerows(rows)

    sims = [float(r[2]) for r in rows if r[2] != ""]
    print("\n==== SUMMARY ====")
    print(f"scanned         : {len(rows)}")
    print(f"with faces      : {len(sims)}")
    print(f"matches @ {args.threshold}: {matches}")
    if sims:
        arr = np.array(sims)
        for lo, hi in [(0.6, 1.01), (0.5, 0.6), (0.45, 0.5), (0.4, 0.45), (0.35, 0.4), (0.3, 0.35), (0.0, 0.3)]:
            print(f"  sim [{lo:.2f},{hi:.2f}): {int(((arr >= lo) & (arr < hi)).sum())}")
        print(f"  max sim: {arr.max():.3f}")
    print(f"report          : {os.path.abspath(args.report)}")
    print(f"elapsed         : {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

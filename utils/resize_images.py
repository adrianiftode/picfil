#!/usr/bin/env python
"""Create lightweight, share-ready JPEG copies of photos (for WhatsApp / social media).

- Resizes so the longest edge is at most --max-dim (never upscales).
- Re-encodes as progressive JPEG at the given --quality.
- Applies EXIF orientation so rotation is correct, then strips metadata (privacy).
- Keeps the ICC color profile so colors stay accurate.

Examples
--------
python resize_images.py --input "person-DSC00477" --output "person-DSC00477-share"
python resize_images.py --input photos --output photos-small --max-dim 1600 --quality 80
"""
import argparse
import os
import time

from PIL import Image, ImageOps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="folder with the full-size photos")
    ap.add_argument("--output", required=True, help="folder for the light versions")
    ap.add_argument("--max-dim", type=int, default=2048, help="max length of the longest edge (px)")
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality 1-95")
    ap.add_argument("--suffix", default="", help="suffix before extension, e.g. _share")
    args = ap.parse_args()

    Image.MAX_IMAGE_PIXELS = None  # allow large images without warnings
    os.makedirs(args.output, exist_ok=True)

    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    files = sorted(
        os.path.join(args.input, f)
        for f in os.listdir(args.input)
        if os.path.splitext(f)[1].lower() in exts
    )

    t0 = time.time()
    total_in = 0
    total_out = 0
    done = 0
    for i, path in enumerate(files, 1):
        name = os.path.basename(path)
        try:
            with Image.open(path) as im:
                icc = im.info.get("icc_profile")
                im = ImageOps.exif_transpose(im)  # bake orientation
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                elif im.mode == "L":
                    im = im.convert("RGB")
                w, h = im.size
                scale = min(1.0, args.max_dim / float(max(w, h)))
                if scale < 1.0:
                    im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)

                stem, _ = os.path.splitext(name)
                dest = os.path.join(args.output, f"{stem}{args.suffix}.jpg")
                save_kwargs = dict(format="JPEG", quality=args.quality, optimize=True, progressive=True)
                if icc:
                    save_kwargs["icc_profile"] = icc
                im.save(dest, **save_kwargs)

            insize = os.path.getsize(path)
            outsize = os.path.getsize(dest)
            total_in += insize
            total_out += outsize
            done += 1
            print(f"[{i}/{len(files)}] {name}: {insize/1e6:.1f}MB -> {outsize/1e6:.2f}MB ({outsize*100//insize}%)")
        except Exception as e:
            print(f"[{i}/{len(files)}] FAILED {name}: {e}")

    print("\n==== SUMMARY ====")
    print(f"converted   : {done}/{len(files)}")
    print(f"total size  : {total_in/1e6:.0f} MB -> {total_out/1e6:.0f} MB ({total_out*100//max(1,total_in)}%)")
    if done:
        print(f"average     : {total_out/done/1e6:.2f} MB/image")
    print(f"max edge    : {args.max_dim}px   quality: {args.quality}")
    print(f"output      : {os.path.abspath(args.output)}")
    print(f"elapsed     : {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()

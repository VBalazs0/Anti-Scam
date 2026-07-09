import os
from PIL import Image, ImageOps, ImageFilter
import imagehash


BLUR_RADIUS = 5


def _blur(img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))


def _compute_hashes(img: Image.Image, label: str = "") -> dict:
    blurred = _blur(img)
    flipped = ImageOps.mirror(img)
    h = {
        "phash": imagehash.phash(img),
        "dhash": imagehash.dhash(img),
        "ahash": imagehash.average_hash(img),
        "colorhash": imagehash.colorhash(img),
        "whash": imagehash.whash(img),
        "phash_blur": imagehash.phash(blurred),
        "dhash_blur": imagehash.dhash(blurred),
        "ahash_blur": imagehash.average_hash(blurred),
        "phash_flip": imagehash.phash(flipped),
        "dhash_flip": imagehash.dhash(flipped),
    }
    if label:
        print(f"  {label}: phash={h['phash']} dhash={h['dhash']} blur_phash={h['phash_blur']}")
    return h


class ScamDetector:
    def __init__(self, images_dir: str, threshold: int = 16):
        self.threshold = threshold
        self.refs = []
        self._load_reference_images(images_dir)

    def _load_reference_images(self, images_dir: str):
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
        if not os.path.isdir(images_dir):
            print(f"WARNING: directory not found: {images_dir}")
            return
        for fname in sorted(os.listdir(images_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in valid_extensions:
                path = os.path.join(images_dir, fname)
                try:
                    with Image.open(path) as img:
                        ref = {"name": fname}
                        ref.update(_compute_hashes(img, fname))
                        self.refs.append(ref)
                except Exception as e:
                    print(f"  Failed to load {fname}: {e}")

        print(f"Loaded {len(self.refs)} reference scam images")

    def is_scam(self, image: Image.Image) -> tuple[bool, str | None]:
        h = _compute_hashes(image)

        best = {"dist": 999, "name": None, "algo": None}

        ALGO_MAP = {
            "phash":      h["phash"],
            "dhash":      h["dhash"],
            "ahash":      h["ahash"],
            "colorhash":  h["colorhash"],
            "whash":      h["whash"],
            "phash_blur": h["phash_blur"],
            "dhash_blur": h["dhash_blur"],
            "ahash_blur": h["ahash_blur"],
            "phash_flip": h["phash_flip"],
            "dhash_flip": h["dhash_flip"],
        }

        for ref in self.refs:
            for algo_name, test_hash in ALGO_MAP.items():
                dist = test_hash - ref[algo_name]

                if dist < best["dist"]:
                    best["dist"] = dist
                    best["name"] = ref["name"]
                    best["algo"] = algo_name

        if best["dist"] <= self.threshold:
            print(f"  Match: {best['name']} via {best['algo']} (dist={best['dist']})")
            return True, best["name"]
        return False, None

    @property
    def is_ready(self) -> bool:
        return len(self.refs) > 0

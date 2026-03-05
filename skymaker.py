"""
skymaker.py — Minecraft 1.8.9 OptiFine / MCPatcher Sky Resource Pack Generator

For OptiFine 1.8.9, ALL six cube faces are stored in ONE combined image
in this exact 3x2 grid layout:

  Top row:    [ Bottom(0,0) ] [ Top(1,0)   ] [ Back(2,0)  ]
  Bottom row: [ Left(0,1)   ] [ Front(1,1) ] [ Right(2,1) ]

The faces are blended at their seams so there are no hard cuts.
"""

import sys, json, math, random, zipfile, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

DEFAULT_RESOLUTION = 1024
VALID_RESOLUTIONS  = (512, 1024, 2048, 4096)

# Grid cell positions (col, row)
GRID_FACE_MAP = {
    "bottom": (0, 0),
    "top":    (1, 0),
    "back":   (2, 0),
    "left":   (0, 1),
    "front":  (1, 1),
    "right":  (2, 1),
}

# For 1.8.9 OptiFine the combined grid image is referenced as sky1.png
# Additional overlays use sky2-sky8
ALL_PROPERTY_KEYS = ["sky1", "sky2", "sky3", "sky4", "sky5", "sky6", "sky7", "sky8"]

PACK_MCMETA = {"pack": {"pack_format": 1, "description": "Custom Sky Pack — SkyMaker"}}

PROP_TMPL = (
    "source=./{source}\n"
    "blend={blend}\n"
    "rotate={rotate}\n"
    "speed={speed}\n"
    "axis={axis}\n"
    "startFadeIn={startFadeIn}\n"
    "endFadeIn={endFadeIn}\n"
    "startFadeOut={startFadeOut}\n"
    "endFadeOut={endFadeOut}\n"
)

FACE_FADE = {k: dict(startFadeIn="18:00", endFadeIn="19:00",
                     startFadeOut="05:00", endFadeOut="06:00")
             for k in ["sky1","sky2","sky3","sky4","sky5","sky6","sky8"]}
FACE_FADE["sky7"] = dict(startFadeIn="20:00", endFadeIn="21:00",
                         startFadeOut="04:00", endFadeOut="05:00")

def log(m): print(f"[SkyMaker] {m}")
def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)

def is_grid(img):
    w, h = img.size
    return 1.3 <= (w / h) <= 1.7

def load_image(path):
    p = Path(path)
    if not p.exists(): raise FileNotFoundError(f"Not found: {path}")
    img = Image.open(p).convert("RGBA")
    w, h = img.size
    if w < 64 or h < 64: raise ValueError(f"Image too small ({w}x{h})")
    log(f"Loaded {p.name}  {w}x{h}px")
    return img


# ── Face extraction ───────────────────────────────────────────────────────────

def extract_faces(img: Image.Image, face_res: int) -> dict:
    """
    Split the 3x2 grid into 6 individual face images, each face_res x face_res.
    """
    w, h = img.size
    cw, ch = w // 3, h // 2
    faces = {}
    for name, (col, row) in GRID_FACE_MAP.items():
        face = img.crop((col*cw, row*ch, col*cw+cw, row*ch+ch))
        face = face.resize((face_res, face_res), Image.LANCZOS)
        faces[name] = face
        log(f"  Extracted face '{name}'  col={col} row={row}")
    return faces


# ── Seam blending ─────────────────────────────────────────────────────────────

def blend_edge(face_a: np.ndarray, face_b: np.ndarray,
               blend_px: int, edge: str) -> tuple:
    """
    Blend the touching edges of two adjacent face arrays.
    edge: 'right'  = right edge of face_a blends with left  edge of face_b
          'bottom' = bottom edge of face_a blends with top   edge of face_b
    Returns modified (face_a, face_b).
    """
    a = face_a.astype(np.float32)
    b = face_b.astype(np.float32)
    ramp = np.linspace(1.0, 0.0, blend_px, dtype=np.float32)  # 1→0

    if edge == 'right':
        for i in range(blend_px):
            alpha = ramp[i]
            col_a = a[:, -(blend_px - i)].copy()
            col_b = b[:, i].copy()
            blended = alpha * col_a + (1 - alpha) * col_b
            a[:, -(blend_px - i)] = blended
            b[:, i]               = blended
    elif edge == 'bottom':
        for i in range(blend_px):
            alpha = ramp[i]
            row_a = a[-(blend_px - i), :].copy()
            row_b = b[i, :].copy()
            blended = alpha * row_a + (1 - alpha) * row_b
            a[-(blend_px - i), :] = blended
            b[i, :]               = blended

    return np.clip(a, 0, 255).astype(np.uint8), np.clip(b, 0, 255).astype(np.uint8)


def blend_all_seams(faces: dict, blend_px: int) -> dict:
    """
    Apply seam blending between all adjacent cube faces.
    Adjacency for the 3x2 grid (horizontal and vertical neighbours):
      Horizontal: bottom-top, top-back  (row 0)
                  left-front, front-right (row 1)
      Vertical:   bottom-left, top-front, back-right
    """
    arr = {k: np.array(v, dtype=np.uint8) for k, v in faces.items()}

    # ── Horizontal seams (right edge of A → left edge of B) ──
    h_pairs = [
        ("bottom", "top"),    # row 0: col0 → col1
        ("top",    "back"),   # row 0: col1 → col2
        ("left",   "front"),  # row 1: col0 → col1
        ("front",  "right"),  # row 1: col1 → col2
    ]
    for a_name, b_name in h_pairs:
        log(f"  Blending seam: {a_name} ↔ {b_name} (horizontal)")
        arr[a_name], arr[b_name] = blend_edge(
            arr[a_name], arr[b_name], blend_px, 'right')

    # ── Vertical seams (bottom edge of A → top edge of B) ──
    v_pairs = [
        ("bottom", "left"),   # col0: row0 → row1
        ("top",    "front"),  # col1: row0 → row1
        ("back",   "right"),  # col2: row0 → row1
    ]
    for a_name, b_name in v_pairs:
        log(f"  Blending seam: {a_name} ↔ {b_name} (vertical)")
        arr[a_name], arr[b_name] = blend_edge(
            arr[a_name], arr[b_name], blend_px, 'bottom')

    return {k: Image.fromarray(v, "RGBA") for k, v in arr.items()}


# ── Reassemble combined grid image ────────────────────────────────────────────

def assemble_grid(faces: dict, face_res: int) -> Image.Image:
    """
    Reassemble the 6 blended faces back into a single 3x2 grid image.
    Layout:
      [ bottom ] [ top   ] [ back  ]
      [ left   ] [ front ] [ right ]
    """
    grid = Image.new("RGBA", (face_res * 3, face_res * 2), (0, 0, 0, 255))
    layout = [
        ("bottom", 0, 0), ("top",   1, 0), ("back",  2, 0),
        ("left",   0, 1), ("front", 1, 1), ("right", 2, 1),
    ]
    for name, col, row in layout:
        grid.paste(faces[name], (col * face_res, row * face_res))
    log(f"  Assembled combined grid: {face_res*3}x{face_res*2}px")
    return grid


# ── Extra textures ────────────────────────────────────────────────────────────

def make_starfield(res: int) -> Image.Image:
    img  = Image.new("RGBA", (res, res), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rng  = random.Random(42)
    for _ in range(4000):
        x, y = rng.randint(0, res-1), rng.randint(0, res-1)
        br   = rng.randint(160, 255)
        sz   = rng.choices([0, 1], weights=[80, 20])[0]
        c    = (br, br, br, br)
        if sz == 0: draw.point((x, y), fill=c)
        else:       draw.ellipse((x-1, y-1, x+1, y+1), fill=c)
    return img.filter(ImageFilter.GaussianBlur(0.6))

def make_cloud(res: int) -> Image.Image:
    rng   = np.random.default_rng(7)
    noise = np.zeros((res, res), dtype=np.float32)
    amp, freq = 1.0, 1
    for _ in range(6):
        s   = max(1, res // freq)
        lyr = np.array(
            Image.fromarray((rng.random((s, s)).astype(np.float32)*255)
                            .astype(np.uint8)).resize((res, res), Image.BILINEAR),
            dtype=np.float32)
        noise += lyr * amp
        amp *= 0.5; freq *= 2
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-9)
    cloud = Image.fromarray((noise*255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(8))
    arr  = np.array(cloud, dtype=np.float32)
    rgba = np.zeros((res, res, 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[...,  3] = np.clip((arr - 120) * 3, 0, 220).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

def make_pack_icon(img: Image.Image) -> Image.Image:
    w, h = img.size
    size = min(w, h)
    icon = img.crop(((w-size)//2, (h-size)//2, (w+size)//2, (h+size)//2))
    return icon.resize((64, 64), Image.LANCZOS)


# ── Properties ────────────────────────────────────────────────────────────────

def write_props(dest: Path, key: str):
    # sky1 = the main combined sky grid
    # sky7 = starfield night overlay
    if key == "sky7":   src = "starfield.png"
    elif key == "sky2": src = "cloud1.png"
    else:               src = f"{key}.png"

    (dest / f"{key}.properties").write_text(
        PROP_TMPL.format(source=src, blend="add", rotate="true",
                         speed="1.0", axis="0.0 1.0 0.0",
                         **FACE_FADE[key]),
        encoding="utf-8")


# ── Resource pack builder ─────────────────────────────────────────────────────

class ResourcePackBuilder:
    def __init__(self, out_root: Path):
        self.root      = out_root
        self.pack_dir  = out_root / "SkyOverlayPack"
        self.optifine  = self.pack_dir / "assets/minecraft/optifine/sky/world0"
        self.mcpatcher = self.pack_dir / "assets/minecraft/mcpatcher/sky/world0"
        ensure_dir(self.optifine)
        ensure_dir(self.mcpatcher)
        log(f"Pack directory: {self.pack_dir}")

    def save(self, img: Image.Image, name: str):
        for d in (self.optifine, self.mcpatcher):
            img.save(d / name, "PNG")
        log(f"  Saved {name}")

    def save_icon(self, img: Image.Image):
        img.save(self.pack_dir / "pack.png", "PNG")
        log("  Saved pack.png")

    def write_mcmeta(self):
        (self.pack_dir / "pack.mcmeta").write_text(
            json.dumps(PACK_MCMETA, indent=4), encoding="utf-8")
        log("Wrote pack.mcmeta")

    def write_all_props(self):
        for k in ALL_PROPERTY_KEYS:
            for d in (self.optifine, self.mcpatcher):
                write_props(d, k)
        log("Wrote all .properties files")

    def zip_pack(self) -> Path:
        zp = self.root / "SkyOverlayPack.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in self.pack_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(self.root))
        log(f"Created ZIP: {zp}")
        return zp


# ── Main SkyMaker ─────────────────────────────────────────────────────────────

class SkyMaker:
    def __init__(self, input_path: str, output_dir: str,
                 resolution: int = DEFAULT_RESOLUTION,
                 blend_px: int = None):
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"Invalid resolution. Choose from {VALID_RESOLUTIONS}")
        self.src      = input_path
        self.out      = Path(output_dir)
        self.res      = resolution
        # blend width = 8% of face resolution by default
        self.blend_px = blend_px if blend_px else max(16, resolution // 12)
        self.builder  = ResourcePackBuilder(self.out)

    def run(self) -> Path:
        log("=" * 55)
        log("SkyMaker — Minecraft 1.8.9 Sky Resource Pack Generator")
        log("=" * 55)

        # 1. Load source image
        img = load_image(self.src)

        # 2. If not a grid, make it one by tiling panoramically
        if not is_grid(img):
            log("Not a grid — converting panoramic to 3x2 grid...")
            img = panoramic_to_grid(img, self.res)
        else:
            log("Detected 3x2 grid layout.")

        # 3. Extract individual faces
        log(f"Extracting 6 faces at {self.res}x{self.res}px each...")
        faces = extract_faces(img, self.res)

        # 4. Blend seams between adjacent faces
        log(f"Blending seams ({self.blend_px}px blend width)...")
        faces = blend_all_seams(faces, self.blend_px)

        # 5. Reassemble into combined 3x2 grid (this is what 1.8.9 uses)
        log("Assembling final combined sky image...")
        combined = assemble_grid(faces, self.res)

        # 6. Save sky1.png = the main combined sky grid image
        log("Saving textures...")
        self.builder.save(combined, "sky1.png")

        # 7. Extra overlay textures
        self.builder.save(make_starfield(self.res), "starfield.png")
        self.builder.save(make_cloud(self.res),     "cloud1.png")

        # 8. Pack icon from front face
        log("Generating pack icon...")
        self.builder.save_icon(make_pack_icon(faces["front"]))

        # 9. Properties + mcmeta
        self.builder.write_all_props()
        self.builder.write_mcmeta()

        # 10. ZIP
        zp = self.builder.zip_pack()
        log("=" * 55)
        log("DONE! Drop SkyOverlayPack.zip into resourcepacks.")
        log("=" * 55)
        return zp


# ── Panoramic → grid converter (for non-grid inputs) ─────────────────────────

def _uv(res):
    t = np.linspace(1, -1, res, dtype=np.float32)
    s = np.linspace(-1, 1, res, dtype=np.float32)
    return np.meshgrid(s, t)

def _sample(arr, vecs, sw, sh):
    n   = np.linalg.norm(vecs, axis=-1, keepdims=True)
    v   = vecs / (n + 1e-9)
    x, y, z = v[...,0], v[...,1], v[...,2]
    lon = np.arctan2(x, z)
    lat = np.arcsin(np.clip(y, -1, 1))
    px  = np.clip(((lon/(2*math.pi)+0.5)*(sw-1)).astype(np.int32), 0, sw-1)
    py  = np.clip(((0.5-lat/math.pi)*(sh-1)).astype(np.int32), 0, sh-1)
    return arr[py, px]

def panoramic_to_grid(img: Image.Image, face_res: int) -> Image.Image:
    """Convert a single panoramic image into a 3x2 grid."""
    if img.size[0] < img.size[1] * 1.5:
        img = img.resize((img.size[1]*2, img.size[1]), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32)
    sw, sh = img.size
    u, v = _uv(face_res)
    one  = np.ones_like(u)
    dirs = {
        "front":  np.stack([ u,  v,  one], -1),
        "back":   np.stack([-u,  v, -one], -1),
        "left":   np.stack([-one, v,  u],  -1),
        "right":  np.stack([ one, v, -u],  -1),
        "top":    np.stack([ u,  one, -v], -1),
        "bottom": np.stack([ u, -one,  v], -1),
    }
    face_imgs = {}
    for name, vecs in dirs.items():
        data = _sample(arr, vecs, sw, sh)
        face_imgs[name] = Image.fromarray(data.astype(np.uint8), "RGBA")
    # assemble into grid and return
    grid = Image.new("RGBA", (face_res*3, face_res*2))
    layout = [("bottom",0,0),("top",1,0),("back",2,0),
              ("left",0,1),("front",1,1),("right",2,1)]
    for name, col, row in layout:
        grid.paste(face_imgs[name], (col*face_res, row*face_res))
    return grid


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Minecraft 1.8.9 sky resource pack generator")
    ap.add_argument("input_image")
    ap.add_argument("output_folder")
    ap.add_argument("--resolution", type=int, default=DEFAULT_RESOLUTION,
                    choices=VALID_RESOLUTIONS)
    ap.add_argument("--blend", type=int, default=None,
                    help="Seam blend width in pixels (default: resolution/12)")
    args = ap.parse_args()
    try:
        SkyMaker(args.input_image, args.output_folder,
                 args.resolution, args.blend).run()
    except Exception as e:
        print(f"[SkyMaker] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

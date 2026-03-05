"""
Basudev's Custom Sky Maker
Minecraft 1.8.9 Sky Resource Pack Generator
"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter import font as tkfont
import os, sys, math, threading, shutil, random, string, json, zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess

def _pip(pkg):
    subprocess.call([sys.executable,"-m","pip","install",pkg,"--quiet"],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:    from PIL import Image, ImageFilter, ImageDraw
except: _pip("pillow"); from PIL import Image, ImageFilter, ImageDraw
try:    import numpy as np
except: _pip("numpy");  import numpy as np

VERSION    = "3.0.0"

# ── Auto-generate START.bat if missing ───────────────────────────────────────
def _ensure_bat():
    bat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "START.bat")
    if not os.path.exists(bat_path):
        bat = (
            "@echo off\r\n"
            "setlocal EnableDelayedExpansion\r\n"
            "title Basudev's Custom Sky Maker\r\n"
            "color 0A\r\n"
            "cd /d \"%~dp0\"\r\n"
            "echo.\r\n"
            "echo  ============================================================\r\n"
            "echo    Basudev's Custom Sky Maker - Smart Launcher\r\n"
            "echo  ============================================================\r\n"
            "echo.\r\n"
            "echo  [1/4] Checking Python...\r\n"
            "python --version >nul 2>&1\r\n"
            "if errorlevel 1 (\r\n"
            "    echo  [!] Python is NOT installed.\r\n"
            "    set /p DLPY=\"  Download and install Python now? (yes/no): \"\r\n"
            "    if /i \"!DLPY!\"==\"yes\" (\r\n"
            "        echo  Downloading Python 3.11...\r\n"
            "        curl -L --progress-bar -o \"%TEMP%\\python_setup.exe\" \"https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe\"\r\n"
            "        if errorlevel 1 ( echo  Download failed. Get Python from python.org & pause & exit /b )\r\n"
            "        \"%TEMP%\\python_setup.exe\" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1\r\n"
            "        del \"%TEMP%\\python_setup.exe\" >nul 2>&1\r\n"
            "        echo  [OK] Python installed! Please close and re-open START.bat\r\n"
            "        pause & exit /b\r\n"
            "    ) else ( echo  Please install Python from python.org & pause & exit /b )\r\n"
            ")\r\n"
            "for /f \"tokens=*\" %%V in ('python --version 2^>^&1') do set PYVER=%%V\r\n"
            "echo  [OK] !PYVER!\r\n"
            "echo  [2/4] Checking pip...\r\n"
            "python -m pip --version >nul 2>&1\r\n"
            "if errorlevel 1 ( python -m ensurepip --upgrade >nul 2>&1 )\r\n"
            "echo  [OK] pip ready.\r\n"
            "echo  [3/4] Checking Pillow...\r\n"
            "python -c \"from PIL import Image\" >nul 2>&1\r\n"
            "if errorlevel 1 (\r\n"
            "    set /p ANS3=\"  [!] Pillow not found. Install? (yes/no): \"\r\n"
            "    if /i \"!ANS3!\"==\"yes\" ( python -m pip install pillow --quiet & echo  [OK] Installed. ) else ( pause & exit /b )\r\n"
            ") else ( echo  [OK] Pillow found. )\r\n"
            "echo  [4/4] Checking NumPy...\r\n"
            "python -c \"import numpy\" >nul 2>&1\r\n"
            "if errorlevel 1 (\r\n"
            "    set /p ANS4=\"  [!] NumPy not found. Install? (yes/no): \"\r\n"
            "    if /i \"!ANS4!\"==\"yes\" ( python -m pip install numpy --quiet & echo  [OK] Installed. ) else ( pause & exit /b )\r\n"
            ") else ( echo  [OK] NumPy found. )\r\n"
            "if not exist \"SkyMaker.pyw\" ( echo  [!] SkyMaker.pyw missing! & pause & exit /b )\r\n"
            "if not exist \"overlays\\\" ( echo  [!] overlays folder missing! & pause & exit /b )\r\n"
            "echo.\r\n"
            "echo  All good! Launching...\r\n"
            "echo.\r\n"
            "timeout /t 1 /nobreak >nul\r\n"
            "python \"SkyMaker.pyw\"\r\n"
            "if errorlevel 1 ( echo. & echo  [!] An error occurred. & pause )\r\n"
        )
        try:
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat)
        except Exception:
            pass

_ensure_bat()
FACE_SIZE  = 2048
FACE_NAMES = ['right','left','top','bottom','front','back']

# ── Cool adjectives for auto naming ──────────────────────────────────────────
COOL_ADJ = [
    "Mystic","Celestial","Eternal","Radiant","Vivid","Serene",
    "Cosmic","Ancient","Shimmering","Crimson","Azure","Golden",
    "Twilight","Astral","Frozen","Blazing","Silent","Hollow",
]

# ── Keyword → scene map ───────────────────────────────────────────────────────
KEYWORD_MAP = {
    "beach":"Ocean Sky","ocean":"Ocean Sky","sea":"Ocean Sky","coast":"Ocean Sky",
    "sunset":"Sunset Sky","dawn":"Sunrise Sky","sunrise":"Sunrise Sky","dusk":"Sunset Sky",
    "night":"Night Sky","star":"Night Sky","galaxy":"Galaxy Sky","space":"Galaxy Sky",
    "nebula":"Galaxy Sky","storm":"Storm Sky","cloud":"Cloudy Sky",
    "fire":"Fire Sky","volcano":"Fire Sky","forest":"Forest Sky",
    "snow":"Snow Sky","winter":"Snow Sky","desert":"Desert Sky","sand":"Desert Sky",
    "fantasy":"Fantasy Sky","magic":"Fantasy Sky","neon":"Neon Sky",
    "cyber":"Neon Sky","aurora":"Aurora Sky","pastel":"Pastel Sky",
}

# ── pack.mcmeta template (name injected at runtime) ──────────────────────────
# § Minecraft color codes for mcmeta description
MC_COLORS = {
    "black":"§0","dark_blue":"§1","dark_green":"§2","dark_aqua":"§3",
    "dark_red":"§4","dark_purple":"§5","gold":"§6","gray":"§7",
    "dark_gray":"§8","blue":"§9","green":"§a","aqua":"§b",
    "red":"§c","light_purple":"§d","yellow":"§e","white":"§f",
    "bold":"§l","italic":"§o","underline":"§n","strike":"§m","magic":"§k","reset":"§r",
}

# Scene → color code mapping for the pack name
SCENE_COLORS = {
    "Galaxy Sky":   "§5§l",   # dark purple + bold
    "Night Sky":    "§1§l",   # dark blue + bold
    "Sunset Sky":   "§6§l",   # gold + bold
    "Sunrise Sky":  "§e§l",   # yellow + bold
    "Fire Sky":     "§4§l",   # dark red + bold
    "Ocean Sky":    "§b§l",   # aqua + bold
    "Clear Sky":    "§9§l",   # blue + bold
    "Storm Sky":    "§8§l",   # dark gray + bold
    "Cloudy Sky":   "§7§l",   # gray + bold
    "Forest Sky":   "§2§l",   # dark green + bold
    "Pastel Sky":   "§d§l",   # light purple + bold
    "Neon Sky":     "§a§l",   # green + bold
    "Desert Sky":   "§6§o",   # gold + italic
    "Aurora Sky":   "§b§k§r§b§l",  # magic flash then aqua bold
    "Fantasy Sky":  "§d§k§r§5§l",  # magic flash then purple bold
    "Snow Sky":     "§f§l",   # white + bold
    "Custom Sky":   "§e§l",   # yellow + bold
}

def get_name_color(display_name: str) -> str:
    for scene, code in SCENE_COLORS.items():
        if scene.lower() in display_name.lower():
            return code
    return "§b§l"  # default aqua bold

def make_mcmeta(pack_display_name: str) -> dict:
    color_code = get_name_color(pack_display_name)
    # Build the § coded description string (works in 1.8.9)
    description = (
        f"§6✦ §r"
        f"{color_code}{pack_display_name}§r"
        f" §6✦\n"
        f"§7Made by §d§lBasudev§r"
    )
    return {
        "pack": {
            "pack_format": 1,
            "description": description
        }
    }

PROP = (
    "source=./{source}\nblend=replace\nrotate=false\nspeed=0.0\naxis=0.0 1.0 0.0\n"
    "startFadeIn={sfi}\nendFadeIn={efi}\nstartFadeOut={sfo}\nendFadeOut={efo}\n"
)
# Properties copied from a verified working 1.8.9 OptiFine sky pack
# sky3 uses blend=replace (daytime base sky — always visible day/night)
# others use blend=add for layered overlays (clouds, stars, sunflare)
# EXACT properties from verified working 1.8.9 OptiFine sky pack
# Only starfield.png and starfield01.png exist — used directly
SKY_PROPS_DATA = [
    ("sky1", "startFadeIn=18:00\nendFadeIn=18:45\nstartFadeOut=18:50\nendFadeOut=19:10\nblend=add\nrotate=true\naxis=0.0 -0.2 0.0\nsource=./cloud2.png\n"),
    ("sky2", "startFadeIn=4:45\nendFadeIn=5:10\nstartFadeOut=5:20\nendFadeOut=6:05\nblend=add\nrotate=true\naxis=0.0 -0.2 0.0\nsource=./cloud2.png\n"),
    ("sky3", "startFadeIn=5:30\nendFadeIn=6:00\nstartFadeOut=17:30\nendFadeOut=18:20\nblend=replace\nrotate=true\naxis=0.0 -0.2 0.0\nsource=./cloud1.png\n"),
    ("sky4", "startFadeIn=17:30\nendFadeIn=20:00\nendFadeOut=6:10\nblend=add\nrotate=true\nsource=./starfield01.png\n"),
    ("sky5", "startFadeIn=19:30\nendFadeIn=19:50\nendFadeOut=4:40\nblend=burn\nrotate=true\naxis=0.0 -0.2 0.0\nsource=./starfield.png\n"),
    ("sky6", "startFadeIn=18:30\nendFadeIn=18:45\nendFadeOut=5:25\nblend=add\nrotate=true\naxis=0.0 -0.2 0.0\nsource=./starfield01.png\n"),
    ("sky7", "startFadeIn=17:50\nendFadeIn=18:30\nendFadeOut=19:20\nblend=add\nrotate=true\nsource=./sky_sunflare.png\n"),
    ("sky8", "startFadeIn=4:40\nendFadeIn=5:00\nendFadeOut=5:50\nblend=add\nrotate=true\nsource=./sky_sunflare.png\n"),
]

# ── Scene detection ───────────────────────────────────────────────────────────
def detect_scene(img: Image.Image) -> str:
    small = img.convert("RGB").resize((64,64), Image.LANCZOS)
    arr   = np.array(small, dtype=np.float32)
    r,g,b = arr[:,:,0].mean(), arr[:,:,1].mean(), arr[:,:,2].mean()
    brightness = (r+g+b)/3
    r_dom = r/(g+b+1); b_dom = b/(r+g+1); g_dom = g/(r+b+1)
    mx=arr.max(axis=2); mn=arr.min(axis=2)
    sat = ((mx-mn)/(mx+1)).mean()
    top = arr[:32,:,:].mean(); bot = arr[32:,:,:].mean()
    if brightness < 40:   return "Galaxy Sky" if b_dom>0.55 else "Night Sky"
    if brightness < 80:
        if r_dom>0.55:    return "Storm Sky"
        if b_dom>0.55:    return "Galaxy Sky"
        if sat>0.4:       return "Fantasy Sky"
        return "Night Sky"
    if r>180 and g>120 and b<100: return "Sunset Sky"
    if r>160 and g>140 and b<120: return "Sunrise Sky"
    if r>200 and g>150 and b<80:  return "Fire Sky"
    if b>r+30 and b>g+20:  return "Clear Sky" if brightness>160 else "Ocean Sky"
    if sat<0.15: return "Cloudy Sky" if brightness>180 else "Storm Sky"
    if g_dom>0.45 and brightness>100: return "Forest Sky"
    if r>180 and g>160 and b>160:     return "Pastel Sky"
    if sat>0.5 and brightness<120:    return "Neon Sky"
    if top>bot+40:                    return "Desert Sky"
    return "Fantasy Sky"

def auto_name(pano_path: str) -> str:
    """Detect scene from filename keywords, then colour analysis."""
    fname = os.path.splitext(os.path.basename(pano_path))[0].lower()
    scene = None
    for kw, sname in KEYWORD_MAP.items():
        if kw in fname:
            scene = sname; break
    if not scene:
        try:    scene = detect_scene(Image.open(pano_path))
        except: scene = "Custom Sky"
    adj = COOL_ADJ[abs(hash(fname+scene)) % len(COOL_ADJ)]
    return f"{adj} {scene}"

def safe_filename(name: str) -> str:
    """Convert display name to safe filename (no special chars)."""
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"
    return "".join(c for c in name if c in keep).strip().replace(" ","_")[:50]

def upscale_image(input_path, output_path, scale, method, log_cb):
    """Upscale image using high-quality Lanczos/bicubic resampling."""
    img = Image.open(input_path).convert("RGB")
    ow, oh = img.size
    nw, nh = int(ow * scale), int(oh * scale)
    log_cb(f"  Input:  {ow}x{oh}px")
    log_cb(f"  Output: {nw}x{nh}px  ({scale}x {method})")
    resample = {
        "Lanczos (Best)":   Image.LANCZOS,
        "Bicubic (Smooth)": Image.BICUBIC,
        "Nearest (Pixel)":  Image.NEAREST,
    }.get(method, Image.LANCZOS)
    out = img.resize((nw, nh), resample)
    # Sharpen slightly for Lanczos to bring back crisp edges
    if "Lanczos" in method:
        arr = np.array(out, dtype=np.float32)
        kernel = np.array([[-0.1,-0.1,-0.1],
                           [-0.1, 1.8,-0.1],
                           [-0.1,-0.1,-0.1]])
        from PIL import ImageFilter
        out = out.filter(ImageFilter.SHARPEN)
    out.save(output_path, "PNG")
    log_cb(f"  Saved → {output_path}")
    return nw, nh

def get_next_sky_number(d: str) -> int:
    if not os.path.exists(d): return 1
    nums = []
    for item in os.listdir(d):
        base = os.path.splitext(item)[0]
        if base.startswith("Sky") and base[3:].isdigit():
            nums.append(int(base[3:]))
    return max(nums)+1 if nums else 1

def rand_name(n=6):
    return ''.join(random.choices(string.ascii_letters+string.digits, k=n))

# ── Core image processing (original logic preserved) ─────────────────────────
def vector_to_uv_vec(x,y,z):
    lon=np.arctan2(z,x); lat=np.arcsin(np.clip(y,-1.0,1.0))
    return (lon/np.pi+1)/2, 0.5-lat/np.pi

def generate_face(pano_img, face_name):
    pano_array=np.array(pano_img); p_height,p_width=pano_array.shape[:2]
    indices=np.linspace(0,FACE_SIZE-1,FACE_SIZE)
    x_idx,y_idx=np.meshgrid(indices,indices)
    u_vals=2*(x_idx+0.5)/FACE_SIZE-1; v_vals=2*(y_idx+0.5)/FACE_SIZE-1
    if   face_name=='right':  vec=(np.ones_like(u_vals), -v_vals,-u_vals)
    elif face_name=='left':   vec=(-np.ones_like(u_vals),-v_vals, u_vals)
    elif face_name=='top':    vec=(u_vals, np.ones_like(u_vals),  v_vals)
    elif face_name=='bottom': vec=(u_vals,-np.ones_like(u_vals), -v_vals)
    elif face_name=='front':  vec=(u_vals,-v_vals, np.ones_like(u_vals))
    elif face_name=='back':   vec=(-u_vals,-v_vals,-np.ones_like(u_vals))
    mag=np.sqrt(vec[0]**2+vec[1]**2+vec[2]**2)
    u,v=vector_to_uv_vec(vec[0]/mag,vec[1]/mag,vec[2]/mag)
    px=(u*p_width).astype(np.int32)%p_width
    py=(v*p_height).astype(np.int32)%p_height
    return Image.fromarray(pano_array[py,px].astype(np.uint8))

def advanced_blend(img,blend_width,blend_mode='cosine'):
    width=img.size[0]; mid=width//2
    blend_width=min(blend_width,mid)
    arr=np.array(img,dtype=np.float32); mirrored=np.fliplr(arr[:,:mid])
    for x in range(blend_width):
        t=x/blend_width
        alpha=(1+math.cos(t*math.pi))/2 if blend_mode=='cosine' else 1-t
        pos=mid+x
        if pos<width: arr[:,pos]=alpha*mirrored[:,x]+(1-alpha)*arr[:,pos]
    return Image.fromarray(arr.astype(np.uint8))

def combine_faces(output_path,faces_dir):
    ts=FACE_SIZE; out=Image.new("RGB",(ts*3,ts*2))
    layout={'down':(0,0),'up':(ts,0),'east':(ts*2,0),
            'north':(0,ts),'west':(ts,ts),'south':(ts*2,ts)}
    for name,(x,y) in layout.items():
        fp=os.path.join(faces_dir,f"{name}.png")
        if os.path.exists(fp): out.paste(Image.open(fp).convert("RGB"),(x,y))
    out.save(output_path)

def process_face(face_name,pano_img,blend_width,blend_mode,out_dir,name_map):
    img=generate_face(pano_img,face_name)
    if face_name=='top':    img=img.rotate(90, expand=True)
    if face_name=='bottom': img=img.rotate(-90,expand=True)
    if face_name in ('top','bottom','left'):
        img=advanced_blend(img,blend_width,blend_mode)
    img.save(os.path.join(out_dir,f"{name_map[face_name]}.png"))
    return face_name

def make_starfield(size=512):
    img=Image.new("RGBA",(size,size),(0,0,0,0))
    draw=ImageDraw.Draw(img); rng=random.Random(99)
    for _ in range(3000):
        x,y=rng.randint(0,size-1),rng.randint(0,size-1)
        br=rng.randint(160,255); sz=rng.choices([0,1],weights=[80,20])[0]
        c=(br,br,br,br)
        if sz==0: draw.point((x,y),fill=c)
        else:     draw.ellipse((x-1,y-1,x+1,y+1),fill=c)
    return img.filter(ImageFilter.GaussianBlur(0.5))

def make_sunflare(size=64):
    img=Image.new("RGBA",(size,size),(0,0,0,0))
    draw=ImageDraw.Draw(img); cx,cy=size//2,size//2
    for r in range(cx,0,-1):
        alpha=int(200*(r/cx)**2)
        draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,220,80,255-alpha))
    return img

def write_properties(dest_dir):
    for key, content in SKY_PROPS_DATA:
        (Path(dest_dir)/f"{key}.properties").write_text(content, encoding="utf-8")

def get_resource_path(rel):
    try:    base=sys._MEIPASS
    except: base=os.path.abspath(".")
    return os.path.join(base,rel)

# ── Main process ──────────────────────────────────────────────────────────────
def main_process(pano_path, blend_width, blend_mode, progress_cb, log_cb,
                 output_dir=None, face_size=2048, custom_name=None, brightness=1.0):
    global FACE_SIZE
    FACE_SIZE   = face_size
    pano_dir    = os.path.dirname(os.path.abspath(pano_path))
    out_root    = output_dir if output_dir else os.path.join(pano_dir,"allSkys")
    os.makedirs(out_root, exist_ok=True)

    # ── Determine final display name ─────────────────────────────────────────
    if custom_name and custom_name.strip():
        display_name = custom_name.strip()
        log_cb(f"✏️  Using custom name: {display_name}")
    else:
        display_name = auto_name(pano_path)
        log_cb(f"🤖 Auto-detected name: {display_name}")

    # ── Unique numbered folder + ZIP name ────────────────────────────────────
    sky_num     = get_next_sky_number(out_root)
    safe_name   = safe_filename(display_name)
    folder_name = f"Sky{sky_num}_{safe_name}"
    final_dir   = os.path.join(out_root, folder_name)
    temp_dir    = os.path.join(pano_dir, f"_tmp_{rand_name()}")
    os.makedirs(temp_dir, exist_ok=True)
    log_cb(f"📦 Pack folder: {folder_name}")

    # ── Load + generate faces ────────────────────────────────────────────────
    log_cb("Loading panorama…")
    pano_img = Image.open(pano_path).convert('RGB')
    name_map = {'right':'east','left':'west','top':'up',
                'bottom':'down','front':'south','back':'north'}

    log_cb("Generating 6 cube faces (parallel)…")
    completed = 0
    with ThreadPoolExecutor() as ex:
        futures = [ex.submit(process_face,f,pano_img,blend_width,
                             blend_mode,temp_dir,name_map) for f in FACE_NAMES]
        for fut in futures:
            done = fut.result(); completed += 1
            log_cb(f"  ✓ Face '{done}'")
            progress_cb(int(completed/(len(FACE_NAMES)+3)*100))

    log_cb("Combining faces into 3×2 grid…")
    sky_result = os.path.join(temp_dir,"sky_result.png")
    combine_faces(sky_result,temp_dir)
    # Brightness at 100% — no darkening applied
    progress_cb(75)

    log_cb("Overlay textures ready (from bundled overlays folder)…")

    os.makedirs(final_dir, exist_ok=True)

    # ── pack.mcmeta — name matches display_name ───────────────────────────────
    with open(os.path.join(final_dir,"pack.mcmeta"),"w",encoding="utf-8") as f:
        json.dump(make_mcmeta(display_name), f, indent=2, ensure_ascii=False)
    log_cb(f"  ✓ pack.mcmeta  →  \"{display_name}\"")

    # ── pack.png — centre face of the sky grid ────────────────────────────────
    sky_img = Image.open(sky_result).convert("RGB")
    sw,sh   = sky_img.size
    cw,ch   = sw//3, sh//2
    crop    = sky_img.crop((cw, 0, cw*2, ch))   # top-centre = TOP face
    crop.thumbnail((128,128), Image.Resampling.LANCZOS)
    crop.save(os.path.join(final_dir,"pack.png"))
    log_cb("  ✓ pack.png  →  sky centre face")

    # ── Place files into both optifine + mcpatcher ────────────────────────────
    # ── Build slot_files ──────────────────────────────────────────────────────
    # Generated sky → used for ALL files except starfield01.png
    # starfield01.png → always the real bundled clean stars texture
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    overlays_dir = os.path.join(script_dir, "overlays")
    starfield01_src = os.path.join(overlays_dir, "starfield01.png")

    slot_files = {
        "cloud1.png":       sky_result,   # main daytime sky (sky3 source)
        "cloud2.png":       sky_result,   # dawn/dusk overlay
        "sky_sunflare.png": sky_result,   # sunflare layer
        "skybox.png":       sky_result,   # skybox
        "skybox2.png":      sky_result,   # skybox2
        "starfield.png":    sky_result,   # night star/fire layer
        # starfield01 stays as the real bundled clean stars — never replaced
        "starfield01.png":  starfield01_src if os.path.exists(starfield01_src) else sky_result,
    }
    for loader in ("mcpatcher","optifine"):
        world0 = os.path.join(final_dir,"assets","minecraft",loader,"sky","world0")
        os.makedirs(world0, exist_ok=True)
        for fname,src in slot_files.items():
            shutil.copy(src, os.path.join(world0,fname))
        write_properties(world0)

    shutil.rmtree(temp_dir, ignore_errors=True)
    progress_cb(92)

    # ── ZIP — name matches display_name exactly ───────────────────────────────
    # § color code prefix on zip filename (e.g. §bCelestial_Ocean_Sky.zip)
    color_code  = get_name_color(display_name)
    # Strip § codes to a single leading code for filename (keep first 2 chars §X)
    mc_prefix   = color_code[:2] if color_code else "§b"
    zip_name    = f"{mc_prefix}{safe_name}.zip"
    zip_path    = os.path.join(out_root, zip_name)
    if os.path.exists(zip_path):
        zip_path = os.path.join(out_root, f"{mc_prefix}{safe_name}_{sky_num}.zip")
    log_cb(f"Creating ZIP: {os.path.basename(zip_path)} …")
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as zf:
        for fp in Path(final_dir).rglob("*"):
            if fp.is_file(): zf.write(fp, fp.relative_to(final_dir))
    shutil.rmtree(final_dir, ignore_errors=True)
    progress_cb(100)
    log_cb(f"✅ Done  →  {zip_path}")
    return zip_path


# ── GUI ───────────────────────────────────────────────────────────────────────
BG   = "#0f0f1a"; BG2  = "#1a1a2e"; CARD = "#16213e"
ACC  = "#0f3460"; BLU  = "#1a4a8a"; GRN  = "#4ecca3"
YEL  = "#f5c842"; FG   = "#e8e8f0"; DIM  = "#6a6a8a"; ENT  = "#0a0a15"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Basudev's Custom Sky Maker")
        self.configure(bg=BG)
        self.resizable(False,False)
        self.selected_files = []
        self._build()
        self._center()
        self.after(200, self._init_dnd)

    def _build(self):
        F  = ("Segoe UI",10); FB = ("Segoe UI",10,"bold")
        FT = ("Segoe UI",15,"bold"); FS = ("Segoe UI",9)
        FC = ("Consolas",9);  FW = ("Segoe UI",11,"bold")

        # ── Banner ────────────────────────────────────────────────────────────
        banner = tk.Frame(self, bg=ACC, pady=0)
        banner.pack(fill="x")
        lb = tk.Frame(banner, bg=ACC)
        lb.pack(side="left", fill="both", expand=True, padx=18, pady=12)
        tk.Label(lb, text="☁  Basudev's Custom Sky Maker",
                 font=FT, bg=ACC, fg=GRN).pack(anchor="w")
        tk.Label(lb, text="Minecraft 1.8.9  ·  OptiFine  ·  MCPatcher  |  Panorama → Sky Pack",
                 font=FS, bg=ACC, fg="#a0b0c8").pack(anchor="w")
        tk.Label(banner, text="Made by Basudev",
                 font=("Segoe UI",9,"italic"), bg=ACC, fg=YEL
                 ).pack(side="right", padx=18)

        # ── Notebook tabs ─────────────────────────────────────────────────────
        style = ttk.Style()
        style.configure("Dark.TNotebook",           background=BG, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",       background=ACC, foreground=FG,
                        padding=[14,6], font=FB)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", GRN)],
                  foreground=[("selected", BG)])
        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        body = tk.Frame(nb, bg=BG, padx=18, pady=12)
        nb.add(body, text="  ⛅  Sky Maker  ")

        up_tab = tk.Frame(nb, bg=BG, padx=18, pady=12)
        nb.add(up_tab, text="  🔍  Upscaler  ")
        self._build_upscaler(up_tab)

        # ── Drop zone ─────────────────────────────────────────────────────────
        drop_outer = tk.Frame(body, bg=GRN, padx=2, pady=2)
        drop_outer.pack(fill="x", pady=(0,12))
        self.drop_frame = tk.Frame(drop_outer, bg=CARD, pady=18, cursor="hand2")
        self.drop_frame.pack(fill="x")
        self.drop_icon  = tk.Label(self.drop_frame, text="📂",
                                   font=("Segoe UI",26), bg=CARD, fg=GRN)
        self.drop_icon.pack()
        self.drop_label = tk.Label(self.drop_frame,
                                   text="Drop panoramic images here  or  click to browse",
                                   font=F, bg=CARD, fg=DIM, justify="center")
        self.drop_label.pack()
        self.file_count = tk.Label(self.drop_frame, text="", font=FB, bg=CARD, fg=GRN)
        self.file_count.pack()
        for w in (self.drop_frame, self.drop_icon, self.drop_label, self.file_count):
            w.bind("<Button-1>", lambda e: self._browse())

        # ── Pack Name row ─────────────────────────────────────────────────────
        name_row = tk.Frame(body, bg=BG)
        name_row.pack(fill="x", pady=(0,6))
        tk.Label(name_row, text="Pack Name", font=FB, bg=BG, fg=FG,
                 width=13, anchor="w").pack(side="left")
        self.name_var   = tk.StringVar(value="")
        self.name_entry = tk.Entry(name_row, textvariable=self.name_var,
                                   bg=ENT, fg=GRN, insertbackground=GRN,
                                   relief="flat", font=("Segoe UI",10), width=34)
        self.name_entry.pack(side="left", padx=(4,6), ipady=5)
        tk.Button(name_row, text="✕", font=F, bg="#1a0a2e", fg=DIM,
                  relief="flat", cursor="hand2", padx=6, pady=3,
                  command=lambda: [self.name_var.set(""),
                                   self.name_hint.config(text="✨ leave empty → auto-detect", fg=DIM)]
                  ).pack(side="left", padx=(0,6))
        self.name_hint = tk.Label(name_row,
                                  text="✨ leave empty → auto-detect from image",
                                  font=("Segoe UI",8,"italic"), bg=BG, fg=DIM)
        self.name_hint.pack(side="left")

        # ── Output folder row ─────────────────────────────────────────────────
        out_row = tk.Frame(body, bg=BG)
        out_row.pack(fill="x", pady=(0,6))
        tk.Label(out_row, text="Output Folder", font=FB, bg=BG, fg=FG,
                 width=13, anchor="w").pack(side="left")
        self.out_var = tk.StringVar(value="(same folder as input image)")
        tk.Entry(out_row, textvariable=self.out_var, bg=ENT, fg=FG,
                 insertbackground=FG, relief="flat", font=F, width=34
                 ).pack(side="left", padx=(4,6), ipady=5)
        tk.Button(out_row, text="Browse", font=F, bg=ACC, fg=FG,
                  relief="flat", cursor="hand2", padx=10, pady=3,
                  command=self._pick_output).pack(side="left", padx=(0,4))
        tk.Button(out_row, text="✕", font=F, bg="#1a0a2e", fg=DIM,
                  relief="flat", cursor="hand2", padx=6, pady=3,
                  command=lambda: self.out_var.set("(same folder as input image)")
                  ).pack(side="left")

        # ── Settings row: blend + resolution ─────────────────────────────────
        settings = tk.Frame(body, bg=BG)
        settings.pack(fill="x", pady=(0,10))

        ls = tk.Frame(settings, bg=BG); ls.pack(side="left", padx=(0,18))
        tk.Label(ls, text="Blend Mode", font=FB, bg=BG, fg=FG).pack(anchor="w")
        self.blend_mode_var = tk.StringVar(value="Cosine (Recommended)")
        ttk.Combobox(ls, textvariable=self.blend_mode_var,
                     values=["Cosine (Recommended)","Linear (old)"],
                     state="readonly", width=20, font=F).pack(anchor="w", pady=2)

        ms = tk.Frame(settings, bg=BG); ms.pack(side="left", padx=(0,18))
        tk.Label(ms, text="Blend Width (px)", font=FB, bg=BG, fg=FG).pack(anchor="w")
        self.blend_width_var = tk.StringVar(value="500")
        ttk.Combobox(ms, textvariable=self.blend_width_var,
                     values=[str(i) for i in range(200,1001,50)],
                     state="readonly", width=9, font=F).pack(anchor="w", pady=2)

        rs = tk.Frame(settings, bg=BG); rs.pack(side="left")
        tk.Label(rs, text="Face Resolution", font=FB, bg=BG, fg=FG).pack(anchor="w")
        self.resolution_var = tk.StringVar(value="2048")
        rf = tk.Frame(rs, bg=BG); rf.pack(anchor="w", pady=2)
        for res,tip in [("512","Fast"),("1024","Good"),("2048","Best"),("4096","Ultra")]:
            tk.Radiobutton(rf, text=f"{res}\n({tip})", variable=self.resolution_var,
                           value=res, bg=BG, fg=FG, selectcolor=GRN,
                           activebackground=BG, activeforeground=GRN,
                           font=("Segoe UI",8), justify="center",
                           indicatoron=0, relief="flat", padx=8, pady=4,
                           cursor="hand2").pack(side="left", padx=2)

        # ── Generate button ───────────────────────────────────────────────────
        self.gen_btn = tk.Button(body, text="🚀  Create Sky Pack",
                                 font=FW, bg=GRN, fg=BG,
                                 activebackground="#7fffd4",
                                 relief="flat", cursor="hand2",
                                 padx=28, pady=11, command=self._run)
        self.gen_btn.pack(pady=(4,8))

        # ── Progress ──────────────────────────────────────────────────────────
        pf = tk.Frame(body, bg=BG); pf.pack(fill="x")
        self.prog_label = tk.Label(pf, text="", font=FS, bg=BG, fg=DIM)
        self.prog_label.pack(anchor="w")
        self.progress = ttk.Progressbar(pf, length=460,
                                        mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(2,8))

        # ── Log ───────────────────────────────────────────────────────────────
        tk.Label(body, text="Log", font=FB, bg=BG, fg=DIM,
                 anchor="w").pack(anchor="w")
        lf = tk.Frame(body, bg=BG); lf.pack(fill="x")
        self.log_box = tk.Text(lf, width=62, height=9, bg=ENT, fg=GRN,
                               font=FC, relief="flat", state="disabled", wrap="word")
        sb = tk.Scrollbar(lf, command=self.log_box.yview, bg=ACC)
        self.log_box.configure(yscrollcommand=sb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="Ready  —  select or drop panoramic images")
        tk.Label(self, textvariable=self.status_var, font=FS,
                 bg=BG2, fg=DIM, anchor="w").pack(fill="x", ipady=4)
        tk.Label(self, text=f"Basudev's Custom Sky Maker  v{VERSION}",
                 font=("Segoe UI",8), bg=BG, fg="#333355").pack(pady=(0,4))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _build_upscaler(self, parent):
        F  = ("Segoe UI",10); FB = ("Segoe UI",10,"bold")
        FS = ("Segoe UI",9);  FC = ("Consolas",9)
        FW = ("Segoe UI",11,"bold")

        # Drop zone
        uouter = tk.Frame(parent, bg=GRN, padx=2, pady=2)
        uouter.pack(fill="x", pady=(0,12))
        self.up_frame = tk.Frame(uouter, bg=CARD, pady=18, cursor="hand2")
        self.up_frame.pack(fill="x")
        self.up_icon  = tk.Label(self.up_frame, text="🖼️",
                                 font=("Segoe UI",26), bg=CARD, fg=GRN)
        self.up_icon.pack()
        self.up_label = tk.Label(self.up_frame,
                                 text="Drop image here  or  click to browse",
                                 font=F, bg=CARD, fg=DIM, justify="center")
        self.up_label.pack()
        self.up_count = tk.Label(self.up_frame, text="", font=FB, bg=CARD, fg=GRN)
        self.up_count.pack()
        for w in (self.up_frame, self.up_icon, self.up_label, self.up_count):
            w.bind("<Button-1>", lambda e: self._browse_upscale())
        self.up_files = []

        # Settings row
        sr = tk.Frame(parent, bg=BG); sr.pack(fill="x", pady=(0,8))

        # Scale
        sc = tk.Frame(sr, bg=BG); sc.pack(side="left", padx=(0,20))
        tk.Label(sc, text="Scale", font=FB, bg=BG, fg=FG).pack(anchor="w")
        self.up_scale_var = tk.StringVar(value="2x")
        for val in ["1.5x","2x","3x","4x"]:
            tk.Radiobutton(sc, text=val, variable=self.up_scale_var, value=val,
                           bg=BG, fg=FG, selectcolor=GRN,
                           activebackground=BG, font=F,
                           indicatoron=0, relief="flat", padx=10, pady=4,
                           cursor="hand2").pack(side="left", padx=2)

        # Method
        mc = tk.Frame(sr, bg=BG); mc.pack(side="left", padx=(0,20))
        tk.Label(mc, text="Method", font=FB, bg=BG, fg=FG).pack(anchor="w")
        self.up_method_var = tk.StringVar(value="Lanczos (Best)")
        ttk.Combobox(mc, textvariable=self.up_method_var,
                     values=["Lanczos (Best)","Bicubic (Smooth)","Nearest (Pixel)"],
                     state="readonly", width=18, font=F).pack(anchor="w", pady=2)

        # Output folder
        oc = tk.Frame(parent, bg=BG); oc.pack(fill="x", pady=(0,8))
        tk.Label(oc, text="Save To", font=FB, bg=BG, fg=FG,
                 width=8, anchor="w").pack(side="left")
        self.up_out_var = tk.StringVar(value="(same folder as input)")
        tk.Entry(oc, textvariable=self.up_out_var, bg=ENT, fg=FG,
                 insertbackground=FG, relief="flat", font=F, width=38
                 ).pack(side="left", padx=(4,6), ipady=4)
        tk.Button(oc, text="Browse", font=F, bg=ACC, fg=FG,
                  relief="flat", cursor="hand2", padx=10, pady=3,
                  command=self._pick_up_output).pack(side="left")

        # Upscale button
        self.up_btn = tk.Button(parent, text="🔍  Upscale Image",
                                font=FW, bg=GRN, fg=BG,
                                activebackground="#7fffd4",
                                relief="flat", cursor="hand2",
                                padx=28, pady=11, command=self._run_upscale)
        self.up_btn.pack(pady=(4,8))

        # Progress
        upf = tk.Frame(parent, bg=BG); upf.pack(fill="x")
        self.up_prog_label = tk.Label(upf, text="", font=FS, bg=BG, fg=DIM)
        self.up_prog_label.pack(anchor="w")
        self.up_progress = ttk.Progressbar(upf, length=460,
                                           mode="determinate", maximum=100)
        self.up_progress.pack(fill="x", pady=(2,8))

        # Log
        tk.Label(parent, text="Log", font=FB, bg=BG, fg=DIM,
                 anchor="w").pack(anchor="w")
        lf2 = tk.Frame(parent, bg=BG); lf2.pack(fill="x")
        self.up_log = tk.Text(lf2, width=62, height=7, bg=ENT, fg=GRN,
                              font=FC, relief="flat", state="disabled", wrap="word")
        sb2 = tk.Scrollbar(lf2, command=self.up_log.yview, bg=ACC)
        self.up_log.configure(yscrollcommand=sb2.set)
        self.up_log.pack(side="left", fill="both", expand=True)
        sb2.pack(side="right", fill="y")

    def _browse_upscale(self):
        files = filedialog.askopenfilenames(
            title="Select images to upscale",
            filetypes=[("Images","*.jpg *.jpeg *.png *.bmp *.tiff"),("All","*.*")])
        if files:
            self.up_files = [os.path.abspath(f) for f in files]
            n = len(self.up_files)
            names = ", ".join(os.path.basename(f) for f in self.up_files[:3])
            if n > 3: names += f"  +{n-3} more"
            self.up_label.config(text=names, fg=FG)
            self.up_count.config(text=f"{n} image{'s' if n>1 else ''} selected ✓")
            self.up_icon.config(text="✅")
            self._up_log(f"Loaded {n} file(s): {names}")

    def _pick_up_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.up_out_var.set(p)

    def _up_log(self, msg):
        self.up_log.configure(state="normal")
        self.up_log.insert("end", msg+"\n")
        self.up_log.see("end")
        self.up_log.configure(state="disabled")
        self.update_idletasks()

    def _run_upscale(self):
        if not self.up_files:
            messagebox.showwarning("No images","Please select images to upscale.")
            return
        scale_str = self.up_scale_var.get().replace("x","")
        scale     = float(scale_str)
        method    = self.up_method_var.get()
        out_val   = self.up_out_var.get().strip()

        self.up_btn.configure(state="disabled")
        self.up_progress.configure(value=0)
        self.up_log.configure(state="normal"); self.up_log.delete("1.0","end")
        self.up_log.configure(state="disabled")

        def task():
            total = len(self.up_files); done = []
            for i, path in enumerate(self.up_files):
                fname  = os.path.basename(path)
                src_dir = os.path.dirname(path)
                out_dir = out_val if not out_val.startswith("(same") else src_dir
                os.makedirs(out_dir, exist_ok=True)
                base, ext = os.path.splitext(fname)
                out_path = os.path.join(out_dir, f"{base}_{int(scale)}x.png")
                self.after(0, lambda n=fname: self._up_log(f"\n── {n} ──"))
                self.after(0, lambda: self.up_prog_label.config(
                    text=f"Upscaling {i+1}/{total}…", fg=DIM))
                try:
                    nw, nh = upscale_image(path, out_path, scale, method,
                                           lambda m: self.after(0, lambda msg=m: self._up_log(msg)))
                    done.append(out_path)
                    self.after(0, lambda: self.up_progress.configure(
                        value=int((i+1)/total*100)))
                except Exception as e:
                    self.after(0, lambda err=str(e): self._up_log(f"❌ {err}"))

            self.after(0, lambda: self.up_btn.configure(state="normal"))
            self.after(0, lambda: self.up_progress.configure(value=100))
            self.after(0, lambda: self.up_prog_label.config(
                text=f"Done! {len(done)}/{total} upscaled.", fg=GRN))
            if done:
                out_dir2 = os.path.dirname(done[0])
                self.after(0, lambda: messagebox.askyesno(
                    "Done! 🎉",
                    f"{len(done)} image(s) upscaled!\n\nOpen output folder?") and
                    os.startfile(out_dir2))

        threading.Thread(target=task, daemon=True).start()

    def _center(self):
        self.update_idletasks()
        w,h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

    def _init_dnd(self):
        try:
            import windnd
            def on_drop(files):
                try:
                    dec=[f.decode('utf-8') if isinstance(f,bytes) else f for f in files]
                    self.after(10, lambda: self._set_files(dec))
                except: pass
            windnd.hook_dropfiles(self, func=on_drop)
            self._log("Drag & drop ready ✓")
        except ImportError:
            self._log("Tip: pip install windnd  for drag & drop support")
        except Exception as e:
            self._log(f"DnD: {e}")

    def _pick_output(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.out_var.set(p)

    def _browse(self):
        files = filedialog.askopenfilenames(
            title="Select panoramic sky images",
            filetypes=[("Images","*.jpg *.jpeg *.png"),("All","*.*")])
        if files: self._set_files(list(files))

    def _set_files(self, files):
        self.selected_files = [os.path.abspath(f) for f in files if os.path.isfile(f)]
        n = len(self.selected_files)
        if n == 0: return
        names = ", ".join(os.path.basename(f) for f in self.selected_files[:3])
        if n > 3: names += f"  +{n-3} more"
        self.drop_label.config(text=names, fg=FG)
        self.file_count.config(text=f"{n} image{'s' if n>1 else ''} selected ✓")
        self.drop_icon.config(text="✅")
        self.status_var.set(f"{n} image(s) loaded — ready to create")
        self._log(f"Loaded {n} file(s): {names}")

        # Auto-fill name for single image (background thread so GUI stays fast)
        if n == 1 and not self.name_var.get().strip():
            def _autofill():
                try:
                    suggested = auto_name(self.selected_files[0])
                    self.after(0, lambda: self.name_var.set(suggested))
                    self.after(0, lambda: self.name_hint.config(
                        text=f"🎨 auto-detected  (you can edit this)", fg=GRN))
                    self.after(0, lambda: self._log(f"🤖 Suggested name: {suggested}"))
                except: pass
            threading.Thread(target=_autofill, daemon=True).start()

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg+"\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    def _set_progress(self, val):
        self.after(0, lambda: self.progress.configure(value=val))

    def _set_status(self, txt):
        self.after(0, lambda: self.status_var.set(txt))
        self.after(0, lambda: self.prog_label.config(text=txt, fg=DIM))

    def _run(self):
        if not self.selected_files:
            messagebox.showwarning("No images","Please select at least one panoramic image.")
            return
        blend_width  = int(self.blend_width_var.get())
        blend_mode   = "cosine" if "Cosine" in self.blend_mode_var.get() else "linear"
        face_size    = int(self.resolution_var.get())
        out_val      = self.out_var.get().strip()
        chosen_out   = None if out_val.startswith("(same") else out_val
        custom_name  = self.name_var.get().strip() or None

        self.gen_btn.configure(state="disabled")
        self.progress.configure(value=0)
        self.log_box.configure(state="normal"); self.log_box.delete("1.0","end")
        self.log_box.configure(state="disabled")

        def task():
            total=len(self.selected_files); results=[]
            for i,path in enumerate(self.selected_files):
                fname = os.path.basename(path)
                # For multiple files with no custom name, auto-detect per file
                per_name = custom_name
                self._set_status(f"Processing {i+1}/{total}: {fname}")
                self.after(0, lambda n=fname: self._log(f"\n── {n} ──"))
                try:
                    zp = main_process(path, blend_width, blend_mode,
                                      self._set_progress,
                                      lambda m: self.after(0,lambda msg=m: self._log(msg)),
                                      output_dir=chosen_out,
                                      face_size=face_size,
                                      custom_name=per_name,
                                      brightness=1.0)
                    results.append(zp)
                except Exception as e:
                    self.after(0,lambda err=str(e): self._log(f"❌ Error: {err}"))
                    self.after(0,lambda err=str(e),n=fname:
                               messagebox.showerror("Error",f"Failed: {n}\n{err}"))

            self._set_status(f"Done!  {len(results)}/{total} pack(s) created.")
            self.after(0,lambda: self.gen_btn.configure(state="normal"))
            self.after(0,lambda: self.progress.configure(value=100))
            if results:
                self.after(0,lambda: self._finish(results,os.path.dirname(results[0])))

        threading.Thread(target=task, daemon=True).start()

    def _finish(self, results, out_dir):
        names = "\n".join(os.path.basename(r) for r in results)
        if messagebox.askyesno("Done! 🎉",
            f"{len(results)} pack(s) created:\n\n{names}\n\nOpen output folder?"):
            os.startfile(out_dir)

if __name__ == "__main__":
    App().mainloop()

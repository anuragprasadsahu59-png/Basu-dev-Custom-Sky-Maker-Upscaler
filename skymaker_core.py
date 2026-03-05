import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import numpy as np
import math
import os
import threading
import time
import shutil
import random
import string
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import queue

VERSION = '1.2.1'

FACE_SIZE = 2048
FACE_NAMES = ['right', 'left', 'top', 'bottom', 'front', 'back']

FACE_DIRS = {
    'right':lambda u, v: [1, -v, -u],
    'left': lambda u, v: [-1, -v, u],
    'top': lambda u, v: [u, 1, v],
    'bottom': lambda u, v: [u, -1, -v],
    'front': lambda u, v: [u, -v, 1],
    'back': lambda u, v: [-u, -v, -1],
}

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def vector_to_uv_vec(x, y, z):
    lon = np.arctan2(z, x)
    lat = np.arcsin(np.clip(y, -1.0, 1.0))
    u = (lon / np.pi + 1) / 2
    v = (0.5 - lat / np.pi)
    return u, v

def generate_face(pano_img, face_name):
    # Prepare pano as numpy array
    pano_array = np.array(pano_img)
    p_height, p_width, _ = pano_array.shape
    
    # Create coordinate grid
    indices = np.linspace(0, FACE_SIZE - 1, FACE_SIZE)
    x_idx, y_idx = np.meshgrid(indices, indices)
    
    u_vals = 2 * (x_idx + 0.5) / FACE_SIZE - 1
    v_vals = 2 * (y_idx + 0.5) / FACE_SIZE - 1
    
    # Calculate directions based on face_name
    if face_name == 'right':  vec = (np.ones_like(u_vals), -v_vals, -u_vals)
    elif face_name == 'left': vec = (-np.ones_like(u_vals), -v_vals, u_vals)
    elif face_name == 'top':  vec = (u_vals, np.ones_like(u_vals), v_vals)
    elif face_name == 'bottom': vec = (u_vals, -np.ones_like(u_vals), -v_vals)
    elif face_name == 'front': vec = (u_vals, -v_vals, np.ones_like(u_vals))
    elif face_name == 'back':  vec = (-u_vals, -v_vals, -np.ones_like(u_vals))
    
    # Normalize vectors
    mag = np.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
    dir_x, dir_y, dir_z = vec[0]/mag, vec[1]/mag, vec[2]/mag
    
    # Map to UV
    u, v = vector_to_uv_vec(dir_x, dir_y, dir_z)
    
    # Pixel lookups (vectorized)
    px = (u * p_width).astype(np.int32) % p_width
    py = (v * p_height).astype(np.int32) % p_height
    
    # Sample from pano array
    result_array = pano_array[py, px]
    return Image.fromarray(result_array.astype(np.uint8))

def advanced_blend_from_middle(img, blend_width, blend_mode='cosine'):
    width, height = img.size
    mid = width // 2
    blend_width = min(blend_width, mid)
    
    img_array = np.array(img, dtype=np.float32)
    left_half = img_array[:, :mid]
    mirrored = np.fliplr(left_half)
    
    for x in range(blend_width):
        t = x / blend_width
        
        if blend_mode == 'cosine':
            alpha = (1 + math.cos(t * math.pi)) / 2
        else:
            alpha = 1 - t
        
        pos = mid + x
        
        if pos < width:
            img_array[:, pos] = (
                alpha * mirrored[:, x] + 
                (1 - alpha) * img_array[:, pos]
            )
    
    return Image.fromarray(img_array.astype(np.uint8))

def combine_faces_into_template(output_path, faces_dir):
    tile_size = FACE_SIZE
    width, height = tile_size * 3, tile_size * 2
    template = Image.new("RGB", (width, height))
    
    layout = {
        'down': (0, 0),
        'up': (tile_size, 0),
        'east': (tile_size * 2, 0),
        'north': (0, tile_size),
        'west': (tile_size, tile_size),
        'south': (tile_size * 2, tile_size),
    }
    
    for name, (x, y) in layout.items():
        face_path = os.path.join(faces_dir, f"{name}.png")
        if os.path.exists(face_path):
            face = Image.open(face_path).convert("RGB")
            template.paste(face, (x, y))
    
    template.save(output_path)

def generate_random_foldername(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_next_sky_number(all_skys_dir):
    if not os.path.exists(all_skys_dir):
        return 1
    
    existing = os.listdir(all_skys_dir)
    numbers = []
    for item in existing:
        if item.startswith("Sky"):
            # Strip extension (e.g. .zip) and check the rest
            base = os.path.splitext(item)[0]
            num_part = base[3:]
            if num_part.isdigit():
                numbers.append(int(num_part))
    
    return max(numbers) + 1 if numbers else 1

def process_single_face(face_name, pano_img, blend_width, blend_mode, out_dir, name_map):
    img = generate_face(pano_img, face_name)
    
    if face_name == 'top':
        img = img.rotate(90, expand=True)
    elif face_name == 'bottom':
        img = img.rotate(-90, expand=True)
    
    if face_name in ['top', 'bottom', 'left']:
        img = advanced_blend_from_middle(img, blend_width=blend_width, blend_mode=blend_mode)
    
    output_path = os.path.join(out_dir, f"{name_map[face_name]}.png")
    img.save(output_path)
    return face_name

def main_process(pano_path, blend_width, blend_mode, progress_callback):
    pano_dir = os.path.dirname(os.path.abspath(pano_path))
    
    all_skys_dir = os.path.join(pano_dir, "allSkys")
    os.makedirs(all_skys_dir, exist_ok=True)
    
    sky_num = get_next_sky_number(all_skys_dir)
    sky_folder_name = f"Sky{sky_num}"
    final_output_dir = os.path.join(all_skys_dir, sky_folder_name)
    
    temp_out_dir = os.path.join(pano_dir, f"temp_faces_{generate_random_foldername(4)}")
    os.makedirs(temp_out_dir, exist_ok=True)
    
    pano_img = Image.open(pano_path).convert('RGB')
    
    name_map = {
        'right': 'east',
        'left': 'west',
        'top': 'up',
        'bottom': 'down',
        'front': 'south',
        'back': 'north',
    }
    
    total_steps = len(FACE_NAMES) + 1
    completed_steps = 0
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for face in FACE_NAMES:
            futures.append(executor.submit(process_single_face, face, pano_img, blend_width, blend_mode, temp_out_dir, name_map))
        
        for future in futures:
            future.result()
            completed_steps += 1
            progress_callback(int((completed_steps / total_steps) * 100))
    
    output_template = os.path.join(temp_out_dir, "sky_result.png")
    combine_faces_into_template(output_template, temp_out_dir)
    progress_callback(95)
    
    src_overlay_dir = get_resource_path("SkyOverlayPack")
    
    os.makedirs(final_output_dir, exist_ok=True)
    
    if os.path.exists(src_overlay_dir):
        # Copy contents directly into final_output_dir instead of a subfolder
        shutil.copytree(src_overlay_dir, final_output_dir, dirs_exist_ok=True)
        # Save a small pack.png (128x128) for better performance in Minecraft
        pack_icon = Image.open(pano_path).convert("RGB")
        pack_icon.thumbnail((128, 128), Image.Resampling.LANCZOS)
        pack_icon.save(os.path.join(final_output_dir, "pack.png"), "PNG")
        
        target_paths = [
            os.path.join(final_output_dir, "assets", "minecraft", "mcpatcher", "sky", "world0", "cloud1.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "optifine", "sky", "world0", "cloud1.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "mcpatcher", "sky", "world0", "cloud2.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "optifine", "sky", "world0", "cloud2.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "mcpatcher", "sky", "world0", "skybox.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "optifine", "sky", "world0", "skybox.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "mcpatcher", "sky", "world0", "skybox2.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "optifine", "sky", "world0", "skybox2.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "mcpatcher", "sky", "world0", "starfield.png"),
            os.path.join(final_output_dir, "assets", "minecraft", "optifine", "sky", "world0", "starfield.png"),
        ]
        
        for target_path in target_paths:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy(output_template, target_path)
    
    shutil.rmtree(temp_out_dir, ignore_errors=True)
    
    # Create the zip file after generating the folder
    try:
        shutil.make_archive(final_output_dir, 'zip', final_output_dir)
        # Delete the folder after zipping
        shutil.rmtree(final_output_dir, ignore_errors=True)
    except Exception as e:
        print(f"Failed to create zip: {e}")
        
    progress_callback(100)

root = tk.Tk()
root.title("Skymaker Pro by vuacy (" + VERSION + ")")
root.geometry("500x450")

# Thread-safe UI update mechanism
def safe_update_progress(value):
    try:
        root.after(0, lambda: progress.configure(value=value))
    except: pass

def safe_update_status(text, color="blue"):
    try:
        root.after(0, lambda: status_label.config(text=text, fg=color))
    except: pass

def safe_show_info(title, message):
    try:
        root.after(0, lambda: messagebox.showinfo(title, message))
    except: pass

def safe_show_error(title, message):
    try:
        root.after(0, lambda: messagebox.showerror(title, message))
    except: pass

def safe_reset_ui():
    try:
        root.after(0, lambda: [
            progress.pack_forget(),
            create_btn.config(state="normal"),
            select_btn.config(state="normal")
        ])
    except: pass

tk.Label(root, text="Blend Mode:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
blend_mode_values = ["Cosine (Recommended)", "Linear (old)"]
blend_mode_box = ttk.Combobox(root, values=blend_mode_values, state="readonly", width=25)
blend_mode_box.set("Cosine (Recommended)")
blend_mode_box.pack(pady=5)

tk.Label(root, text="Blend Width (Pixels):", font=("Arial", 10, "bold")).pack(pady=(10, 5))
blend_values = [str(i) for i in range(200, 1001, 50)]
blend_box = ttk.Combobox(root, values=blend_values, state="readonly", width=15)
blend_box.set("500")
blend_box.pack(pady=5)

selected_file_label = tk.Label(root, text="No images selected.", fg="gray", wraplength=400)
selected_file_label.pack(pady=10)

status_label = tk.Label(root, text="", fg="blue")
status_label.pack(pady=5)

progress = ttk.Progressbar(root, length=350, mode='determinate')
progress.pack(pady=10)
progress.pack_forget()

selected_files = []

def select_images(files=None):
    global selected_files
    if not files:
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png"), ("All Files", "*.*")]
        )
    
    if files:
        selected_files = [os.path.abspath(f) for f in files]
        count = len(selected_files)
        selected_file_label.config(text=f"Selected {count} images:\n" + ", ".join([os.path.basename(f) for f in selected_files[:3]]) + ("..." if count > 3 else ""), fg="green")
        create_btn.pack(pady=10)

def run_creation():
    if not selected_files:
        return
        
    blend_width = int(blend_box.get())
    blend_mode_display = blend_mode_box.get()
    blend_mode = "cosine" if "Cosine" in blend_mode_display else "linear"
    
    progress.pack()
    create_btn.config(state="disabled")
    select_btn.config(state="disabled")
    
    def task():
        total_files = len(selected_files)
        for i, file_path in enumerate(selected_files):
            safe_update_status(f"Processing {i+1}/{total_files}: {os.path.basename(file_path)}")
            try:
                main_process(file_path, blend_width, blend_mode, safe_update_progress)
            except Exception as e:
                safe_show_error("Error", f"Failed to process {os.path.basename(file_path)}:\n{str(e)}")
        
        safe_update_status("All tasks finished!", color="green")
        safe_show_info("Done", f"Successfully processed {total_files} images.")
        safe_reset_ui()
    
    threading.Thread(target=task, daemon=True).start()

select_btn = tk.Button(root, text="Select Images", command=select_images, 
                       bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), 
                       padx=20, pady=5)
select_btn.pack(pady=10)

create_btn = tk.Button(root, text="Create Sky", command=run_creation,
                       bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                       padx=20, pady=5)

# Drag & Drop support - initialize last and with a fallback
def init_dnd():
    try:
        import windnd
        def on_drop(files):
            # Decode carefully to avoid GIL issues in callback
            try:
                files_decoded = [f.decode('utf-8') if isinstance(f, bytes) else f for f in files]
                root.after(10, lambda: select_images(files_decoded))
            except: pass
        windnd.hook_dropfiles(root, func=on_drop)
        status_label.config(text="Drag & Drop is ready!", fg="gray")
    except ImportError:
        pass
    except Exception as e:
        print(f"DND Init failed: {e}")

root.after(100, init_dnd)
root.mainloop()

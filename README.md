# ☁️ Basudev's Custom Sky Maker

> Transform any panoramic image into a Minecraft 1.8.9 OptiFine / MCPatcher sky resource pack — automatically, offline, and for free.

![Version](https://img.shields.io/badge/version-3.0.0-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Minecraft](https://img.shields.io/badge/Minecraft-1.8.9-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## ✨ Features

- 🤖 **AI Scene Detection** — automatically names your pack based on image colors (Galaxy Sky, Sunset Sky, Ocean Sky etc.)
- 🌈 **Minecraft § Color Codes** — pack name styled with real Minecraft formatting in `.mcmeta` and filename
- 🔍 **Built-in Image Upscaler** — upscale any image 1.5x / 2x / 3x / 4x before converting
- ☀️ **24/7 Sky Visibility** — sky shows at all times, day and night, always
- 📦 **Auto-numbered Packs** — Sky1, Sky2, Sky3... never overwrites your previous packs
- ✏️ **Custom Pack Naming** — type your own name or let AI auto-detect it
- 🎨 **Dark GUI** — clean professional dark theme interface
- 🖱️ **Drag & Drop** — drag images straight onto the window
- 📴 **100% Offline** — works with no internet after first setup
- 🔧 **Smart Launcher** — START.bat auto-checks and installs all requirements

---

## 🖼️ What It Does

Takes a panoramic sky image like this 👇
```
your_sky.jpg  (any panoramic / wide sky photo)
```

And outputs a ready-to-use Minecraft resource pack ZIP like this 👇
```
§bCelestial_Storm_Sky.zip
├── pack.mcmeta       ← colored name in Minecraft menu
├── pack.png          ← preview thumbnail
└── assets/minecraft/
    ├── optifine/sky/world0/    ← OptiFine support
    └── mcpatcher/sky/world0/   ← MCPatcher support
        ├── cloud1.png
        ├── cloud2.png
        ├── starfield.png
        ├── starfield01.png
        ├── sky_sunflare.png
        ├── sky1.properties
        └── ... (sky2 - sky8)
```

---

## 🚀 How To Use

### First Time Setup
1. Download the latest ZIP from [Releases](../../releases)
2. Extract the ZIP anywhere on your PC
3. Double-click **START.bat**
4. It will auto-check and install Python, Pillow, and NumPy if missing
5. Say **yes** to any install prompts

### Creating a Sky Pack
1. Launch via **START.bat**
2. Drop your panoramic sky image onto the drop zone (or click to browse)
3. Optionally type a custom pack name — or leave empty for AI auto-detection
4. Choose your face resolution (512 / 1024 / 2048 / 4096)
5. Click **🚀 Create Sky Pack**
6. Your ZIP is saved in an `allSkys` folder next to your image

### Installing in Minecraft
1. Open Minecraft 1.8.9
2. Go to **Options → Resource Packs → Open Resource Pack Folder**
3. Drop your generated `.zip` file into that folder
4. Select it in the resource pack list
5. Launch your world and look up! ☁️

---

## 📋 Requirements

| Requirement | Version | Notes |
|---|---|---|
| Windows | 10 / 11 | Required |
| Python | 3.8 or higher | Auto-installed by START.bat |
| Pillow | 9.0+ | Auto-installed |
| NumPy | 1.21+ | Auto-installed |
| Minecraft | 1.8.9 | Target version |
| OptiFine | HD U G5+ | For sky to show in-game |

---

## 🎮 Supported Loaders

| Loader | Supported |
|---|---|
| OptiFine (1.8.9) | ✅ Yes |
| MCPatcher | ✅ Yes |
| Fabric / Forge | ❌ No |
| Vanilla | ❌ No |

---

## 📁 File Structure
```
SkyMaker/
├── SkyMaker.pyw        ← Main application (double-click to run)
├── START.bat           ← Smart launcher with auto-installer
├── requirements.txt    ← Python dependencies
└── overlays/           ← Bundled sky overlay textures
    ├── cloud1.png
    ├── cloud2.png
    ├── starfield.png
    ├── starfield01.png
    ├── sky_sunflare.png
    ├── skybox.png
    └── skybox2.png
```

---

## 🔒 Safety & Trust

- ✅ **100% open source** — every line of code is visible on this page
- ✅ **No EXE files** — only `.py` and `.bat` scripts, fully readable
- ✅ **No internet required** after setup — runs completely offline
- ✅ **No telemetry, no tracking, no ads** — pure local tool
- ✅ **MIT Licensed** — free to use, modify, and share forever

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or want to suggest a feature:

1. Fork this repository
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Push and open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Made with ❤️ by Basudev**

If this helped you, consider giving the repo a ⭐ star — it really helps!
```

---

## 📄 LICENSE
```
MIT License

Copyright (c) 2026 Basudev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📄 requirements.txt
```
Pillow>=9.0.0
numpy>=1.21.0

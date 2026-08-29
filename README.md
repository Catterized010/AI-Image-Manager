AI Image Manager

A lightweight desktop app for organizing folders of AI-generated images from Automatic1111 / Forge and ComfyUI. Browse your gens in a Lightroom-style grid, sort them into folders by model and LoRA, find exact duplicates, and see which prompt tags show up most across a folder.



Features
Grid library view — thumbnail browser with a resizable column layout and full-size viewer (double-click any image).
Metadata panel — shows filename, model, and LoRA(s) for the selected image, read straight from embedded generation metadata.
Sort by metadata — automatically moves images into Model/LoRA/ subfolders based on what generated them.
Duplicate scanner — SHA-256 hashing finds exact-duplicate files and lets you review each pair side-by-side before deciding what to keep.
Common tags scanner — scans every image in a folder and shows a ranked, shareable breakdown of the most frequent prompt tags, with what percentage of images contain each one.
Reads both formats — supports A1111/Forge's parameters text metadata and ComfyUI's embedded JSON workflow graph, so it works regardless of which tool generated the image.
Requirements
Python 3.8+
Pillow
bash
pip install -r requirements.txt
Usage
bash
python META.py

The app opens in your current working directory by default. Use Change Dir to point it at your outputs folder, or double-click a subfolder in the sidebar to navigate.

⇄ Sort by Meta — moves all images in the current folder into Model/LoRA subfolders. This is a file-moving operation — try it on a copy of your folder first.
🔍 Scan Dupes — walks the folder for byte-identical images and prompts you to keep or delete each pair found.
🏷️ Common Tags — parses every image's prompt and pops up a ranked list of shared tags across the whole folder.
Notes
Tag extraction pulls text from every text-encode node in a ComfyUI workflow, so negative-prompt terms may currently be included alongside positive ones.
Folder names generated from metadata are sanitized, but since that metadata comes from image files themselves, treat images from unknown sources with the same caution you'd give any downloaded file before running batch operations on them.
License

MIT — see LICENSE.

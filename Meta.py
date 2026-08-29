import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
import os
import re
import shutil
import hashlib
import json
from collections import Counter

# --- Modern Dark Theme Colors (Lightroom Inspired) ---
BG_DARK = "#1e1e1e"
BG_PANEL = "#252526"
BG_CARD = "#2d2d2d"
BG_HOVER = "#3e3e42"
FG_PRIMARY = "#e0e0e0"
FG_SECONDARY = "#858585"
ACCENT_BLUE = "#007acc"
ACCENT_RED = "#ff4757"
ACCENT_ORANGE = "#f39c12"
ACCENT_GREEN = "#27ae60"
ACCENT_PURPLE = "#9b59b6"

class LightroomStyleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Image Manager")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        self.root.configure(bg=BG_DARK)

        self.current_directory = os.getcwd()
        self.image_data = [] # Stores dicts: {'path', 'thumb', 'model', 'lora'}
        self.selected_index = None
        self.current_columns = 4

        self.setup_ui()
        self.load_directory(self.current_directory)

    def setup_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

    def build_left_panel(self):
        left_frame = tk.Frame(self.root, bg=BG_PANEL, width=250, bd=0)
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.grid_propagate(False)

        tk.Label(left_frame, text="LIBRARY", bg=BG_PANEL, fg=FG_SECONDARY, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill=tk.X, padx=15, pady=(15,5))
        
        btn_frame = tk.Frame(left_frame, bg=BG_PANEL)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="📁 Change Dir", bg=BG_HOVER, fg=FG_PRIMARY, bd=0, command=self.change_directory).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="⬆ Up", bg=BG_HOVER, fg=FG_PRIMARY, bd=0, command=self.go_up).pack(fill=tk.X, pady=2)

        tk.Label(left_frame, text="FOLDERS", bg=BG_PANEL, fg=FG_SECONDARY, font=("Segoe UI", 9, "bold"), anchor="w").pack(fill=tk.X, padx=15, pady=(20,5))

        self.folder_listbox = tk.Listbox(left_frame, bg=BG_DARK, fg=FG_PRIMARY, selectbackground=ACCENT_BLUE, bd=0, highlightthickness=0, font=("Segoe UI", 10))
        self.folder_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.folder_listbox.bind('<Double-Button-1>', self.on_folder_double_click)

    def build_center_panel(self):
        center_frame = tk.Frame(self.root, bg=BG_DARK)
        center_frame.grid(row=0, column=1, sticky="nsew")
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        top_bar = tk.Frame(center_frame, bg=BG_DARK, height=40)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.path_label = tk.Label(top_bar, text="Current: ", bg=BG_DARK, fg=FG_SECONDARY, font=("Segoe UI", 10))
        self.path_label.pack(side=tk.LEFT)

        # --- Top Right Buttons ---
        btn_container = tk.Frame(top_bar, bg=BG_DARK)
        btn_container.pack(side=tk.RIGHT)

        self.tags_btn = tk.Button(btn_container, text="🏷️ COMMON TAGS", bg=ACCENT_PURPLE, fg="white", bd=0, font=("Segoe UI", 10, "bold"), padx=15, pady=5, command=self.scan_common_tags)
        self.tags_btn.pack(side=tk.RIGHT, padx=(5,0))

        self.dupe_btn = tk.Button(btn_container, text="🔍 SCAN DUPES", bg=ACCENT_ORANGE, fg="white", bd=0, font=("Segoe UI", 10, "bold"), padx=15, pady=5, command=self.start_dupe_scan)
        self.dupe_btn.pack(side=tk.RIGHT, padx=(5,0))

        self.sort_btn = tk.Button(btn_container, text="⇄ SORT BY META", bg=ACCENT_RED, fg="white", bd=0, font=("Segoe UI", 10, "bold"), padx=15, pady=5, command=self.sort_images)
        self.sort_btn.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(center_frame, bg=BG_DARK, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(center_frame, orient="vertical", command=self.canvas.yview, troughcolor=BG_DARK, bg=BG_HOVER)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def build_right_panel(self):
        right_frame = tk.Frame(self.root, bg=BG_PANEL, width=280, bd=0)
        right_frame.grid(row=0, column=2, sticky="nsew")
        right_frame.grid_propagate(False)

        tk.Label(right_frame, text="METADATA", bg=BG_PANEL, fg=FG_SECONDARY, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill=tk.X, padx=15, pady=(15,10))

        info_container = tk.Frame(right_frame, bg=BG_PANEL)
        info_container.pack(fill=tk.BOTH, expand=True, padx=15)

        self.lbl_filename = tk.Label(info_container, text="Filename: -", bg=BG_PANEL, fg=FG_PRIMARY, font=("Segoe UI", 9), anchor="w", wraplength=240, justify="left")
        self.lbl_filename.pack(fill=tk.X, pady=5)

        self.lbl_model = tk.Label(info_container, text="Model: -", bg=BG_PANEL, fg=FG_PRIMARY, font=("Segoe UI", 11, "bold"), anchor="w", wraplength=240, justify="left")
        self.lbl_model.pack(fill=tk.X, pady=5)

        self.lbl_lora = tk.Label(info_container, text="LoRA: -", bg=BG_PANEL, fg=ACCENT_ORANGE, font=("Segoe UI", 11, "bold"), anchor="w", wraplength=240, justify="left")
        self.lbl_lora.pack(fill=tk.X, pady=5)

    def on_canvas_resize(self, event):
        new_cols = max(1, event.width // 210)
        if new_cols != self.current_columns:
            self.current_columns = new_cols
            self.render_grid()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # --- DATA & LOGIC ---

    def get_full_file_hash(self, filepath):
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    def get_metadata(self, filepath):
        model, lora = "Unknown", "None"
        try:
            with Image.open(filepath) as img:
                params = img.info.get('parameters', '')
                if params:
                    model_match = re.search(r'Model:\s*([^\n,]+)', params)
                    if model_match: model = model_match.group(1).strip()
                    lora_match = re.search(r'Lora:\s*([^\n]+)', params, re.IGNORECASE)
                    if lora_match:
                        lora_raw = lora_match.group(1).strip()
                        loras = [l.split(':')[0].strip() for l in lora_raw.split(',') if l.strip()]
                        lora = ", ".join(loras) if loras else "None"
                else:
                    exif = img.getexif()
                    if exif: model = exif.get(0x0110, "Unknown Camera")
        except Exception: pass
        return model, lora

    def get_prompt_tags(self, filepath):
        """
        Extracts positive-prompt 'tags' from an image's embedded generation
        metadata. Supports both A1111/Forge-style ('parameters' text block)
        and ComfyUI-style ('prompt' JSON workflow graph) metadata.
        Returns a set of lowercase, deduplicated tags for this single image.
        """
        raw_prompt_texts = []

        try:
            with Image.open(filepath) as img:
                info = img.info or {}

                # --- A1111 / Forge style ---
                params = info.get('parameters', '')
                if params:
                    positive = params.split('Negative prompt:')[0]
                    raw_prompt_texts.append(positive)

                # --- ComfyUI style (JSON workflow graph) ---
                comfy_json = info.get('prompt') or info.get('workflow')
                if comfy_json:
                    try:
                        data = json.loads(comfy_json)
                        nodes = data.values() if isinstance(data, dict) else []
                        for node in nodes:
                            if not isinstance(node, dict):
                                continue
                            inputs = node.get('inputs', {})
                            if not isinstance(inputs, dict):
                                continue
                            text_val = inputs.get('text')
                            if isinstance(text_val, str) and text_val.strip():
                                raw_prompt_texts.append(text_val)
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        pass
        except (UnidentifiedImageError, OSError):
            pass

        tags = set()
        for block in raw_prompt_texts:
            for chunk in block.split(','):
                tag = chunk.strip().lower()
                if not tag:
                    continue
                # Strip A1111 emphasis/weight syntax: (word:1.2) -> word, (word) -> word, [word] -> word
                tag = re.sub(r'^[\(\[]+|[\)\]]+$', '', tag)
                tag = re.sub(r':\s*[\d.]+$', '', tag).strip()
                # Collapse stray whitespace/newlines from multiline prompts
                tag = re.sub(r'\s+', ' ', tag)
                if tag:
                    tags.add(tag)
        return tags

    def load_directory(self, path):
        if not os.path.exists(path): return
        self.current_directory = path
        self.path_label.config(text=f"Current: {path}")
        self.folder_listbox.delete(0, tk.END)
        self.selected_index = None
        self.update_right_panel()
        
        try:
            for item in sorted(os.listdir(path)):
                if os.path.isdir(os.path.join(path, item)):
                    self.folder_listbox.insert(tk.END, f"📁 {item}")
        except PermissionError: pass

        self.process_images()

    def process_images(self):
        self.image_data = []
        image_files = [f for f in os.listdir(self.current_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        
        for filename in image_files:
            filepath = os.path.join(self.current_directory, filename)
            model, lora = self.get_metadata(filepath)

            try:
                with Image.open(filepath) as img:
                    img.thumbnail((200, 200))
                    thumb = ImageTk.PhotoImage(img)
            except Exception:
                thumb = None

            self.image_data.append({
                "filename": filename, "path": filepath, "thumb": thumb,
                "model": model, "lora": lora
            })
        
        self.render_grid()

    def render_grid(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, data in enumerate(self.image_data):
            row = i // self.current_columns
            col = i % self.current_columns

            card = tk.Frame(self.scrollable_frame, bg=BG_CARD, bd=0, highlightthickness=2, highlightbackground=BG_DARK)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            if data["thumb"]:
                lbl_img = tk.Label(card, image=data["thumb"], bg=BG_CARD, cursor="hand2")
                lbl_img.pack(padx=5, pady=5)
                lbl_img.bind("<Button-1>", lambda e, idx=i: self.select_image(idx))
                lbl_img.bind("<Double-Button-1>", lambda e, idx=i: self.open_viewer(idx))

            lbl_name = tk.Label(card, text=data["filename"], bg=BG_CARD, fg=FG_SECONDARY, font=("Segoe UI", 8), anchor="w", wraplength=180)
            lbl_name.pack(fill=tk.X, padx=5, pady=(0,5))
            lbl_name.bind("<Button-1>", lambda e, idx=i: self.select_image(idx))

        for i in range(self.current_columns):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)

    def select_image(self, index):
        self.selected_index = index
        for i, widget in enumerate(self.scrollable_frame.winfo_children()):
            widget.config(highlightbackground=ACCENT_BLUE if i == index else BG_DARK)
        self.update_right_panel()

    def update_right_panel(self):
        if self.selected_index is None or self.selected_index >= len(self.image_data):
            self.lbl_filename.config(text="Filename: -")
            self.lbl_model.config(text="Model: -")
            self.lbl_lora.config(text="LoRA: -")
            return

        data = self.image_data[self.selected_index]
        self.lbl_filename.config(text=f"Filename: {data['filename']}")
        self.lbl_model.config(text=f"Model: {data['model']}")
        self.lbl_lora.config(text=f"LoRA: {data['lora']}")

    def open_viewer(self, index):
        data = self.image_data[index]
        viewer = tk.Toplevel(self.root)
        viewer.title(data["filename"])
        viewer.configure(bg="black")
        try:
            viewer.state('zoomed') # Windows maximize
        except:
            viewer.attributes('-zoomed', True) # Linux maximize

        try:
            with Image.open(data["path"]) as full_img:
                screen_w = viewer.winfo_screenwidth()
                screen_h = viewer.winfo_screenheight()
                full_img.thumbnail((screen_w, screen_h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(full_img)

            lbl = tk.Label(viewer, image=photo, bg="black")
            lbl.image = photo
            lbl.pack(expand=True)
            
            lbl.bind("<Button-1>", lambda e: viewer.destroy())
            viewer.bind("<Escape>", lambda e: viewer.destroy())
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}", parent=viewer)

    # --- DUPLICATE SCANNER LOGIC ---

    def start_dupe_scan(self):
        messagebox.showinfo("Scanning", "Scanning folder for duplicates...\n(This uses SHA256 hashing and may take a moment for large folders).")
        self.root.update() # Force UI update
        self._run_dupe_scanner()

    def _run_dupe_scanner(self):
        hash_map = {}
        
        # Build hash map of current images
        for i, data in enumerate(self.image_data):
            h = self.get_full_file_hash(data['path'])
            if not h: continue
            
            if h in hash_map:
                # Found a duplicate! Pause scan, show dialog.
                self._show_dupe_dialog(original_idx=hash_map[h], dupe_idx=i)
                return # Stop loop, wait for user choice
            else:
                hash_map[h] = i
                
        # If loop finishes without returning, no more dupes
        messagebox.showinfo("Scan Complete", "No more duplicate images found in this folder.")

    def _show_dupe_dialog(self, original_idx, dupe_idx):
        orig_data = self.image_data[original_idx]
        dupe_data = self.image_data[dupe_idx]

        dialog = tk.Toplevel(self.root)
        dialog.title("Duplicate Detected")
        dialog.configure(bg=BG_DARK)
        dialog.geometry("900x550")
        dialog.transient(self.root)
        dialog.grab_set() # Make it modal (forces user to answer)

        tk.Label(dialog, text="EXACT DUPLICATE FOUND", bg=BG_DARK, fg=ACCENT_RED, font=("Segoe UI", 14, "bold")).pack(pady=15)

        content_frame = tk.Frame(dialog, bg=BG_DARK)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # --- Left Side (Original) ---
        left_frame = tk.Frame(content_frame, bg=BG_CARD, bd=2, relief=tk.SUNKEN)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
        
        tk.Label(left_frame, text="ORIGINAL FILE", bg=BG_CARD, fg=ACCENT_GREEN, font=("Segoe UI", 10, "bold")).pack(pady=5)
        try:
            with Image.open(orig_data['path']) as img:
                img = img.resize((350, 350), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            lbl_orig = tk.Label(left_frame, image=photo, bg=BG_CARD)
            lbl_orig.image = photo
            lbl_orig.pack(padx=10, pady=5)
        except Exception: pass
        tk.Label(left_frame, text=orig_data['filename'], bg=BG_CARD, fg=FG_PRIMARY, font=("Segoe UI", 9), wraplength=300).pack(pady=5)

        # --- Right Side (Duplicate) ---
        right_frame = tk.Frame(content_frame, bg=BG_CARD, bd=2, relief=tk.SUNKEN)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10,0))
        
        tk.Label(right_frame, text="DUPLICATE FILE", bg=BG_CARD, fg=ACCENT_RED, font=("Segoe UI", 10, "bold")).pack(pady=5)
        try:
            with Image.open(dupe_data['path']) as img2:
                img2 = img2.resize((350, 350), Image.LANCZOS)
                photo2 = ImageTk.PhotoImage(img2)
            lbl_dupe = tk.Label(right_frame, image=photo2, bg=BG_CARD)
            lbl_dupe.image = photo2
            lbl_dupe.pack(padx=10, pady=5)
        except Exception: pass
        tk.Label(right_frame, text=dupe_data['filename'], bg=BG_CARD, fg=FG_PRIMARY, font=("Segoe UI", 9), wraplength=300).pack(pady=5)

        # --- Buttons ---
        btn_frame = tk.Frame(dialog, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        def keep_both():
            dialog.destroy()
            self._run_dupe_scanner() # Continue scanning for next dupe

        def delete_original():
            dialog.destroy()
            try:
                os.remove(orig_data['path'])
            except Exception as e: messagebox.showerror("Error", str(e))
            self.process_images() # Refresh main UI
            self._run_dupe_scanner() # Continue scanning

        def delete_duplicate():
            dialog.destroy()
            try:
                os.remove(dupe_data['path'])
            except Exception as e: messagebox.showerror("Error", str(e))
            self.process_images() # Refresh main UI
            self._run_dupe_scanner() # Continue scanning

        tk.Button(btn_frame, text="Keep Both", bg=BG_HOVER, fg=FG_PRIMARY, font=("Segoe UI", 10, "bold"), width=15, command=keep_both).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Delete Original", bg="#cc0000", fg="white", font=("Segoe UI", 10, "bold"), width=15, command=delete_original).pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_frame, text="Delete Duplicate", bg=ACCENT_RED, fg="white", font=("Segoe UI", 10, "bold"), width=15, command=delete_duplicate).pack(side=tk.RIGHT, padx=10)

    # --- COMMON TAGS SCANNER ---

    def scan_common_tags(self):
        if not self.image_data:
            messagebox.showinfo("Common Tags", "No images loaded in this folder.")
            return

        self.root.config(cursor="watch")
        self.root.update()

        tag_image_count = Counter()   # how many images contain each tag
        images_with_no_tags = 0

        try:
            for data in self.image_data:
                tags = self.get_prompt_tags(data['path'])
                if not tags:
                    images_with_no_tags += 1
                    continue
                tag_image_count.update(tags)  # Counter.update on a set adds 1 per unique tag
        finally:
            self.root.config(cursor="")

        if not tag_image_count:
            messagebox.showinfo(
                "Common Tags",
                "No embedded prompt metadata found in these images.\n"
                "(Expected an A1111/Forge 'parameters' block or a ComfyUI 'prompt' workflow.)"
            )
            return

        self._show_common_tags_popup(tag_image_count, total_images=len(self.image_data), skipped=images_with_no_tags)

    def _show_common_tags_popup(self, tag_image_count, total_images, skipped):
        popup = tk.Toplevel(self.root)
        popup.title("Most Common Tags")
        popup.configure(bg=BG_DARK)
        popup.geometry("480x600")
        popup.transient(self.root)

        tk.Label(popup, text="MOST COMMON TAGS", bg=BG_DARK, fg=ACCENT_PURPLE,
                 font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

        subtitle = f"Across {total_images} image(s)"
        if skipped:
            subtitle += f"  •  {skipped} had no readable prompt metadata"
        tk.Label(popup, text=subtitle, bg=BG_DARK, fg=FG_SECONDARY, font=("Segoe UI", 9)).pack(pady=(0, 10))

        list_container = tk.Frame(popup, bg=BG_DARK)
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        canvas = tk.Canvas(list_container, bg=BG_DARK, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        max_count = tag_image_count.most_common(1)[0][1] if tag_image_count else 1

        for tag, count in tag_image_count.most_common(100):
            row = tk.Frame(inner, bg=BG_CARD)
            row.pack(fill=tk.X, pady=3)

            pct = count / total_images if total_images else 0
            bar_width = max(2, int(180 * (count / max_count)))

            bar_bg = tk.Frame(row, bg=BG_HOVER, width=180, height=10)
            bar_bg.pack(side=tk.LEFT, padx=(10, 10), pady=8)
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=ACCENT_PURPLE, width=bar_width, height=10).place(x=0, y=0)

            tk.Label(row, text=tag, bg=BG_CARD, fg=FG_PRIMARY, font=("Segoe UI", 10),
                     anchor="w", wraplength=170, justify="left").pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(row, text=f"{count}/{total_images} ({pct:.0%})", bg=BG_CARD, fg=FG_SECONDARY,
                     font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=10)

        tk.Button(popup, text="Close", bg=BG_HOVER, fg=FG_PRIMARY, font=("Segoe UI", 10, "bold"),
                  command=popup.destroy).pack(pady=(0, 15))

    # --- NAVIGATION & SORTING ---

    def sanitize_folder_name(self, name):
        if not name: return "Unknown"
        # Sanitize traversal indicators like '..' to prevent path exposure
        name = re.sub(r'[\.]{2,}', '', name)
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
        name = re.sub(r'\s+', ' ', name).strip().rstrip('. ')
        return name if name else "Unknown"

    def sort_images(self):
        if not messagebox.askyesno("Confirm Sort", "Move images into Model/LoRA subfolders?"): return

        moved = 0
        for data in self.image_data:
            safe_model = self.sanitize_folder_name(data["model"])
            safe_lora = self.sanitize_folder_name(data["lora"])
            if safe_lora == "Unknown": safe_lora = "No_Lora"

            target_dir = os.path.join(self.current_directory, safe_model, safe_lora)
            try:
                os.makedirs(target_dir, exist_ok=True)
                
                # Collision protection
                target_path = os.path.join(target_dir, data["filename"])
                base, ext = os.path.splitext(data["filename"])
                counter = 1
                
                while os.path.exists(target_path):
                    target_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1

                shutil.move(data["path"], target_path)
                moved += 1
            except OSError: pass

        messagebox.showinfo("Sort Complete", f"Moved {moved} images.")
        self.load_directory(self.current_directory)

    def on_folder_double_click(self, event):
        sel = self.folder_listbox.curselection()
        if not sel: return
        folder = self.folder_listbox.get(sel[0]).replace("📁 ", "").strip()
        new_path = os.path.join(self.current_directory, folder)
        if os.path.isdir(new_path): self.load_directory(new_path)

    def go_up(self):
        parent = os.path.dirname(self.current_directory)
        if parent != self.current_directory: self.load_directory(parent)

    def change_directory(self):
        chosen = filedialog.askdirectory(title="Select Root Folder")
        if chosen: self.load_directory(chosen)

if __name__ == "__main__":
    root = tk.Tk()
    app = LightroomStyleApp(root)
    root.mainloop()
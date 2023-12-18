import os
import string
import tkinter as tk
import zstandard as zstd
import shutil
from tkinter import filedialog
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import tempfile
from PIL import Image, ImageTk
import threading

def read_game_folder(file_path='gamefolder.txt'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("gamefolder.txt not found.")
        return None

def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def search_steam_directories(game_folder, drives):
    steam_path_suffix = "Steam\\steamapps\\common"
    for drive in drives:
        potential_path = os.path.join(drive, "Program Files (x86)", steam_path_suffix, game_folder)
        if os.path.exists(potential_path):
            return potential_path

        potential_path = os.path.join(drive, "Program Files", steam_path_suffix, game_folder)
        if os.path.exists(potential_path):
            return potential_path

    return None

def prompt_user_for_path():
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    return folder_selected

def decompress_zst_file(zst_file_path, output_path):
    with open(zst_file_path, 'rb') as compressed:
        dctx = zstd.ZstdDecompressor()
        with open(output_path, 'wb') as destination:
            dctx.copy_stream(compressed, destination)

def process_mod_files(source_dir, dest_dir):
    for root, dirs, files in os.walk(source_dir):

        for dir in dirs:
            source_sub_dir = os.path.join(root, dir)
            dest_sub_dir = os.path.join(dest_dir, os.path.relpath(source_sub_dir, source_dir))
            os.makedirs(dest_sub_dir, exist_ok=True)


        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)
            dest_file_path = os.path.join(dest_dir, rel_path)

            if file.endswith('.zst'):
            
                decompressed_file_path = os.path.splitext(dest_file_path)[0]
                decompress_zst_file(file_path, decompressed_file_path)
            else:
            
                shutil.copy(file_path, dest_file_path)



def parse_extract_pointer(file_path, temp_dir, game_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    instructions = []
    for line in lines:
        if '->' in line:
            src, dest = line.split('->')
            src = os.path.join(temp_dir, src.strip().replace("Tempdir/", ""))
            dest = dest.strip().replace("%GamePath%", game_path)
            instructions.append((src, dest))

    return instructions

def move_files(instructions):
    for src, dest in instructions:
        if os.path.isdir(src):
        
            if not os.path.exists(dest):
                os.makedirs(dest)

        
            for src_dir, dirs, files in os.walk(src):
                dst_dir = src_dir.replace(src, dest, 1)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                for file in files:
                    src_file = os.path.join(src_dir, file)
                    dst_file = os.path.join(dst_dir, file)
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    shutil.copy(src_file, dst_dir)
        else:
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            shutil.copy(src, dest)


def find_steam_game_path():
    game_folder = read_game_folder()
    if not game_folder:
        return None

    drives = get_available_drives()
    game_path = search_steam_directories(game_folder, drives)
    if game_path:
        return game_path
    else:
        print("Game folder not found in default directories. Please select the game folder.")
        return prompt_user_for_path()

def play_midi(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(loops=-1)
        pygame.mixer.music.set_volume(0.5)
    except Exception as e:
        print(f"Error playing MIDI: {e}")

def install_game(mod_files_dir, temp_dir, root, callback):
    game_installation_path = find_steam_game_path()
    if game_installation_path:
        print(f"Game Installation Path: {game_installation_path}")
        process_mod_files(mod_files_dir, temp_dir)
        instructions = parse_extract_pointer("extract_pointer.txt", temp_dir, game_installation_path)
        move_files(instructions)
        callback()  # Call the callback function after installation
        root.after(0, callback)
    else:
        print("Game installation path not found.")


def create_gui(mod_files_dir, midi_file_path, image_path):
    def on_install():
        threading.Thread(target=install_game, args=(mod_files_dir, temp_dir, root, on_installation_complete), daemon=True).start()

    def on_installation_complete():

        finish_button.pack(side=tk.LEFT, padx=10)
        status_label.config(text="Installation Completed!")

    def on_finish():
        root.destroy()

    def on_play():
        pygame.mixer.music.unpause()

    def on_pause():
        pygame.mixer.music.pause()

    def on_volume_change(v):
        pygame.mixer.music.set_volume(float(v))

    root = tk.Tk()
    root.title("ANK Mod Installer")
    root.geometry("800x600")


    img = Image.open(image_path)
    img = img.resize((780, 500), Image.Resampling.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    img_label = tk.Label(root, image=img_photo)
    img_label.image = img_photo
    img_label.pack(pady=10)


    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=10)

    install_button = tk.Button(button_frame, text="Install", command=on_install)
    install_button.pack(side=tk.LEFT, padx=10)

    play_button = tk.Button(button_frame, text="Play", command=on_play)
    play_button.pack(side=tk.LEFT, padx=10)

    pause_button = tk.Button(button_frame, text="Pause", command=on_pause)
    pause_button.pack(side=tk.LEFT, padx=10)

    volume_slider = tk.Scale(button_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, label="Volume", command=on_volume_change)
    volume_slider.set(0.5)
    volume_slider.pack(side=tk.LEFT, padx=10)

    status_label = tk.Label(root, text="")
    status_label.pack(side=tk.BOTTOM, pady=10)

    finish_button = tk.Button(root, text="Finish", command=on_finish)

    play_midi(midi_file_path)

    root.mainloop()

# Main execution
mod_files_dir = 'modfiles'
midi_file_path = 'music'
image_path = 'installer_image'

with tempfile.TemporaryDirectory() as temp_dir:
    create_gui(mod_files_dir, midi_file_path, image_path)
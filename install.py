import os
import string
import tkinter as tk
import shutil
from tkinter import filedialog
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
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

        potential_path = os.path.join(drive, "SteamLibrary", steam_path_suffix, game_folder)
        if os.path.exists(potential_path):
            return potential_path

    return None

def prompt_user_for_path(root):
    root.withdraw()  # Hide the main window
    folder_selected = filedialog.askdirectory(parent=root)
    root.deiconify()  # Show the main window again
    return folder_selected

def find_steam_game_path(root):
    game_folder = read_game_folder()
    if not game_folder:
        print("Game folder not specified in gamefolder.txt.")
        return None

    drives = get_available_drives()
    game_path = search_steam_directories(game_folder, drives)
    if game_path:
        print(f"Found game path: {game_path}")
        return game_path
    else:
        print("Game folder not found in default directories. Prompting user for path.")
        return prompt_user_for_path(root)

def play_midi(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(loops=-1)
        pygame.mixer.music.set_volume(0.5)
    except Exception as e:
        print(f"Error playing MIDI: {e}")

def copy_files(src, dest):
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
    except Exception as e:
        print(f"Error copying {src} to {dest}: {e}")

def install_game(mod_files_dir, game_installation_path, callback):
    if not game_installation_path:
        print("Game installation path not found.")
        return

    print(f"Game Installation Path: {game_installation_path}")
    try:
        for item in os.listdir(mod_files_dir):
            src = os.path.join(mod_files_dir, item)
            dest = os.path.join(game_installation_path, item)
            if os.path.isdir(src):
                shutil.copytree(src, dest, dirs_exist_ok=True)
            elif os.path.isfile(src):
                shutil.copy2(src, dest)
    except Exception as e:
        print(f"Error during installation: {e}")
    callback()

def create_gui(mod_files_dir, midi_file_path, image_path):
    root = tk.Tk()

    def on_install():
        game_installation_path = find_steam_game_path(root)
        if game_installation_path:
            threading.Thread(target=install_game, args=(mod_files_dir, game_installation_path, on_installation_complete), daemon=True).start()
        else:
            print("Unable to find the game installation path.")

    def on_installation_complete():
        img_label.pack_forget()  # Hide the image label
        finish_button.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def on_finish():
        root.destroy()

    def on_play():
        pygame.mixer.music.unpause()

    def on_pause():
        pygame.mixer.music.pause()

    def on_volume_change(v):
        pygame.mixer.music.set_volume(float(v))

    def on_close():
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error stopping MIDI playback: {e}")
        root.destroy()
    
    root.title("ANK Mod Installer")
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.geometry("800x600")

    img = Image.open(image_path)
    img = img.resize((780, 500), Image.Resampling.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    img_label = tk.Label(root, image=img_photo)
    img_label.image = img_photo
    img_label.pack(pady=10)

    finish_button = tk.Button(root, text="Finish", command=on_finish, font=("Helvetica", 20))
    finish_button.config(height=20, width=50)  # Adjust size as needed

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

    play_midi(midi_file_path)

    root.mainloop()

# Main execution
mod_files_dir = 'modfiles'
midi_file_path = 'music'
image_path = 'installer_image'
create_gui(mod_files_dir, midi_file_path, image_path)

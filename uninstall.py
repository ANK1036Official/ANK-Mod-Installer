import os
import string
import shutil

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

def parse_extract_pointer(file_path, game_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    instructions = []
    for line in lines:
        if '->' in line:
            _, dest = line.split('->')
            dest = dest.strip().replace("%GamePath%", game_path)
            instructions.append(dest)
    
    return instructions

def uninstall_game(game_path, instructions):
    for dest in instructions:
        full_dest_path = os.path.join(game_path, dest)
        if os.path.exists(full_dest_path):
            if os.path.isdir(full_dest_path):
                shutil.rmtree(full_dest_path)
            else:
                os.remove(full_dest_path)
            print(f"Removed: {full_dest_path}")
        else:
            print(f"File or directory not found: {full_dest_path}")

def main():
    game_folder = read_game_folder()
    if not game_folder:
        return

    drives = get_available_drives()
    game_path = search_steam_directories(game_folder, drives)
    if game_path:
        print(f"Game Installation Path: {game_path}")
        instructions = parse_extract_pointer("extract_pointer.txt", game_path)
        uninstall_game(game_path, instructions)
    else:
        print("Game installation path not found.")

if __name__ == "__main__":
    main()

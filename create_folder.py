import os
import sys

def create_folder_with_file(file_name):
    with open(file_name, 'r') as file:
        lines = file.readlines()
        number = 1
        is_created = False
        for line in lines:
            arr_lines = line.strip().split(' ')
            if 'practices' == arr_lines[-1]:
                is_created = True
                continue
            if is_created:
                folder_name = f'{number}. {line.strip()}'
                os.makedirs(folder_name, exist_ok=True)
                print(f"Folder '{folder_name}' created successfully.")
                is_created = False
                number += 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_folder.py <file_name>")
    else:
        file_name = sys.argv[1]
        create_folder_with_file(file_name)
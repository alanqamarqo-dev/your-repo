import os


def read_text_file(filepath):
    if not os.path.exists(filepath):
        return f"File does not exist at {filepath}"

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return "File not found"
    except PermissionError:
        return "Permission denied to read the file"


if __name__ == "__main__":
    filepath = r"D:\AGL\README.txt"
    print(read_text_file(filepath))

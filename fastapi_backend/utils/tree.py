import pathlib


def list_files(startpath, indent=''):
    # Added '.idea' and '.vscode' to the ignore list
    ignore_list = {
        '.venv', '__pycache__', '.git', '.pytest_cache',
        '.pyc', '.idea', '.vscode', '.DS_Store'
    }

    path = pathlib.Path(startpath)

    # Filter out ignored items before sorting and printing
    items = [
        item for item in path.iterdir()
        if item.name not in ignore_list
    ]

    # Sort: Directories first, then files
    items.sort(key=lambda p: (not p.is_dir(), p.name.lower()))

    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "

        print(f"{indent}{connector}{item.name}")

        if item.is_dir():
            extension = "    " if is_last else "│   "
            list_files(item, indent + extension)


if __name__ == "__main__":
    root_name = pathlib.Path.cwd().name
    print(f"Project Structure for: {root_name}")
    list_files('.')
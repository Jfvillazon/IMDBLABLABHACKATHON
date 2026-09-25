from pathlib import Path


def analyze_architecture(repo_path: str):
    root = Path(repo_path)

    directories = [
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]

    entry_points = []

    possible_entry_points = {
        "main.py",
        "app.py",
        "server.py",
        "index.js",
        "main.js",
        "App.jsx"
    }

    for path in root.rglob("*"):
        if path.is_file() and path.name in possible_entry_points:
            entry_points.append(str(path.relative_to(root)))

    return {
        "directories": directories,
        "entry_points": entry_points
    }
def analyze_testing(files, root):
    findings = []

    test_files = [
        file
        for file in files
        if file.name.startswith("test_")
        or file.name.endswith("_test.py")
    ]

    python_source_files = [
        file
        for file in files
        if file.suffix == ".py"
        and "tests" not in file.parts
        and not file.name.startswith("test_")
    ]

    if python_source_files and not test_files:

        findings.append({
            "category": "testing",
            "severity": "high",
            "title": "No automated tests detected",
            "file": ".",
            "line": None,
            "description":
                "Python source files were found but no automated tests were detected.",
            "recommendation":
                "Add automated tests for important application behavior."
        })

    return findings
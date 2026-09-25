import ast


MAX_FUNCTION_LINES = 30


def analyze_quality(files, root):
    findings = []

    for file_path in files:

        if file_path.suffix != ".py":
            continue

        try:
            source = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.ExceptHandler):

                if node.type is None:

                    findings.append({
                        "category": "error_handling",
                        "severity": "medium",
                        "title": "Bare except clause",
                        "file": str(file_path.relative_to(root)),
                        "line": node.lineno,
                        "description":
                            "The code catches every exception without identifying the expected error.",
                        "recommendation":
                            "Catch specific exception types instead."
                    })

                elif (
                    isinstance(node.type, ast.Name)
                    and node.type.id == "Exception"
                ):

                    findings.append({
                        "category": "error_handling",
                        "severity": "medium",
                        "title": "Overly broad exception handling",
                        "file": str(file_path.relative_to(root)),
                        "line": node.lineno,
                        "description":
                            "The code catches Exception broadly.",
                        "recommendation":
                            "Catch the specific exceptions expected here."
                    })

            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            ):

                if hasattr(node, "end_lineno"):

                    length = node.end_lineno - node.lineno + 1

                    if length > MAX_FUNCTION_LINES:

                        findings.append({
                            "category": "maintainability",
                            "severity": "low",
                            "title": "Large function",
                            "file": str(file_path.relative_to(root)),
                            "line": node.lineno,
                            "description":
                                f"Function '{node.name}' spans {length} lines.",
                            "recommendation":
                                "Consider dividing this function into smaller responsibilities."
                        })

    return findings
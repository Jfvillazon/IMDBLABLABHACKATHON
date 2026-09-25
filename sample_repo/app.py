"""Entry point for a synthetic, intentionally flawed checkout demo.

This application is never imported or executed by RepoMedic's static scanner.
"""

from checkout import process_checkout


if __name__ == "__main__":
    print(process_checkout({"price": 12.50, "quantity": 2}))
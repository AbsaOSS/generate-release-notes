import os
import sys


def get_action_input(name: str) -> str:
    return os.getenv(f'INPUT_{name.replace("-", "_").upper()}', '')


def set_action_output(name: str, value: str, default_output_path: str = "default_output.txt"):
    output_file = os.getenv('GITHUB_OUTPUT', default_output_path)
    with open(output_file, 'a') as f:
        # Write the multiline output to the file
        f.write(f"{name}<<EOF\n")
        f.write(f"{value}")
        f.write(f"EOF\n")


def set_action_failed(message: str):
    print(f'::error::{message}')
    sys.exit(1)

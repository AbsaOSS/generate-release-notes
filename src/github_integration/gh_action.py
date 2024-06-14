import os
import sys


def get_input(name: str) -> str:
    # print all environment variables - keys only
    print(os.environ.keys())
    return os.getenv(f'{name.replace("-", "_").upper()}', '')


def set_output(name: str, value: str, default_output_path: str = "default_output.txt"):
    output_file = os.getenv('GITHUB_OUTPUT', default_output_path)
    with open(output_file, 'a') as f:
        f.write(f'{name}={value}\n')


def set_failed(message: str):
    print(f'::error::{message}')
    sys.exit(1)

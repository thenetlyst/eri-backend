import subprocess


def execute(command):

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=10,
    )
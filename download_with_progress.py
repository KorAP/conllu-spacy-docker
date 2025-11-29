#!/usr/bin/env python3
"""
Download spaCy model with progress bar
"""
import sys
import subprocess
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: download_with_progress.py MODEL_NAME")
        sys.exit(1)

    model_name = sys.argv[1]

    print(f"Downloading {model_name}...", file=sys.stderr)
    print("This may take several minutes depending on model size", file=sys.stderr)
    print("", file=sys.stderr)

    # Run spacy download with unbuffered output
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "spacy", "download", model_name, "--no-cache-dir"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    download_started = False

    for line in iter(process.stdout.readline, ''):
        if not line:
            break

        # Print the line
        print(line.rstrip(), file=sys.stderr)

        # Detect download progress
        if 'Downloading' in line and not download_started:
            download_started = True
            print("Download in progress...", file=sys.stderr)

        # Look for percentage or size indicators
        if '%' in line or 'MB' in line or 'KB' in line:
            # Extract and show progress
            match = re.search(r'(\d+)%', line)
            if match:
                percent = match.group(1)
                bar_length = 40
                filled = int(bar_length * int(percent) / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\rProgress: [{bar}] {percent}%", end='', file=sys.stderr)

    process.stdout.close()
    return_code = process.wait()

    if return_code != 0:
        print(f"\nError: Download failed with code {return_code}", file=sys.stderr)
        sys.exit(return_code)

    print("\n✓ Download complete!", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())

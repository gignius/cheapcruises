"""Standalone script to run scrapers manually"""
import asyncio
import sys

# Add current directory to path
sys.path.insert(0, '.')

from scheduler import run_scrapers_now


def safe_print(text):
    """Print with Unicode error handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'ignore').decode('ascii')
        print(ascii_text if ascii_text else "[Output contains unsupported characters]")


if __name__ == "__main__":
    safe_print("🚀 Running scrapers manually...")
    asyncio.run(run_scrapers_now())
    safe_print("✅ Done!")



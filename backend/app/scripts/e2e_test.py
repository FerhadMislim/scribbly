"""
End-to-end test script for the Scribbly API.
Run this script to test the full image generation flow:
- Upload artwork
- Generate styled image
- Poll for result

Usage:
    python -m scripts.e2e_test

Requires:
    - Docker services running (backend, postgres, redis, minio, celery)
    - Test image at ai-engine/output/flowers.jpeg
"""

import argparse
import sys
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8000"
TEST_IMAGE = Path(__file__).parent / "image.png"
TEST_USER = "test-user-e2e"
STYLE = "sketch"
DEFAULT_PROMPT = "flowers"


def upload_image(image_path: Path) -> str:
    """Upload an image and return the upload_id."""
    print(f"Uploading {image_path}...")

    with open(image_path, "rb") as f:
        response = requests.post(
            f"{API_BASE}/api/v1/artwork/upload",
            files={"file": (image_path.name, f, "image/jpeg")},
            headers={"X-User-Id": TEST_USER},
        )

    if response.status_code != 201:
        print(f"Upload failed: {response.status_code} - {response.text}")
        sys.exit(1)

    data = response.json()
    print(f"  upload_id: {data['upload_id']}")
    print(f"  preview_url: {data['preview_url'][:80]}...")
    return data["upload_id"]


def generate_image(upload_id: str, style: str, prompt: str) -> str:
    """Start image generation and return the task_id."""
    print(f"Generating image with style='{style}', prompt='{prompt}'...")

    response = requests.post(
        f"{API_BASE}/api/v1/generate/image",
        json={
            "upload_id": upload_id,
            "style_id": style,
            "prompt": prompt,
        },
        headers={"X-User-Id": TEST_USER},
    )

    if response.status_code != 202:
        print(f"Generate failed: {response.status_code} - {response.text}")
        sys.exit(1)

    data = response.json()
    print(f"  task_id: {data['task_id']}")
    print(f"  status: {data['status']}")
    return data["task_id"]


def poll_task(task_id: str, timeout: int = 300, interval: int = 5) -> dict:
    """Poll for task completion."""
    print(f"Polling for task {task_id}...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{API_BASE}/api/v1/tasks/{task_id}")

        if response.status_code != 200:
            print(f"Status check failed: {response.status_code}")
            time.sleep(interval)
            continue

        data = response.json()
        print(f"  status: {data['status']}")

        if data["status"] == "complete":
            print(f"  result_url: {data['result_url'][:80]}...")
            return data
        elif data["status"] == "failed":
            print(f"  error: {data['error']}")
            sys.exit(1)

        time.sleep(interval)

    print(f"Timeout after {timeout}s")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="E2E test for Scribbly API")
    parser.add_argument(
        "--image",
        type=Path,
        default=TEST_IMAGE,
        help="Path to test image",
    )
    parser.add_argument(
        "--style",
        type=str,
        default=STYLE,
        help="Style to apply",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        help="Prompt for generation",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Scribbly E2E Test")
    print("=" * 50)

    if not args.image.exists():
        print(f"Error: Image not found: {args.image}")
        sys.exit(1)

    upload_id = upload_image(args.image)
    task_id = generate_image(upload_id, args.style, args.prompt)
    result = poll_task(task_id, timeout=args.timeout)

    print("=" * 50)
    print("SUCCESS! Image generation complete.")
    print(f"Result URL: {result['result_url']}")
    print("=" * 50)


if __name__ == "__main__":
    main()

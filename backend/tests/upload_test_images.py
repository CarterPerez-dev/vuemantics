"""
Script to bulk upload test images to the API.
"""

import asyncio
import httpx
from pathlib import Path


API_BASE = "http://localhost:856/api"
EMAIL = "tester@gmail.com"
PASSWORD = "Test123!"  # noqa: S105

IMAGES = [
    "art1.jpg",
    "art2.jpg",
    "art3.jpg",
    "cat1.jpg",
    "cat2.jpg",
    "dog1.jpg",
    "dog2.jpg",
    "bird1.jpg",
    "bird2.jpg",
    "fish1.jpg",
    "fish2.jpg",
    "car1.jpg",
    "car2.jpg",
    "bicycle1.jpg",
    "bicycle2.jpg",
    "motorcycle1.jpg",
    "motorcycle2.jpg",
    "bus1.jpg",
    "bus2.jpg",
    "beach1.jpg",
    "beach2.jpg",
    "mountain1.jpg",
    "mountain2.jpg",
    "forest1.jpg",
    "forest2.jpg",
    "man1.jpg",
    "man2.jpg",
    "man3.jpg",
    "female1.jpg",
    "female2.jpg",
    "female3.jpg",
    "group1.jpg",
    "group2.jpg",
    "food1.jpg",
    "food2.jpg",
    "electronics1.jpg",
    "electronics2.jpg",
    "sunset1.jpg",
    "sunset2.jpg",
    "furniture1.jpg",
    "furniture2.jpg",
    "city1.jpg",
    "city2.jpg",
    "meme1.jpg",
    "meme2.jpg",
    "meme3.jpg",
    "website-screenshot.jpg",
    "tech-companies.jpg",
    "graphic1.jpg",
    "desktop.jpg",
    "linux-terminal.jpg",
    "generic-companies.jpg",
    "blank-blue.jpg",
    "blank-pink.jpg",
    "blank-red.jpg",
    "known-art1.jpg",
    "known-art2.jpg",
    "graphic2.jpg",
]

IMAGE_DIR = Path(__file__).parent / "images"


async def login(client: httpx.AsyncClient) -> str:
    response = await client.post(
        f"{API_BASE}/auth/token",
        data = {
            "username": EMAIL,
            "password": PASSWORD
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def upload_image(
    client: httpx.AsyncClient,
    token: str,
    image_path: Path
) -> bool:
    headers = {"Authorization": f"Bearer {token}"}

    with open(image_path, "rb") as f:
        files = {"file": (image_path.name, f, "image/jpeg")}
        response = await client.post(
            f"{API_BASE}/uploads",
            headers = headers,
            files = files,
            timeout = 30.0,
        )

    if response.status_code == 201:
        print(f"Uploaded: {image_path.name}")
        return True
    else:
        print(
            f"Failed: {image_path.name} - {response.status_code}: {response.text}"
        )
        return False


async def main():
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        token = await login(client)
        print(f"Got token: {token[:20]}...")

        success = 0
        failed = 0

        for image_name in IMAGES:
            image_path = IMAGE_DIR / image_name

            if not image_path.exists():
                print(f"Not found: {image_name}")
                failed += 1
                continue

            if await upload_image(client, token, image_path):
                success += 1
            else:
                failed += 1

            await asyncio.sleep(7)

        print(f"\nDone! Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(main())

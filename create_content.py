#!env python
from src.process import build_site_data
from src.media import download_images
from src.generate import build_site_content
import json

def main():
    videos, kwds = build_site_data()
    images = download_images(videos)
    build_site_content(videos, kwds, images)

    return videos, kwds, images


if __name__ == "__main__":
    main()


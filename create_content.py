from src.process import build_site_data, create_videos
from src.media import download_images
from src.generate import build_site_content


def main():
    data, kwds = build_site_data()
    videos = create_videos(data, kwds)
    images = download_images(videos)
    build_site_content(videos, kwds, images)

    return data, kwds, images


if __name__ == "__main__":
    main()


import shutil
import os
import logging
import numpy as np
import re

from . import *


def clean_content():
    articles_path = os.path.join(BASEDIR, 'content', 'videos')
    for item in os.listdir(articles_path):
        path = os.path.join(articles_path, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        print(f'Removed:    {path}')


def to_video_page(video, medias):
    out = f"""{video['title']}
{'#'*len(video['title'])}

:slug: {video['slug_web']}
:date: {video['created'].strftime('%Y-%m-%d')}
:tags: {';'.join(video['tags'])}
:summary: {video['summary']}"""

    if video['category'] is not np.NaN:
        out += f'\n:category: {video["category"]}'

    if video['authors'] is not np.NaN:
        out += f'\n:authors: {";".join(video["authors"])}'

#    if medias is not None and 'main_img' in medias:
#        out += f'\n:medias_main_img: {medias["main_img"]}'

    out += f'\n\n{video["description"]}\n'

    return out


def build_site_content(videos, keywords, images):
    clean_content()

    for video in videos:
        content = to_video_page(video, images.get(video['slug_fs'], None))
        if video['category'] is not np.NaN:
            filepath = os.path.join(BASEDIR, 'content', 'videos', video['category'], f"{video['slug_fs']}.rst")
        else:
            filepath = os.path.join(BASEDIR, 'content', 'videos', f"{video['slug_fs']}.rst")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'Wrote:   {filepath}')

    return


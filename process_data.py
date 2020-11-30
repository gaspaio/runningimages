import pandas as pd
import numpy as np
import gspread
from leven import levenshtein
import datetime as dt
import pycountry
import textwrap
import re
import shutil
import os

TAG_MIN_COUNT = 2

SUMMARY_LENGTH = 150

NAME_MAPS = {
    'events': {
        'diag': { 'name': 'La Diagonale des Fous' },
        'barkley': { 'name': 'The Barkley Marathons' },
        'ws100': { 'name': 'Western States 100' },
        'templiers': { 'name': 'Festival des Templiers' },
        'hardrock': { 'name': 'Hardrock 100' },
        'pct': { 'name': 'Pacific Crest Trail' },
        'bgr': { 'name': 'Bob Graham Round' },
        'at': { 'name': 'Appalachian Trail' },
        'mds': { 'name': 'Marathon des Sables' },
        'badwater': { 'name': 'Badwater 135' },
        'transcon': { 'name': 'US Transcontinental' },
        'leadville': { 'name': 'Leadville 100' },
        'gr20': {'name': 'GR 20'},
    }
}

LANG_MAP = {
    'fr': 'French',
    'en': 'English',
    'gr': 'Greek'
}

IMG_FORMATS = ['jpg']

def download_data():
    gc = gspread.service_account(filename='secrets/runningimages.key.json')
    sh = gc.open("Running Images")
    return pd.DataFrame(sh.sheet1.get_all_records())

def clean_data(orig_data):
    data = orig_data.copy()
    bool_cols = ['free_access', 'export']
    for col in bool_cols:
        errs = data[~data[col].isin(['yes', 'no'])]
        if not errs.empty:
            print(f'Found bad values in bool column {col}')
            print(errs)
            raise RuntimeError(f'Bad values in bool column {col}')
        data[col] = data[col].apply(lambda val: val == 'yes')

    data = data[data.export].copy().drop(['saw', 'export'], axis=1)

    # minimal data clean and type casting
    data = data.applymap(lambda x: x.strip() if type(x) is str else x)
    data['slug'] = data.slug.apply(lambda x: x.lower())
    data = data.replace('', np.nan)

    # verify
    non_empty_cols = ['id', 'slug', 'title', 'release_year', 'created', 'description', 'free_access']
    for col in non_empty_cols:
        errs = data[data[col].isna()]
        if not errs.empty:
            print(f'Found empty/wrong values in column {col}')
            print(errs)
            raise RuntimeError(f'Empty values in critical column {col}')

    unique_cols = ['id', 'slug', 'title']
    for col in unique_cols:
        errs = data[data[col].duplicated(keep=False)]
        if not errs.empty:
            print(f'Found duplicate values in unique column {col}')
            print(errs)
            raise RuntimeError(f'Duplicate values in unique column {col}')

    # validate release year
    if data.release_year.dtype is not np.dtype('int64'):
        raise RuntimeError(f'Invalid value(s) in release_year field. Column type is not int64')

    # parse duration
    def parse_duration(row):
        if row.duration is np.NaN:
            return row.duration
        try:
            t = dt.datetime.strptime(row.duration, "%H:%M:%S")
            return dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        except Exception as err:
            raise RuntimeError(f'Failed to parse duration for row.id == {row.id} ({row.duration}) - {err}')

    data['duration'] = data.apply(parse_duration, axis=1)

    # Parse date
    def parse_created(row):
        try:
            return dt.datetime.strptime(row.created, "%Y/%m/%d")
        except Exception as err:
            raise RuntimeError(f'Failed to parse created for row.id == {row.id} ({row.created}) - {err}')

    data['created'] = data.apply(parse_created, axis=1)

    # Split tag columns
    get_name = lambda col, label: NAME_MAPS.get(col, {}).get(label, {}).get('name', label)
    for colname in ['events', 'people', 'sponsors', 'production', 'direction']:
        data[colname] = data[colname].str.split(',').apply(lambda items: [get_name(colname, item.strip()) for item in np.unique(items)] if type(items) is list else items)

    # Lang & Country
    def country_name(idx, code):
        if code is np.NaN:
            return code
        cty = pycountry.countries.get(alpha_2=code)
        if cty is not None:
            return cty.name
        raise RuntimeError(f'Unknown country code in col id == {idx} ({code})')
    data['country'] = data.apply(lambda row: country_name(row.id, row.country), axis=1)

    def parse_lang(idx, lang):
        if lang is np.NaN:
            return lang
        if lang not in LANG_MAP:
            raise RuntimeError(f'Unknown language in col id == {idx} ({lang})')
        return LANG_MAP[lang]
    data['language'] = data.apply(lambda row: parse_lang(row.id, row.language), axis=1)

    # validate and clean slug.
    # regex: [a-z0-9\_]+
    # create 1 field: web_slug (convert _ to -]
    def build_web_slug(idx, slug):
        if re.match(r'^[0-9a-z\_]+$', slug) is None:
            raise RuntimeError(f'Invalid slug in col id == {idx} ({slug})')
        return slug.replace('_', '-')
    data['slug_web'] = data.apply(lambda row: build_web_slug(row.id, row.slug), axis=1)

    return data


def item_table(data, colname):
    items = pd.DataFrame(data[colname].dropna().explode().str.strip().value_counts())
    items.columns = ['counts']
    items['is_tag'] = items.counts.apply(lambda c: c >= TAG_MIN_COUNT)
    return items


def find_similar(items, similarity_threshold=3):
    itemnb = len(items)
    scores = [(items[i],items[j],levenshtein(items[i],items[j])) for i in range(itemnb) for j in range(i+1, itemnb)]
    return sorted([x for x in scores if x[2] <= similarity_threshold], key=lambda x: x[2])


def set_category(year):
    if year < 2000:
        return 'x-1999'
    elif year < 2005:
        return '2000-2004'
    elif year < 2010:
        return '2005-2009'
    elif year < 2015:
        return '2010-2014'
    else:
        return '2015-x'


def extract_keywords(data, similarity_threshold=3):
    out = {
        'events': item_table(data, 'events'),
        'people': item_table(data, 'people'),
        'sponsors': item_table(data, 'sponsors'),
        'production': item_table(data, 'production'),
        'direction': item_table(data, 'direction')
    }

    for k, items in out.items():
        similar = find_similar(items.index.to_list(), similarity_threshold)

        if len(similar):
            print(f'\n\nFound similar "{k}" keywords. You may want to review these:')
            for sim in similar:
                print(f'* {sim[2]}\t{sim[0]}\t{sim[1]}')

    out_final = {}
    for k, df in out.items():
        out_final[k] = df.to_dict('index')

    # Ensure we have no conflicting keywords
    # all_k = [name for vals in out_final.values() for name, info in vals.items() if info['is_tag']]



    return out_final


def create_articles(data, tag_sources):
    items = []

    for _, row in data.iterrows():
        item = {
            'id': row.id,
            'title': row.title,
            'slug_web': row.slug_web,
            'slug_fs': row.slug,
            'created': row.created,
            'release_year': row.release_year,
            'category': set_category(row.release_year),
            'duration': row.duration,
            'created': row.created,
            'production': row.production,
            'direction': row.direction,
            'sponsors': row.sponsors,
            'people': row.people,
            'events': row.events,
            'description': row.description,
            'summary': textwrap.shorten(row.description, width=SUMMARY_LENGTH, placeholder="..."),
            'free_access': row.free_access,
            'language': row.language,
            'country': row. country
        }

        item['authors'] = item['direction']

        # build tags
        item['tags'] = []
        for name, info in tag_sources.items():
            if item[name] is np.NaN:
                continue
            item['tags'] += [elem for elem in item[name] if info.get(elem, {}).get('is_tag', False)]

        items.append(item)

    return items


def generate_site_data():
    data = download_data()
    data = clean_data(data)
    keywords = extract_keywords(data)
    videos = create_articles(data, keywords)

    return videos, keywords


def generate_video_images(videos, keywords):
    medias = {}
    for video in videos:
        # Support multiple file formats
        path = None
        for img_format in IMG_FORMATS:
            path = f'images/{video["slug_fs"]}.{img_format}'
            if os.path.isfile(f'content/{path}'):
                break
            path = None

        if path is not None:
            medias[video['slug_fs']] = {
                'main_img': path
            }
    return medias


def clean_content():
    for item in os.listdir('content/videos'):
        path = f'content/videos/{item}'
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        print(f'Removed:    {path}')


def to_video_page(video, medias):

    non_empty_cols = ['id', 'slug', 'title', 'release_year', 'created', 'description', 'free_access']

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

    if medias is not None and 'main_img' in medias:
        out += f'\n:medias_main_img: {medias["main_img"]}'

    out += f'\n\n{video["description"]}\n'

    return out

def generate_site_content(videos, keywords):
    clean_content()
    medias = generate_video_images(videos, keywords)

    for video in videos:
        content = to_video_page(video, medias.get(video['slug_fs'], None))
        filepath = f"content/videos/{video['category']}/{video['slug_fs']}.rst" if video['category'] is not np.NaN else f"content/videos/{video['slug_fs']}.rst"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'Wrote:   {filepath}')

    return

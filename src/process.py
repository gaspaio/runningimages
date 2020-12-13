import pyyoutube
import gspread
import pandas as pd
from leven import levenshtein
import pycountry
import re
import os
import numpy as np
import datetime as dt
import textwrap

from . import *

def download_gspread():
    gc = gspread.service_account(filename=os.path.join(BASEDIR, 'secrets', 'runningimages.key.json'))
    sh = gc.open("Running Images")
    return pd.DataFrame(sh.sheet1.get_all_records())


def validate_non_empty(df, colname):
    errs = df[df[colname].isna()]
    if not errs.empty:
        print(f'Found empty/wrong values in column {colname}')
        print(errs)
        raise RuntimeError(f'Empty values in critical column {colname}')


def validate_unique(df, colname):
    errs = df[df[colname].duplicated(keep=False)]
    if not errs.empty:
        print(f'Found duplicate values in unique column {col}')
        print(errs)
        raise RuntimeError(f'Duplicate values in unique column {col}')


def validate_is_yesno(df, colname):
    errs = df[~df[colname].isin(['yes', 'no'])]
    if not errs.empty:
        print(f'Found bad values in bool column {col}')
        print(errs)
        raise RuntimeError(f'Bad values in bool column {col}')


def clean_gspread_data(orig_data):

    data = orig_data.copy()

    # minimal data clean and type casting
    data = data.applymap(lambda x: x.strip() if type(x) is str else x)
    data = data.replace('', np.nan)

    # Drop rows not for export
    validate_is_yesno(data, 'export')
    data = data[data.export == 'yes']

    # Drop cols not for export
    data = data.drop(['saw', 'export'], axis=1)

    # Col id
    validate_non_empty(data, 'id')
    validate_unique(data, 'id')

    # Col title
    validate_non_empty(data, 'title')
    validate_unique(data, 'title')

    # Col release_year
    validate_non_empty(data, 'release_year')
    if data.release_year.dtype is not np.dtype('int64'):
        raise RuntimeError(f'Invalid value(s) in release_year field. Column type is not int64')

    # Col slug
    validate_non_empty(data, 'slug')
    data['slug'] = data.slug.apply(lambda x: x.lower())
    validate_unique(data, 'slug')
    def build_web_slug(idx, slug):
        if re.match(r'^[0-9a-z\_]+$', slug) is None:
            raise RuntimeError(f'Invalid slug in col id == {idx} ({slug})')
        return slug.replace('_', '-')
    data['slug_web'] = data.apply(lambda row: build_web_slug(row.id, row.slug), axis=1)

    # Col created
    validate_non_empty(data, 'created')
    def parse_created(row):
        try:
            return dt.datetime.strptime(row.created, "%Y/%m/%d")
        except Exception as err:
            raise RuntimeError(f'Failed to parse created for row.id == {row.id} ({row.created}) - {err}')
    data['created'] = data.apply(parse_created, axis=1)

    # Col duration
    def parse_duration(row):
        if row.duration is np.NaN:
            return row.duration
        try:
            t = dt.datetime.strptime(row.duration, "%H:%M:%S")
            return dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        except Exception as err:
            raise RuntimeError(f'Failed to parse duration for row.id == {row.id} ({row.duration}) - {err}')
    data['duration'] = data.apply(parse_duration, axis=1)

    # Col language
    def parse_lang(idx, lang):
        if lang is np.NaN:
            return lang
        if lang not in LANG_MAP:
            raise RuntimeError(f'Unknown language in col id == {idx} ({lang})')
        return LANG_MAP[lang]
    data['language'] = data.apply(lambda row: parse_lang(row.id, row.language), axis=1)

    # Col country
    def country_name(idx, code):
        if code is np.NaN:
            return code
        cty = pycountry.countries.get(alpha_2=code)
        if cty is not None:
            return cty.name
        raise RuntimeError(f'Unknown country code in col id == {idx} ({code})')
    data['country'] = data.apply(lambda row: country_name(row.id, row.country), axis=1)

    # Cols direction, production, events, sponsors, people
    # Split into items
    get_name = lambda col, label: NAME_MAPS.get(col, {}).get(label, {}).get('name', label)
    for colname in ['events', 'people', 'sponsors', 'production', 'direction']:
        data[colname] = data[colname].str.split(',').apply(lambda items: [get_name(colname, item.strip()) for item in np.unique(items)] if type(items) is list else items)

    # Col description
    validate_non_empty(data, 'description')

    # TODO Warn if no video link in video

    # Col free access
    validate_non_empty(data, 'free_access')
    data['free_access'] = data['free_access'].apply(lambda val: val == 'yes')

    return data


def extract_keywords(data, similarity_threshold=3):
    def item_table(data, colname):
        items = pd.DataFrame(data[colname].dropna().explode().str.strip().value_counts())
        items.columns = ['counts']
        items['is_tag'] = items.counts.apply(lambda c: c >= TAG_MIN_COUNT)
        return items

    def find_similar(items, similarity_threshold=3):
        itemnb = len(items)
        scores = [(items[i],items[j],levenshtein(items[i],items[j])) for i in range(itemnb) for j in range(i+1, itemnb)]
        return sorted([x for x in scores if x[2] <= similarity_threshold], key=lambda x: x[2])

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


def create_videos(data, keywords):
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
            'country': row.country,
            'link_trailer': row.link_trailer,
            'link_stream': row.link_stream,
            'link_official': row.link_official
        }

        item['authors'] = item['direction']

        # build tags
        item['tags'] = []
        for name, info in keywords.items():
            if item[name] is np.NaN:
                continue
            item['tags'] += [elem for elem in item[name] if info.get(elem, {}).get('is_tag', False)]

        items.append(item)

    return items


def build_site_data():
    data = download_gspread()
    data = clean_gspread_data(data)
    keywords = extract_keywords(data)
    return data, keywords

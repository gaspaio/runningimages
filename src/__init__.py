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

TAG_SEPARATOR = ', '

BASEDIR = os.path.join(os.path.dirname(__file__), '..')


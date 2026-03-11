import os
from flask import request
from feffery_dash_utils.i18n_utils import Translator
from functools import partial

_here = os.path.dirname(os.path.abspath(__file__))
_translations_dir = os.path.join(_here, 'translations')
_topic_locales_dir = os.path.join(_translations_dir, 'topic_locales')

translator = Translator(
    translations=[
        os.path.join(_translations_dir, 'locales.json'),
        *[os.path.join(_topic_locales_dir, path) for path in os.listdir(_topic_locales_dir)],
    ],
    force_check_content_translator=False,
)

t__default = partial(translator.t)
t__access = partial(translator.t, locale_topic='access')
t__dashboard = partial(translator.t, locale_topic='dashboard')
t__person = partial(translator.t, locale_topic='person')
t__notification = partial(translator.t, locale_topic='notification')
t__task = partial(translator.t, locale_topic='task')
t__setting = partial(translator.t, locale_topic='setting')
t__other = partial(translator.t, locale_topic='other')
# -*- coding: utf8 -*-
# create_author: (heyue@g-i.asia)
import re
from googletrans import Translator, LANGUAGES

# RegExp
empty_str = re.compile('^\s*$', re.I | re.M)

### =====  Translate Nodes [googletrans module]  ===== ###
translator = Translator()


def translate(prompt, srcTrans=None, toTrans=None):
    if not srcTrans:
        srcTrans = 'auto'

    if not toTrans:
        toTrans = 'en'

    translate_text_prompt = ''
    if prompt and not empty_str.match(prompt):
        translate_text_prompt = translator.translate(prompt, src=srcTrans, dest=toTrans)

    return translate_text_prompt.text if hasattr(translate_text_prompt, 'text') else ''
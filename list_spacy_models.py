#!/usr/bin/env python3
"""
Display available spaCy models
Uses a curated list of current models since spacy.io/models is JavaScript-rendered
"""
import sys

def get_models():
    """Get list of available models organized by language"""
    # Curated list of spaCy models (updated 2025-01)
    # Based on https://spacy.io/models and https://github.com/explosion/spacy-models
    return {
        'ca': ['ca_core_news_sm', 'ca_core_news_md', 'ca_core_news_lg', 'ca_core_news_trf'],
        'zh': ['zh_core_web_sm', 'zh_core_web_md', 'zh_core_web_lg', 'zh_core_web_trf'],
        'hr': ['hr_core_news_sm', 'hr_core_news_md', 'hr_core_news_lg'],
        'da': ['da_core_news_sm', 'da_core_news_md', 'da_core_news_lg', 'da_core_news_trf'],
        'nl': ['nl_core_news_sm', 'nl_core_news_md', 'nl_core_news_lg'],
        'en': ['en_core_web_sm', 'en_core_web_md', 'en_core_web_lg', 'en_core_web_trf'],
        'fi': ['fi_core_news_sm', 'fi_core_news_md', 'fi_core_news_lg'],
        'fr': ['fr_core_news_sm', 'fr_core_news_md', 'fr_core_news_lg', 'fr_dep_news_trf'],
        'de': ['de_core_news_sm', 'de_core_news_md', 'de_core_news_lg'],
        'el': ['el_core_news_sm', 'el_core_news_md', 'el_core_news_lg'],
        'it': ['it_core_news_sm', 'it_core_news_md', 'it_core_news_lg'],
        'ja': ['ja_core_news_sm', 'ja_core_news_md', 'ja_core_news_lg', 'ja_core_news_trf'],
        'ko': ['ko_core_news_sm', 'ko_core_news_md', 'ko_core_news_lg'],
        'lt': ['lt_core_news_sm', 'lt_core_news_md', 'lt_core_news_lg'],
        'mk': ['mk_core_news_sm', 'mk_core_news_md', 'mk_core_news_lg'],
        'nb': ['nb_core_news_sm', 'nb_core_news_md', 'nb_core_news_lg'],
        'pl': ['pl_core_news_sm', 'pl_core_news_md', 'pl_core_news_lg'],
        'pt': ['pt_core_news_sm', 'pt_core_news_md', 'pt_core_news_lg'],
        'ro': ['ro_core_news_sm', 'ro_core_news_md', 'ro_core_news_lg'],
        'ru': ['ru_core_news_sm', 'ru_core_news_md', 'ru_core_news_lg'],
        'es': ['es_core_news_sm', 'es_core_news_md', 'es_core_news_lg'],
        'sv': ['sv_core_news_sm', 'sv_core_news_md', 'sv_core_news_lg'],
        'uk': ['uk_core_news_sm', 'uk_core_news_md', 'uk_core_news_lg', 'uk_core_news_trf'],
    }

def get_language_name(code):
    """Get full language name from code"""
    languages = {
        'ca': 'Catalan',
        'zh': 'Chinese',
        'hr': 'Croatian',
        'da': 'Danish',
        'nl': 'Dutch',
        'en': 'English',
        'fi': 'Finnish',
        'fr': 'French',
        'de': 'German',
        'el': 'Greek',
        'it': 'Italian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'lt': 'Lithuanian',
        'mk': 'Macedonian',
        'nb': 'Norwegian Bokmål',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ro': 'Romanian',
        'ru': 'Russian',
        'es': 'Spanish',
        'sv': 'Swedish',
        'uk': 'Ukrainian',
    }
    return languages.get(code, code.upper())

def display_models(by_language):
    """Display models grouped by language"""
    # Priority languages to show first
    priority = ['de', 'en', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'ru', 'zh', 'ja']

    # Show priority languages first
    for lang_code in priority:
        if lang_code in by_language:
            lang_name = get_language_name(lang_code)
            print(f"\n{lang_name}:", file=sys.stderr)
            for model in sorted(by_language[lang_code]):
                # Estimate size based on suffix
                if model.endswith('_sm'):
                    size = "~15MB"
                elif model.endswith('_md'):
                    size = "~100MB"
                elif model.endswith('_lg'):
                    size = "~560MB"
                elif model.endswith('_trf'):
                    size = "~500MB (transformer)"
                else:
                    size = ""

                default = " (default)" if model == "de_core_news_lg" else ""
                print(f"  {model:30} {size}{default}", file=sys.stderr)

    # Show remaining languages
    remaining = sorted([code for code in by_language.keys() if code not in priority])
    if remaining:
        print(f"\nOther languages:", file=sys.stderr)
        for lang_code in remaining:
            lang_name = get_language_name(lang_code)
            models = ", ".join([m.split('_')[-1] for m in sorted(by_language[lang_code])])
            print(f"  {lang_name}: {models}", file=sys.stderr)

def main():
    print("=== Available spaCy Models ===\n", file=sys.stderr)

    by_language = get_models()
    display_models(by_language)

    print(f"\n\nTotal: {sum(len(models) for models in by_language.values())} models across {len(by_language)} languages", file=sys.stderr)
    print("\nFor complete details and latest updates, visit: https://spacy.io/models", file=sys.stderr)
    print("\nUsage: docker run --rm -i korap/conllu-spacy -m MODEL_NAME < input.conllu", file=sys.stderr)

if __name__ == "__main__":
    main()

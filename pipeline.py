"""
Pipeline for text processing implementation
"""
from pathlib import Path
import re

import pymorphy2
from pymystem3 import Mystem

from constants import ASSETS_PATH
from core_utils.article import Article

class EmptyDirectoryError(Exception):
    """
    No data to process
    """


class InconsistentDatasetError(Exception):
    """
    Corrupt data:
        - numeration is expected to start from 1 and to be continuous
        - a number of text files must be equal to the number of meta files
        - text files must not be empty
    """


class MorphologicalToken:
    """
    Stores language params for each processed token
    """

    def __init__(self, original_word):
        self.original_word = original_word
        self.normalized_form = ''
        self.tags_mystem = ''
        self.tags_pymorphy = ''

    def get_cleaned(self):
        """
        Returns lowercased original form of a token
        """
        return self.original_word.lower()

    def get_single_tagged(self):
        """
        Returns normalized lemma with MyStem tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>'

    def get_multiple_tagged(self):
        """
        Returns normalized lemma with PyMorphy tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>({self.tags_pymorphy})'


class CorpusManager:
    """
    Works with articles and stores them
    """

    def __init__(self, path_to_raw_txt_data: str):
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self._storage = {}
        self._scan_dataset()

    def _scan_dataset(self):
        """
        Register each dataset entry
        """
        used_ids = []

        for path in Path(self.path_to_raw_txt_data).iterdir():
            match = re.match(r'(\d+)_\w+\.\w+', path.name)
            article_id = int(match.group(1))

            if article_id not in used_ids:
                self._storage[article_id] = Article(url=None, article_id=article_id)

            used_ids.append(article_id)

    def get_articles(self):
        """
        Returns storage params
        """
        return self._storage


class TextProcessingPipeline:
    """
    Process articles from corpus manager
    """

    def __init__(self, corpus_manager: CorpusManager):
        self.corpus_manager = corpus_manager

    def run(self):
        """
        Runs pipeline process scenario
        """
        articles = self.corpus_manager.get_articles().values()

        for article in articles:
            processed_tokens = self._process(article.get_raw_text())

            tokens_cleaned = []
            tokens_single_tagged = []
            tokens_multi_tagged = []

            for processed_token in processed_tokens:
                tokens_cleaned.append(processed_token.get_cleaned())
                tokens_single_tagged.append(processed_token.get_single_tagged())
                tokens_multi_tagged.append(processed_token.get_multiple_tagged())

            article.save_as(' '.join(tokens_cleaned), 'cleaned')
            article.save_as(' '.join(tokens_single_tagged), 'single_tagged')
            article.save_as(' '.join(tokens_multi_tagged), 'multiple_tagged')

    def _process(self, raw_text: str):
        """
        Processes each token and creates MorphToken class instance
        """
        result = Mystem().analyze(raw_text)
        morph = pymorphy2.MorphAnalyzer()

        morph_tokens = []

        for token in result:
            if not token.get('analysis') or not token['analysis'][0].get('lex') \
                    or not token['analysis'][0].get('gr'):
                continue

            morphological_token = MorphologicalToken(original_word=token['text'])
            morphological_token.normalized_form = token['analysis'][0]['lex']
            morphological_token.tags_mystem = token['analysis'][0]['gr']
            morphological_token.tags_pymorphy = morph.parse(token['text'])[0].tag
            morph_tokens.append(morphological_token)

        return morph_tokens


def validate_dataset(path_to_validate):
    """
    Validates folder with assets
    """
    path = Path(path_to_validate)
    if not path.exists():
        raise FileNotFoundError

    if not path.is_dir():
        raise NotADirectoryError

    all_article_ids = []

    for file in path.glob("*.txt"):
        with open(file, 'r', encoding='utf-8') as text_file:
            text = text_file.read()
        raw_data = list(path.glob('*_raw.txt'))
        meta_data = list(path.glob('*_meta.json'))

        if not len(meta_data) == len(raw_data):
            raise InconsistentDatasetError
        if not text:
            raise InconsistentDatasetError

        name_pattern = re.match(r'\d+', file.name)
        if not name_pattern:
            raise InconsistentDatasetError

        pattern = re.match(r'\d+', file.name)
        article_id = int(pattern.group(0))
        all_article_ids.append(article_id)

    if not all_article_ids:
        raise EmptyDirectoryError

    previous_article_id = 0
    sorted_all_ids = sorted(all_article_ids)
    for article_id in sorted_all_ids:
        if article_id - previous_article_id > 1:
            raise InconsistentDatasetError
        previous_article_id = article_id

    if sorted_all_ids[0] != 1:
        raise InconsistentDatasetError


def main():
    # YOUR CODE HERE
    pass
    validate_dataset(ASSETS_PATH)
    corpus_manager = CorpusManager(path_to_raw_txt_data=ASSETS_PATH)
    pipeline = TextProcessingPipeline(corpus_manager=corpus_manager)
    pipeline.run()


if __name__ == "__main__":
    main()

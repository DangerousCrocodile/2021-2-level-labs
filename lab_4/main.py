"""
Lab 4
Language generation algorithm based on language profiles
"""

from typing import Tuple
from lab_4.storage import Storage
from lab_4.language_profile import LanguageProfile
import re


# 4
def tokenize_by_letters(text: str) -> Tuple or int:
    """
    Tokenizes given sequence by letters
    """
    if not isinstance(text, str):
        return -1
    new_text = []
    text = text.lower()
    for letter in text:
        if letter.isalpha() or letter.isspace():
            new_text.append(letter)
    new_text = "".join(new_text)
    words = []
    for word in new_text.split():
        letters = ['_']
        for symbol in word:
            letters.append(symbol)
        letters.append("_")
        words.append(tuple(letters))
    return tuple(words)


# 4
class LetterStorage(Storage):
    """
    Stores letters and their ids
    """

    def update(self, elements: tuple) -> int:
        """
        Fills a storage by letters from the tuple
        :param elements: a tuple of tuples of letters
        :return: 0 if succeeds, -1 if not
        """
        if not isinstance(elements, tuple):
            return -1
        for token in elements:
            for letter in token:
                self._put(letter)
        return 0

    def get_letter_count(self) -> int:
        """
        Gets the number of letters in the storage
        """
        if not self.storage:
            return -1
        return len(self.storage)


# 4
def encode_corpus(storage: LetterStorage, corpus: tuple) -> tuple:
    """
    Encodes corpus by replacing letters with their ids
    :param storage: an instance of the LetterStorage class
    :param corpus: a tuple of tuples
    :return: a tuple of the encoded letters
    """
    if not isinstance(storage, LetterStorage) or \
            not isinstance(corpus, tuple):
        return ()
    encoded_corpus = []
    for token in corpus:
        encoded_token = []
        for letter in token:
            encoded_token.append(storage.get_id(letter))
        encoded_corpus.append(tuple(encoded_token))
    return tuple(encoded_corpus)


# 4
def decode_sentence(storage: LetterStorage, sentence: tuple) -> tuple:
    """
    Decodes sentence by replacing letters with their ids
    :param storage: an instance of the LetterStorage class
    :param sentence: a tuple of tuples-encoded words
    :return: a tuple of the decoded sentence
    """
    if not isinstance(storage, LetterStorage) or \
            not isinstance(sentence, tuple):
        return ()
    decoded_sentence = []
    for token in sentence:
        decoded_token = []
        for letter in token:
            decoded_token.append(storage.get_element(letter))
        decoded_sentence.append(tuple(decoded_token))
    return tuple(decoded_sentence)


# 6
class NGramTextGenerator:
    """
    Language model for basic text generation
    """

    def __init__(self, language_profile: LanguageProfile):
        self.profile = language_profile
        self._used_n_grams = []

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter from the most
            frequent ngram corresponding to the context given.
        """
        if not isinstance(context, tuple) or \
                len(context) + 1 not in [trie.size for trie in self.profile.tries]:
            return -1
        variants = {}
        variant = ()
        for trie in self.profile.tries:
            if len(context) + 1 == trie.size:
                for n_gram, freq in trie.n_gram_frequencies.items():
                    if self._used_n_grams == list(trie.n_gram_frequencies.keys()):
                        self._used_n_grams = []
                    if n_gram[:len(context)] == context and n_gram not in self._used_n_grams:
                        variants[n_gram] = freq
                if len(variants.keys()) == 0:
                    variant = sorted(trie.n_gram_frequencies, key=trie.n_gram_frequencies.get, reverse=True)[0]
                else:
                    variant = sorted(variants, key=variants.get, reverse=True)[0]
                    self._used_n_grams.append(variant)
        return variant[-1]

    def _generate_word(self, context: tuple, word_max_length=15) -> tuple:
        """
        Generates full word for the context given.
        """
        if not isinstance(context, tuple) or \
                not isinstance(word_max_length, int):
            return ()
        word = list(context)
        if len(word) >= word_max_length:
            word.append(self.profile.storage.get_special_token_id())
        else:
            while len(word) < word_max_length:
                letter = self._generate_letter(context)
                word.append(letter)
                if letter == self.profile.storage.get_special_token_id():
                    break
                context = tuple(word[-1:])
                if len(word) == word_max_length:
                    word.append(self.profile.storage.get_special_token_id())
        return tuple(word)

    def generate_sentence(self, context: tuple, word_limit: int) -> tuple:
        """
        Generates full sentence with fixed number of words given.
        """
        if not isinstance(context, tuple) or \
                not isinstance(word_limit, int):
            return ()
        sentence = []
        while len(sentence) < word_limit:
            word = self._generate_word(context)
            sentence.append(word)
            context = tuple(word[-1:])
        return tuple(sentence)

    def generate_decoded_sentence(self, context: tuple, word_limit: int) -> str:
        """
        Generates full sentence and decodes it
        """
        if not isinstance(context, tuple) or \
                not isinstance(word_limit, int):
            return ""
        strange_sentence = ""
        sentence = self.generate_sentence(context, word_limit)
        for word in sentence:
            for letter in word:
                strange_sentence += self.profile.storage.get_element(letter)
        result = strange_sentence.replace("__", " ").replace("_", "").capitalize()
        return result + "."


# 6
def translate_sentence_to_plain_text(decoded_corpus: tuple) -> str:
    """
    Converts decoded sentence into the string sequence
    """
    if not isinstance(decoded_corpus, tuple) or not decoded_corpus:
        return ""
    strange_text = ""
    for word in decoded_corpus:
        for symbol in word:
            strange_text += str(symbol)
    text = strange_text.replace("__", " ").replace("_", "").capitalize()
    return text + "."


# 8
class LikelihoodBasedTextGenerator(NGramTextGenerator):
    """
    Language model for likelihood based text generation
    """

    def _calculate_maximum_likelihood(self, letter: int, context: tuple) -> float:
        """
        Calculates maximum likelihood for a given letter
        :param letter: a letter given
        :param context: a context for the letter given
        :return: float number, that indicates maximum likelihood
        """
        if not isinstance(letter, int) or \
                not isinstance(context, tuple) or \
                len(context) + 1 not in [trie.size for trie in self.profile.tries] or \
                len(context) == 0:
            return -1
        variant = context + (letter,)
        all_n_grams = {}
        for trie in self.profile.tries:
            if trie.size == len(variant):
                for n_gram, freq in trie.n_gram_frequencies.items():
                    if n_gram[:len(context)] == context:
                        all_n_grams[n_gram] = freq
                if not all_n_grams:
                    return 0.0
        all_n_grams_freq = sum(all_n_grams.values())
        variant_freq = all_n_grams[variant]
        return variant_freq/all_n_grams_freq

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter with highest
            maximum likelihood frequency.
        """
        if not isinstance(context, tuple) or \
                len(context) + 1 not in [trie.size for trie in self.profile.tries] or \
                len(context) < 1:
            return -1
        all_n_grams = {}
        for trie in self.profile.tries:
            if trie.size == len(context) + 1:
                for n_gram, freq in trie.n_gram_frequencies.items():
                    if n_gram[:len(context)] == context:
                        all_n_grams[n_gram] = self._calculate_maximum_likelihood(n_gram[-1],
                                                                                 context)
        if all_n_grams:
            variant = sorted(all_n_grams, key=all_n_grams.get, reverse=True)[0][-1]
            return variant
        else:
            for trie in self.profile.tries:
                if trie.size == 1:
                    variant = sorted(trie.n_gram_frequencies,
                                     key=trie.n_gram_frequencies.get, reverse=True)[0][0]
                    return variant


# 10
class BackOffGenerator(NGramTextGenerator):
    """
    Language model for back-off based text generation
    """

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter with highest
            available frequency for the corresponding context.
            if no context can be found, reduces the context size by 1.
        """
        pass


# 10
class PublicLanguageProfile(LanguageProfile):
    """
    Language Profile to work with public language profiles
    """

    def open(self, file_name: str) -> int:
        """
        Opens public profile and adapts it.
        :return: o if succeeds, 1 otherwise
        """
        pass

import os
import re

from numpy import argmax
from nltk.tokenize import wordpunct_tokenize

from cltk.corpus.utils.importer import CLTK_DATA_DIR

class OldEnglishDictioraryLemmatizer(object):
	"""Implementation of a lemmatizer for Old English based on a dictionary of lemmas and forms.
	Since a given form may map to multiple lemmas, a corpus-based frequency disambiguator is employed."""

	def __init__(self):
		self._load_forms_and_lemmas()
		self._load_type_counts()

	def _load_forms_and_lemmas(self):
		"""Load the dictionary of lemmas and forms from the OE models repository."""

		rel_path = os.path.join(CLTK_DATA_DIR,
                                'old_english',
                                'model',
                                'old_english_models_cltk',
                                'data',
                                'oe.lemmas')
		path = os.path.expanduser(rel_path)

		self.lemma_dict = {}

		with open(path, 'r') as infile:
			lines = infile.read().splitlines()
			for line in lines:
				forms = line.split('\t')
				
				lemma = forms[0]
				for form_seq in forms:
					indiv_forms = form_seq.split(',')
					for form in indiv_forms:
						form = form.lower()
						lemma_list = self.lemma_dict.get(form, [])
						lemma_list.append(lemma)
						self.lemma_dict[form] = lemma_list

		for form in self.lemma_dict.keys():
			self.lemma_dict[form] = list(set(self.lemma_dict[form]))


	def _load_type_counts(self):
		"""Load the table of frequency counts of word forms."""

		rel_path = os.path.join(CLTK_DATA_DIR,
                                'old_english',
                                'model',
                                'old_english_models_cltk',
                                'data',
                                'oe.counts')
		path = os.path.expanduser(rel_path)

		self.type_counts = {}

		with open(path, 'r') as infile:
			lines = infile.read().splitlines()
			for line in lines:
				count, word = line.split()
				self.type_counts[word] = count


	def lemmatize_token(self, token, best_guess=True):
		"""Lemmatize a single token.  If best_guess is true, then take the most frequent lemma when a form 
		has multiple possible lemmatizations.  If the form is not found, just return it.
		If best_guess is false, then always return the full set of possible lemmas, or None if none found.
		"""

		lemmas = self.lemma_dict.get(token.lower(), None)

		if best_guess == True:
			if lemmas == None:
				lemma = token
			elif len(lemmas) > 1:
				counts = [self.type_counts[word] for word in lemmas]
				lemma = lemmas[argmax(counts)]
			else:
				lemma = lemmas[0]
		else:
			lemma = [] if lemmas == None else lemmas

		return(token, lemma)

	def lemmatize(self, text, best_guess=True):
		"""Lemmatize all tokens in a string or a list.  A string is first tokenized using punkt.
		Throw a type error if the input is neither a string nor a list.
		"""
		if isinstance(text, str):
			tokens = wordpunct_tokenize(text)
		elif isinstance(text, list):
			tokens= text
		else:
			raise TypeError("lemmatize only works with strings or lists of string tokens.")

		return [self.lemmatize_token(token, best_guess) for token in tokens]

	def evaluate(self, filename):
		"""Runs the lemmatize over the contents of the file, counting the proportion of unfound lemmas."""
		with open(filename, 'r') as infile:
			lines = infile.read().splitlines()

			lemma_count = 0
			token_count = 0

			for line in lines:
				line = re.sub(r'[.,!?:;0-9]', ' ', line)
				lemmas = [lemma for (_, lemma) in self.lemmatize(line, best_guess=False)]

				token_count += len(lemmas)
				lemma_count += len(lemmas) - lemmas.count([])

			return lemma_count/token_count



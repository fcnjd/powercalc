#!/usr/bin/env python

_current_language = 'de'

_translations = {
	'de': {
		'title': 'Wissenschaftlicher Rechner',
		'input_label': 'Eingabe',
		'output_label': 'Ergebnis',
		'index_title': 'Index',
		'menu_file': 'Datei',
		'menu_exit': 'Beenden',
		'menu_language': 'Sprache',
		'menu_english': 'Englisch',
		'menu_german': 'Deutsch',
		'index_message': 'Wähle ein Element aus dem Index, um es in den Ausdruck einzufügen',
	},
	'en': {
		'title': 'Scientific Calculator',
		'input_label': 'Input',
		'output_label': 'Output',
		'index_title': 'Index',
		'menu_file': 'File',
		'menu_exit': 'Exit',
		'menu_language': 'Language',
		'menu_english': 'English',
		'menu_german': 'German',
		'index_message': 'Select an item to add to the expression',
	}
}

def set_language(lang):
	global _current_language
	if lang in _translations:
		_current_language = lang

def get_language():
	return _current_language

def translate(key):
	return _translations.get(_current_language, {}).get(key, key)



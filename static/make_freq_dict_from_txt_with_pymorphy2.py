# -*- coding: utf-8 -*-
'''
INPUT: List of txt files you wish to read
OUTPUT: tab delimited text file containing words in order
        frequency of appearance

TO-DO: 
 - Make files open in new folders
 - Output 20 word list to anki compatible deck 
 - Steal a sample sentence from the text for each deck
'''

'''
Steps
1.) Open files in for loop
2.) Parse through each word 
   * Check if in dictionary (and/or conjugation variants are there) 
   * add to master dictionary or += 1

3.) Sort dictionary by frequency
4.) export to file

UNICODE_NOTE: All operations within the program happen in unicode. All output to
files should occurr in bytes 

'''
import string
from collections import defaultdict
import operator
import re
import os
import pymorphy2

#Files in utf-8 format

morph = pymorphy2.MorphAnalyzer()

def sanitize_text(text):
   '''Removes punctuation and whitespace characters from Russian text
   '''
   original_text = text.strip()
   #make everything lowercase
   sanitized_text = original_text.decode('utf-8').lower()
   #define punctuation marks and remove them
   punctuation = string.punctuation.decode('utf-8') + '«…»—“'.decode('utf-8')
   for character in punctuation:
      sanitized_text = sanitized_text.replace(character, '')
   return sanitized_text


def make_freq_dict(sanitized_txt):
   '''Input: text input that has had punctuation and whitespace characters removed.
   Output: an unsorted dictionary of word frequency
   ''' 
   freq_dict = defaultdict(int)
   #print 'Text type freq_dict: ', type(txt)
   words = sanitized_txt.split()
   #print 'all words:', words
   for word in words:
      lemma = lemmatize(word)
      #print type(word)
      #print word
      freq_dict[lemma] += 1
   return freq_dict

def lemmatize(word):
   '''Input: utf-8 word,
   Output: The lemmatized version of the source word.
   Example: Стали would output: стать
   '''
   #word_utf = word.decode('utf-8')
   #Grab the most likely lemma
   best_match_word = morph.parse(word)[0]
   lemma = best_match_word.normal_form
   return lemma




'''
#Tests for functions
test_txt = 'Гарри любился, себя… Рон; «влюбился роном!??-'
#test_txt = 'boy loved boy, girl; loved girl!??-'
print type(test_txt)
print 'original:  ', test_txt

no_punct = remove_punctuation(test_txt)
print "Did it remove Punctuation?\n", no_punct,'\n'

blah = make_freq_dict(no_punct)
print "Frequency Dictionary:\n", blah

'''


def split_chapters(sanitized_text):
   '''
   Input: sanitized text (no punctuation, no whitespace characters) in byte format
   Output: A list, where each entry is the sanitized text of one chapter'''
   regex = u'глава\s[0-9]{1,3}'
   print 'text: ', type(sanitized_text)
   print 'regex: ', type(regex)
   #split text by chapter number
   glava_split = re.split(regex, sanitized_text)
   #print out number of chapters and check if correct
   print 'glava split: ', len(glava_split)
   print glava_split[0][0:100]
   chapter_split = []
   for entry in glava_split:
      #Exclude really short entries, they're probably the "Глава х" entries
      if len(entry) > 500:
         chapter_split.append(entry)
         #print 'Chapter split?: ', entry[0:100]
   print 'Number of chapters?: ', len(chapter_split)
   return chapter_split

'''
test_text = '… расскажи, погибнешь рассказали погиб расскажу'.lower()
depunctuated_txt = remove_punctuation(test_text)

frequency_dict = make_freq_dict(depunctuated_txt)
print frequency_dict
'''


      
def ignore_known_words_ru(frequency_dict, book_name, chapter):
   '''Takes dictionary of word-frequency pairs 
   tests if they are in a text file full of known words, 
   and returns a sorted frequency dict full of only the unknown words
   '''
   #TODO
   known_words_file = 'PATH_TO_WORDS'
   known_words = known_words_file.read().decode('utf-8')
   unknown_word_frequency_dict = {}
   for word in sorted_frequency_dict:
      #test if known word
      if word[0] not in known_words:
         unknown_word_frequency_dict[word[0]] = word[1]
   sorted_unknown_word_frequency_dict = sorted(unknown_word_frequency_dict.items(), key=operator.itemgetter(1), reverse=True)
   return sorted_unknown_word_frequency_dict

def add_dictionaries(input_dict, summed_dict):
   '''
   Adds the frequency from one dictionary of word:frequency pairs
   to another
   '''
   for key in input_dict:
      if key in summed_dict:
         summed_dict[key] += input_dict[key]
      else:
         summed_dict[key] = input_dict[key]
   return summed_dict



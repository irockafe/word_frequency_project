# -*- coding: utf-8
from flask import (Flask, request, url_for,
   				redirect, send_from_directory,
   				after_this_request, send_file)
from werkzeug import secure_filename
import os
import operator
from scripts.make_freq_dict_from_txt_with_pymorphy2 import (sanitize_text,
make_freq_dict, lemmatize, split_chapters)
import tempfile

UPLOAD_FOLDER = os.getcwd() + '/uploads/'
KNOWN_WORDS_FOLDER = os.getcwd() + '/known_words/'
ALLOWED_EXTENTSIONS = set(['txt', 'pdf', 'png', 'jpg'])

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
   	file = request.files['file']
   	if file and allowed_file(file.filename):
   		filename = secure_filename(file.filename)
   		processed_filename = filename.replace('.txt','')+'_word_frequency.txt'
   		freq_dict = process_file(file)
   		temp_output = write_freq_dict_to_file(freq_dict, processed_filename)
   		#return temp_output.read()
   		#return redirect(url_for('processed_file',
   		#					filename=processed_filename))
   		return send_file(temp_output.name, as_attachment=True, attachment_filename=processed_filename), temp_output.close()
   		#send_file(temp_path, as_attachment=True)
   return '''
   <!doctype html>
   <title>Create Russian Word-Frequency Lists</title>
   <h1>Create Word Frequency Lists for Russian Texts</h1>
   <h3>Focus your Russian studies on the most common words.</h3>
        <p>Simply upload a text file containing your reading and 
        download the resulting word-frequency list.</p>
        <p>Thanks to <a href="https://pymorphy2.readthedocs.org/en/latest/">
        pymorphy2,</a> almost all words should be lemmatized, so говорит, говорят,
        говорил, говорящий, итд. should all be counted as forms of
        говорить.</p>
   <form action="" method=post enctype=multipart/form-data>
   	<p><input type=file name=file>
   		<input type=submit value=Upload>
   </form>
      <body>At the moment this only accepts plain-text files (.txt).<br>
       Harry Potter and the Prisoner of Azkaban (around 300 pages)
       takes around 1 minute, so please be patient. <br>
       Hopefully new languages, file formats, and features -
       not to mention an actual effort at design -
       will come in the future.<br>
       Best,<br>
       Isaac</body>
   '''

def allowed_file(filename):
   #Checks if this is an allowed filename
   return '.' in filename and \
   	filename.rsplit('.', 1)[1] in ALLOWED_EXTENTSIONS

'''
@app.route('/uploads/<filename>')
def processed_file(filename):
   #Remove the file after it has been given to user
   print type(filename)
   return send_from_directory(app.config['UPLOAD_FOLDER'],
   							filename, as_attachment=True)
   @after_this_request
   def remove_file(response):
   	os.remove(UPLOAD_FOLDER + filename)
'''

def process_file(file):
   unprocessed_text = file.read()
   sanitized_text = sanitize_text(unprocessed_text)
   unsorted_word_freq_dict = make_freq_dict(sanitized_text)
   #sort by word occurrence
   sorted_word_freq_dict = sorted(unsorted_word_freq_dict.items(), key=operator.itemgetter(1), reverse=True)
   return sorted_word_freq_dict

def write_freq_dict_to_file(freq_dict, filename):
   temp = tempfile.NamedTemporaryFile()
   for word in freq_dict:
   	temp.write('%s\t%s\n' % (word[0].encode('utf-8'), word[1]))
   temp.seek(0)
   #send_file(temp, as_attachment=True, attachment_filename = filename)
   return temp

if __name__ == '__main__':
   app.run(debug=True)

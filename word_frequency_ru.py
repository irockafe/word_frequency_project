from flask import (Flask, request, url_for,
					redirect, send_from_directory,
					after_this_request, g)
from werkzeug import secure_filename
import os
import operator
from scripts.make_freq_dict_from_txt_with_pymorphy2 import (sanitize_text,
make_freq_dict, lemmatize, split_chapters)
from glob import glob

UPLOAD_FOLDER = os.getcwd() + '/uploads/'
KNOWN_WORDS_FOLDER = os.getcwd() + '/known_words/'
ALLOWED_EXTENTSIONS = set(['txt', 'pdf', 'png', 'jpg'])

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

'''
def after_this_request(func):
	if not hasattr(g, 'call_after_request'):
		g.call_after_request = []
	g.call_after_request.append(func)
	return func

@app.after_request 
def per_request_callbacks(response):
	for func in getattr(g, 'call_after_request', ()):
		response = func(response)
	return response
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			processed_filename = filename.replace('.txt','')+'_processed.txt'
			freq_dict = process_file(file)
			write_freq_dict_to_file(freq_dict, processed_filename)
			#return output_file
			return redirect(url_for('processed_file',
								filename=processed_filename))
	return '''
	<!doctype html>
	<title>Upload New File</title>
	<h1>Upload New File</h1>
	<form action="" method=post enctype=multipart/form-data>
		<p><input type=file name=file>
			<input type=submit value=Upload>
	</form>
	'''

def allowed_file(filename):
	#Checks if this is an allowed filename
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENTSIONS

@app.route('/uploads/<filename>')
def processed_file(filename):
	#Remove the file after it has been given to user
	print type(filename)
	return send_from_directory(app.config['UPLOAD_FOLDER'],
								filename, as_attachment=True)
	@after_this_request
	def remove_file(response):
		os.remove(UPLOAD_FOLDER + filename)

def process_file(file):
	unprocessed_text = file.read()
	sanitized_text = sanitize_text(unprocessed_text)
	unsorted_word_freq_dict = make_freq_dict(sanitized_text)
	#sort by word occurrence
	sorted_word_freq_dict = sorted(unsorted_word_freq_dict.items(), key=operator.itemgetter(1), reverse=True)
	return sorted_word_freq_dict

def write_freq_dict_to_file(freq_dict, filename):
	with open(UPLOAD_FOLDER+filename, 'w') as f:
		for word in freq_dict:
			f.write('%s\t%s\n' % (word[0].encode('utf-8'), word[1]))

if __name__ == '__main__':
	app.run(debug=True)
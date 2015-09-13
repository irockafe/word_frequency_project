# -*- coding: utf-8
from flask import (Flask, request, url_for, render_template,
                      redirect, send_from_directory,
                      after_this_request, send_file, jsonify,
                      copy_current_request_context)
from werkzeug import secure_filename
import os
import operator
from scripts.make_freq_dict_from_txt_with_pymorphy2 import (sanitize_text,
 lemmatize, split_chapters)
import tempfile
from celery import Celery
from collections import defaultdict
import time
import redis

#Remember to set and Environmental Variable for REDIS_URL!

def make_celery(app):
   '''From flask's celery page at
   http://flask.pocoo.org/docs/0.10/patterns/celery/
   The function creates a new Celery object, 
   configures it with the broker from the application 
   config, updates the rest of the Celery config from 
   the Flask config and then creates a subclass of the 
   task that wraps the task execution in an application 
   context.

   '''
   celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
   celery.conf.update(app.config)
   TaskBase = celery.Task
   class ContextTask(TaskBase):
         abstract = True
         def __call__(self, *args, **kwargs):
               with app.app_context():
                     return TaskBase.__call__(self, *args, **kwargs)
   celery.Task = ContextTask
   return celery

UPLOAD_FOLDER = os.getcwd() + '/uploads/'
KNOWN_WORDS_FOLDER = os.getcwd() + '/known_words/'
ALLOWED_EXTENTSIONS = set(['txt'])

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['SERVER_NAME'] = '127.0.0.1:5000'

app.config.update(
   CELERY_BROKER_URL=os.environ["REDIS_URL"],
   CELERY_RESULT_BACKEND=os.environ["REDIS_URL"]
   )

celery = make_celery(app)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
   '''A page where people can upload their files
   and which begins a background processing task
   (via taskstatus) when they click the upload button.
   
   '''
   if request.method == 'GET':
      return render_template('index.html')
   if request.method == 'POST':
      file = request.files['file']
      if file and allowed_file(file.filename):
         filename = secure_filename(file.filename)
         print 'GOT TO FILE UPLOAD'
         return longtask(file, filename)
   return redirect(url_for('upload_file'))
   #return render_template('index.html')

@app.route('/longtask', methods=['POST'])
def longtask(file, filename):
   '''
   This begins the background task (make_freq_dict).
   It pre-processes the uploaded file as well. Then 
   it redirects user to the /taskstatus page, which
   updates them on progress and serves the 
   output file.
   '''
   if request.method == 'GET':
      return render_template('index.html')
   print 'BEGAN LONG TASK'
   processed_filename = filename.replace('.txt','')+'_word_frequency.txt'
   unprocessed_text = file.read()
   print unprocessed_text[0:100]

   sanitized_text = sanitize_text(unprocessed_text)
   print '\nSANITIZED:\n\n', sanitized_text[0:100]
   #Time consuming!
   unsorted_word_freq_dict = make_freq_dict.delay(sanitized_text, processed_filename)
   print type(unsorted_word_freq_dict)
   
   return redirect(url_for('taskstatus',
                  task_id=unsorted_word_freq_dict.id, 
                  filename=processed_filename,))
                  


@celery.task(name='__main__.make_freq_dict',bind=True)
def make_freq_dict(self, sanitized_txt, processed_filename):
   '''Input: text input that has had punctuation and whitespace characters removed.
   Output: an unsorted dictionary of word frequency
   Uses self variable (enabled by celery.tast(bind=True)) to
   return information about the task's process. In this case, 
   the percent of words that have been processed.
   ''' 
   print sanitized_txt[0:100]

   freq_dict = defaultdict(int)
   #print 'Text type freq_dict: ', type(txt)
   words = sanitized_txt.split()
   print words[0:10]
   total_words = len(words)
   #print 'all words:', words
   for i, word in enumerate(words):
      lemma = lemmatize(word)
      #print type(word)
      #print word
      freq_dict[lemma] += 1

      #Update status of task
      self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total_words,
                                'status': 'In Progres...'})
   print 'Entries in freq dict: ', len(freq_dict)
   #sort_and_download_dict(freq_dict, processed_filename) 
   return freq_dict

#WORKING ON MAKING PYTHON/CELERY TALK WITH 
#the task at hand and a progress bar

@app.route('/status/<task_id>/<filename>')
def taskstatus(task_id, filename):
   '''
   Checks the status of the background task.
   Auto-refreshes a page that updates the user
   on the task's progress.
   Sends the user the file if 
   '''
   print 'GOT TO TASK STATUS'
   task = make_freq_dict.AsyncResult(task_id)
   print 'Task State:', task.state

   if task.state == 'PENDING':
      response = {
         'state': task.state,
         'current': 0,
         'total': 1,
         'status': 'Pending...'
      }
      #time.sleep Prevents a redirect loop???
      #time.sleep(2)
      return render_template('auto_refresh.html', percent_complete= "Pending")


   if task.state == 'SUCCESS':
      #get the background task
      unsorted_freq_dict = task.wait()
      sorted_word_freq_dict = sorted(unsorted_freq_dict.items(), key=operator.itemgetter(1), reverse=True)
      output = write_freq_dict_to_file(sorted_word_freq_dict, filename)
      return send_from_directory(app.config['UPLOAD_FOLDER'],
                                             filename), os.remove(UPLOAD_FOLDER + filename)


   elif task.state != 'FAILURE':
      print 'STATE', task.state
      response = {
         'state': task.state,
         'current': task.info.get('current', 0),
         'total': task.info.get('total', 1),
         'status': task.info.get('status', '')
      }
      #this version of format give no decimal places
      percent_complete = '{0:.0%}'.format(float(response['current'])/response['total'])
      
      
      return render_template('auto_refresh.html', percent_complete= percent_complete)
   else:
      # something went wrong in the background job
      response = {
         'state': task.state,
         'current': 1,
         'total': 1,
         'status': str(task.info),  # this is the exception raised
      }
      return 'something messed up. Sorry!'
   return redirect(url_for('taskstatus', 
                           task_id=task_id, 
                           filename=filename,))
   
   
#@celery.task(name='__main__.write_freq_dict_to_file')
def write_freq_dict_to_file(freq_dict, filename):
   temp = tempfile.NamedTemporaryFile
   
   with open(UPLOAD_FOLDER+filename, 'w+') as f:
      for word in freq_dict:
         f.write('%s\t%s\n' % (word[0].encode('utf-8'), word[1]))
      #send_file(temp, as_attachment=True, attachment_filename = filename)
   
   return f


def allowed_file(filename):
   #Checks if this is an allowed filename
   return '.' in filename and \
         filename.rsplit('.', 1)[1] in ALLOWED_EXTENTSIONS

if __name__ == '__main__':
   app.run(debug=True)



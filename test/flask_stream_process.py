import flask
import time

app = flask.Flask(__name__)

@app.route('/yield')
def index():
	f = open('test.txt', 'w')
	f.write('asdfghkl;')
	def inner(number):
		for x in range(number):
			time.sleep(1)
			yield '%s<br/>\n' % x
# text/html is required for most browsers to show the partial page immediately
	return flask.Response(inner(7), mimetype='text/html'), 
	#flask.send_file(f, as_attachment=True)


app.run(debug=True)

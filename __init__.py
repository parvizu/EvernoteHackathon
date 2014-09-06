import os
from flask import Flask
from flask import render_template
from flask import request
from flask import make_response
from flask import session, redirect, url_for, escape
from evernote.api.client import EvernoteClient
app = Flask(__name__)

@app.route('/')
def index():
	dev_token = "S=s1:U=8f622:E=14fa3ae0552:C=1484bfcd570:P=1cd:A=en-devtoken:V=2:H=c42c1821448ed5c5147028a089f2368f"
	client = EvernoteClient(token=dev_token)
	userStore = client.get_user_store()
	user = userStore.getUser()
	username = user.username
	return render_template('index.html', username=username)

@app.route('/login', methods=['POST'])
def login():
	if request.method == 'POST':
		if valid_login(request.form['email'], request.form['password']):
			#result = get_user_login(request.form['email'], request.form['password'])
			result = {'careId': 1}
			if 'careId' in result:
				careId = result['careId']
				session['careId'] = careId
				return redirect(url_for('myhealth'))
			else:
				error = 'Invalid username/password'
				return render_template('index.html', error=error)


@app.route('/myhealth')
def myhealth():
	if 'careId' in session:
		context = get_app_context()
		careId = session['careId']
		# UNCOMMENT THE FOLLOWING TO USE REAL DATA
		#name = get_data(careId, 'Ptn4kebAo9')['data']['value']
		#birthday = get_data(careId, 'Pt9nZWiTFa')['data']['value']
		#birthday = birthday.split(' ')[0]
		#gender = get_data(careId, 'PtDQzNlDgW')['data']['value']
		#if gender == '1':
		#	gender = "Male"
		#else:
		#	gender = "Female"
		#context['name'] = name
		#context['birthday'] = birthday
		#context['gender'] = gender
		context['name'] = "Theerapat Yangyuenthanasan"
		context['years'] = "26"
		context['gender'] = "Male"
		context['weight'] = 74.84
		context['height'] = 177.8

		return render_template('app.html', context = context)
	else:
		return render_template('index.html')

@app.route('/community')
def community():
	if 'careId' in session:
		return render_template('community.html')
	else:
		return render_template('index.html')

def get_user_login(username, password):
	rips = RequestsIPS()
	result = rips.login(username, password)
	return result.json()

def register_new_user():
	rips = RequestsIPS()
	result = rips.add_new_user('tim35050@gmail.com', 'berkeley')
	if result:
		print "success"
	else:
		print result

def add_data(careId, key, value, date):
	rips = RequestsIPS()
	result = rips.add_data(careId, key, value, date)
	if result:
		print "success"
	else:
		print result

def get_data(careId, key):
	rips = RequestsIPS()
	result = rips.get_data(careId, key)
	return result.json()

def valid_login(username, password):
	return True

def log_the_user_in(username):
	pass

app.secret_key = '*\xd6\xe8T\xd7\xdc9\xcb\xbb\x9e/\xc1\xf5\xbas\x94s\xb6,\xbaB\xfcS!'

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.debug = True
	app.run(host='0.0.0.0', port=port)
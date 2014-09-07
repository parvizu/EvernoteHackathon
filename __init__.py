import os
from flask import Flask
from flask import render_template
from flask import make_response
from flask import session, redirect, url_for, request, escape
from flask import make_response, current_app, jsonify
from datetime import timedelta
from functools import update_wrapper

import urlparse
import urllib

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.api.client import EvernoteClient

import oauth2 as oauth
import shelve

app = Flask(__name__)

APP_SECRET_KEY = \
    'I SCHOOL 4EVER'

EN_CONSUMER_KEY = 'tim35050-0104'
EN_CONSUMER_SECRET = 'f7248ba8d8526c52'

EN_REQUEST_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_ACCESS_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_AUTHORIZE_URL = 'https://sandbox.evernote.com/OAuth.action'

EN_HOST = "sandbox.evernote.com"
EN_USERSTORE_URIBASE = "https://" + EN_HOST + "/edam/user"
EN_NOTESTORE_URIBASE = "https://" + EN_HOST + "/edam/note/"

def get_oauth_client(token=None):
    """Return an instance of the OAuth client."""
    consumer = oauth.Consumer(EN_CONSUMER_KEY, EN_CONSUMER_SECRET)
    if token:
        client = oauth.Client(consumer, token)
    else:
        client = oauth.Client(consumer)
    return client


def get_notestore():
    """Return an instance of the Evernote NoteStore. Assumes that 'shardId' is
    stored in the current session."""
    shardId = session['shardId']
    noteStoreUri = EN_NOTESTORE_URIBASE + shardId
    noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
    noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
    noteStore = NoteStore.Client(noteStoreProtocol)
    return noteStore


def get_userstore():
    """Return an instance of the Evernote UserStore."""
    userStoreHttpClient = THttpClient.THttpClient(EN_USERSTORE_URIBASE)
    userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
    userStore = UserStore.Client(userStoreProtocol)
    return userStore

def store_group_user_assoc(group_id, user_id, assoc_metadata):
	d = shelve.open('shelve.db')
	user_data = { user_id : assoc_metadata }
	if not d.has_key(group_id):
		d[group_id] = []
	d[group_id].append(user_data)

def crossdomain(origin=None, methods=None, headers=None, max_age=21600, attach_to_all=True, automatic_options=True):  
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enter_group', methods=['POST'])
@crossdomain(origin='*')
def enter_group():
	print request.form['groupid']
	return jsonify(groupid=5)


#@app.route('/')
#def index():
#	dev_token = "S=s1:U=8f622:E=14fa3ae0552:C=1484bfcd570:P=1cd:A=en-devtoken:V=2:H=c42c1821448ed5c5147028a089f2368f"
#	client = EvernoteClient(token=dev_token)
#	userStore = client.get_user_store()
#	user = userStore.getUser()
#	username = user.username
#	usernotes = user.listNotebooks()
#	return render_template('index.html', username=username, notebooks=usernotes)

@app.route('/auth')
def auth_start():
    """Makes a request to Evernote for the request token then redirects the
    user to Evernote to authorize the application using the request token.

    After authorizing, the user will be redirected back to auth_finish()."""

    client = get_oauth_client()

    # Make the request for the temporary credentials (Request Token)
    callback_url = 'http://%s%s' % ('127.0.0.1:5000', url_for('auth_finish'))
    request_url = '%s?oauth_callback=%s' % (EN_REQUEST_TOKEN_URL,
        urllib.quote(callback_url))

    resp, content = client.request(request_url, 'GET')

    if resp['status'] != '200':
        raise Exception('Invalid response %s.' % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    # Save the request token information for later
    session['oauth_token'] = request_token['oauth_token']
    session['oauth_token_secret'] = request_token['oauth_token_secret']

    # Redirect the user to the Evernote authorization URL
    return redirect('%s?oauth_token=%s' % (EN_AUTHORIZE_URL,
        urllib.quote(session['oauth_token'])))


@app.route('/authComplete')
def auth_finish():
    """After the user has authorized this application on Evernote's website,
    they will be redirected back to this URL to finish the process."""

    oauth_verifier = request.args.get('oauth_verifier', '')

    token = oauth.Token(session['oauth_token'], session['oauth_token_secret'])
    token.set_verifier(oauth_verifier)

    client = get_oauth_client()
    client = get_oauth_client(token)

    # Retrieve the token credentials (Access Token) from Evernote
    resp, content = client.request(EN_ACCESS_TOKEN_URL, 'POST')

    if resp['status'] != '200':
        raise Exception('Invalid response %s.' % resp['status'])

    access_token = dict(urlparse.parse_qsl(content))
    authToken = access_token['oauth_token']

    userStore = get_userstore()
    user = userStore.getUser(authToken)

    # Save the users information to so we can make requests later
    session['shardId'] = user.shardId
    session['identifier'] = authToken

    return "<ul><li>oauth_token = %s</li><li>shardId = %s</li></ul>" % (
        authToken, user.shardId)


@app.route('/notebook')
def default_notbook():
    authToken = session['identifier']
    noteStore = get_notestore()
    notebooks = noteStore.listNotebooks(authToken)

    names = ''
    for notebook in notebooks:
        defaultNotebook = notebook
        break

    print '---'
    print '7d3611fe-29e6-4399-ae25-c3683a480fa9'
    print '---'
    nfilter = NoteFilter()
    nfilter.notebookGuid = defaultNotebook.guid
    result_spec = NotesMetadataResultSpec(includeTitle=True)
    notes = noteStore.findNotesMetadata(authToken, nfilter, 0, 100, result_spec)
    print notes
    for note in notes.notes:
    	print note
    	print '---'

    return defaultNotebook.name





@app.route('/dummy')
def dummy():
	return render_template('dummy.html')

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
	app.secret_key = APP_SECRET_KEY
	app.run(host='0.0.0.0', port=port)
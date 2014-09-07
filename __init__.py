import os
from flask import Flask
from flask import render_template
from flask import make_response
from flask import session, redirect, url_for, request, escape
from flask import make_response, current_app, jsonify
from datetime import timedelta
from functools import update_wrapper

import calendar
import datetime
import time
import shelve
import itertools
import collections
import json

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
app.debug = True

input_db = shelve.open("timenote.db")
output_db = shelve.open("merge.db")


APP_SECRET_KEY = \
    'I SCHOOL 4EVER'

EN_CONSUMER_KEY = 'ramitmalhotra'
EN_CONSUMER_SECRET = '1f629b9e4f237fdd'

EN_REQUEST_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_ACCESS_TOKEN_URL = 'https://sandbox.evernote.com/oauth'
EN_AUTHORIZE_URL = 'https://sandbox.evernote.com/OAuth.action'

EN_HOST = "sandbox.evernote.com"
EN_USERSTORE_URIBASE = "https://" + EN_HOST + "/edam/user"
EN_NOTESTORE_URIBASE = "https://" + EN_HOST + "/edam/note/"

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


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

@app.route('/save_user_data',methods=['POST'])
def save_user_data():
	return "Saved"


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

    for notebook in notebooks:
        defaultNotebook = notebook
        break

    nfilter = NoteFilter()
    nfilter.notebookGuid = defaultNotebook.guid
    result_spec = NotesMetadataResultSpec(includeTitle=True)
    notes = noteStore.findNotesMetadata(authToken, nfilter, 0, 100, result_spec)
    print notes
    for note in notes.notes:
<<<<<<< HEAD
     if note.guid == "e00c1b8b-cc4f-48b5-bdbb-5f6069dbbc4a":
      fullnote = noteStore.getNote(authToken,note.guid,True,True,True,True)
      resources = fullnote.resources

    syncState = noteStore.getSyncState(authToken)
    mergeByTimeStamp()
    return resources[0].guid

@app.route('/save_user_data',methods=['POST'])
def saveUserData():
    incomingJson = request.get_json()
    input_db = json.loads(incomingJson)



def mergeByTimeStamp():
    createDummyData()
    timestampList = input_db.values()
    tsList = list(itertools.chain(*timestampList))
    print tsList
    temp_dict = {}
    for item in tsList:
        temp_dict = parseDictList(item,temp_dict)
    od = collections.OrderedDict(sorted(temp_dict.items()))
    output_db = od
    print od


def parseDictList(item,temp_dict):
    for ts in item:
        if temp_dict and temp_dict.has_key(ts):
            temp_dict[ts].append(item.get(ts))
        else:
            valList = []
            valList += [item.get(ts)]
            temp_dict[ts] = valList
    return temp_dict


def createDummyData():
	input_db['ramit']=[{'12515':{'text':'this is crazy','userid':'ramit'}},{'14241':{'text':'what the hell?','userid':'ramit'}},{'16241':{'text':'this is a test','userid':'ramit'}}]
	input_db['tim']=[{'12517':{'text':'shit is mad','userid':'tim'}},{'14241':{'text':'hell breaks lose','userid':'tim'}},{'16141':{'text':'testing this shit','userid':'tim'}}]
	input_db['pablo']=[{'12517':{'text':'insanity is calling','userid':'pablo'}},{'14224':{'text':'armageddon and hell','userid':'pablo'}},{'16141':{'text':'testing one two three','userid':'pablo'}}]

app.secret_key = '*\xd6\xe8T\xd7\xdc9\xcb\xbb\x9e/\xc1\xf5\xbas\x94s\xb6,\xbaB\xfcS!'

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.debug = True
	app.secret_key = APP_SECRET_KEY
	app.run(host='0.0.0.0', port=port)
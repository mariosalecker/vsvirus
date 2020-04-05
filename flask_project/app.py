import os

from flask import Flask

app = Flask(__name__)
app.secret_key = "secret key"

UPLOAD_FOLDER = os.path.join(app.root_path, 'data')
PATH_PRODIGY_LABELED = os.path.join(app.root_path, 'src/specs/kurzarbeit_voranmeldung.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PATH_PRODIGY_LABELED'] = PATH_PRODIGY_LABELED
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

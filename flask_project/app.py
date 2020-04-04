from flask import Flask

UPLOAD_FOLDER = './data'
PATH_PRODIGY_LABELED = 'src/specs/kurzarbeit_voranmeldung_de_p.json'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PATH_PRODIGY_LABELED'] = PATH_PRODIGY_LABELED
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

import os
from flask import send_from_directory
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from pathlib import Path
import datetime

from src.convert_to_tsv import Converter
from src.map_labels_to_tsv import LabelMapper

from app import app

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

converter = Converter()
mapper = LabelMapper()


def allowed_file(filename):
    if filename.endswith('.pdf'):
        return True
    return False

@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/result', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            folder_name = str(datetime.datetime.now().timestamp()) + "_" + Path(filename).stem
            root_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(root_dir, exist_ok=True)
            file_path = os.path.join(root_dir, filename)
            file.save(file_path)
            tsv_path = converter.convert_pdf(root_dir, filename)
            result = mapper.extract_and_write_result_for_document(file_path, tsv_path)

            return render_template('result.html', result=result, data_root=Path(filename).stem)
        else:
            flash('Allowed file types is pdf only')
            return render_template('result.html', result={}, data_root='')


@app.route("/get_signature_file/<data_root>")
def get_signature_file(data_root):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], data_root), "signature.jpg")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

import csv
import glob
import os
from pathlib import Path

import pandas as pd
import pytesseract
from loguru import logger
from pdf2image import convert_from_path
from pytesseract import Output
from wand.image import Image

from app import app
os.environ['TESSDATA_PREFIX'] = os.path.join("./", 'tessdata')


class Converter:

    def __init__(self):
        self.files = self.get_files_from_data_dir()
        self.output_root = app.config['UPLOAD_FOLDER']
        self.resolution = 200

    def get_files_from_data_dir(self):
        return glob.glob('./data/*.pdf')

    def convert_pdf(self, filename):

        result_dir_path = self.create_result_dir(filename)

        result_file = self.get_result_file(result_dir_path)
        if result_file:
            return result_file

        result_file_paths = self.create_images(filename, result_dir_path)

        page_list_file_path = self.create_page_list_file(result_dir_path, result_file_paths)

        result_tsv_path = self.create_tsv_results(result_dir_path, page_list_file_path)

        self.create_full_text_result(result_dir_path, result_tsv_path)

        return result_tsv_path

    def create_result_dir(self, filename):
        result_dir_path = os.path.join(self.output_root, Path(filename).stem)
        os.makedirs(result_dir_path, exist_ok=True)
        return result_dir_path

    def get_result_file(self, result_dir):
        result_file = os.path.join(result_dir, 'document.tsv')
        if os.path.isfile(result_file):
            logger.info('Skipping, already converted {}'.format(result_dir))
            return result_file
        return None

    def create_page_list_file(self, result_dir, result_file_paths):
        # create list of page paths in a text file, which can be used by tesseract
        page_list_file_path = os.path.join(result_dir, 'pages-list.txt')
        with open(page_list_file_path, 'w') as f:
            f.write('\n'.join(result_file_paths))
        return page_list_file_path

    def create_tsv_results(self, result_dir, page_list_file):
        # apply OCR on images and get the tsv data
        data = pytesseract.image_to_data(page_list_file, lang='deu', config='', nice=0, output_type=Output.STRING)
        result_tsv_path = os.path.join(result_dir, 'document.tsv')
        with open(result_tsv_path, 'w', encoding='utf8') as f:
            f.write(data)
        return result_tsv_path

    def create_images(self, filename, result_dir_path):
        file_path = os.path.join(result_dir_path, filename)
        images = convert_from_path(file_path, dpi=self.resolution)

        result_file_paths = []
        for index, image in enumerate(images):
            result_file_path = os.path.join(result_dir_path, 'p-{:02d}.png'.format(index))
            result_file_paths.append(result_file_path)
            image.save(result_file_path)

            with Image(filename=result_file_path) as img:
                img.threshold(0.5)
                img.save(filename=result_file_path)
        return result_file_paths

    def create_full_text_result(self, result_dir_path, result_tsv_path):
        df = pd.read_csv(result_tsv_path, escapechar=None, sep='\t', encoding='utf8', quoting=csv.QUOTE_NONE)

        # convert tsv to raw text
        df = df.fillna('')
        line_group = df.groupby(['page_num', 'block_num', 'par_num', 'line_num'])
        line_words = line_group['text'].apply(list).values

        lines = [' '.join(l) for l in line_words]
        full_text = '\n'.join(lines)

        out_txt = os.path.join(result_dir_path, 'document.txt')
        with open(out_txt, 'w', encoding='utf8') as f:
            f.write(full_text)

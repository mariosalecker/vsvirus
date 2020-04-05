from PyPDF2 import PdfFileWriter,PdfFileReader,PdfFileMerger
import collections
import csv
from loguru import logger
import json
import os
from pdf2image import convert_from_path
import cv2

import pandas as pd

import app
class LabelMapper:

    def __init__(self):
        self.path_prodigy_labeled = app.app.config['PATH_PRODIGY_LABELED']
        self.output_root = app.app.config['UPLOAD_FOLDER']

        self.Rectangle = collections.namedtuple("Rectangle", "left top width height")
        self.Field = collections.namedtuple("Field", "filename page_num page_width page_height label rectangle")

        self.fields, self.signature_field = self.extract_field_information()


    def extract_for_all_docs(self):
        documents = self.get_tsvs_to_extract()
        extracted_data = self._extract_data_for_documents(documents)
        self.write_results(extracted_data)

    def _extract_data_for_documents(self, documents):
        extracted_data = []
        for document in documents:
            extracted_document_data = self.extract_and_write_result_for_document(document)
            extracted_data.append(extracted_document_data)

        return extracted_data

    def extract_and_write_result_for_document(self, file_path, tsv_document):
        logger.info('Extracing document: {}'.format(tsv_document))
        df = pd.read_csv(tsv_document, sep='\t', error_bad_lines=False, quoting=csv.QUOTE_NONE, escapechar=None,
                         na_values='', encoding='utf-8')
        df = df.fillna('')

        doc_width = df.iloc[[0]].width.values[0]
        doc_height = df.iloc[[0]].height.values[0]

        scaled_fields = self.scale_annotations(doc_width, doc_height)

        extract = {'filename': tsv_document}
        for field in scaled_fields:
            words = []
            logger.info('Key: {}, {}'.format(field.label, field))
            for index, x in df.iterrows():
                if x['page_num'] != field.page_num:
                    continue
                word_rect = self.Rectangle(x['left'], x['top'], x['width'], x['height'])
                word = x['text']
                conf = x['conf']
                overlap_area = self.area(word_rect, field.rectangle)

                if overlap_area < 20 or conf < 10: continue
                logger.info(overlap_area)
                words.append(word)

            extract[field.label] = ' '.join(words)
            logger.info('Label: {}, {}'.format(field.label, extract[field.label]))

        self.extract_and_save_signature(file_path);
        self.write_results([extract])
        return extract

    def extract_and_save_signature(self, pdf_file_path):
        with open(pdf_file_path) as file:

            signature_file_path = os.path.join(os.path.dirname(file.name), 'p-0' + str(self.signature_field.page_num - 1) + '.png')

            image = cv2.imread(signature_file_path)
            scaled_signature = self.scale(self.signature_field, image.shape[1], image.shape[0])

            y = scaled_signature.rectangle.top
            x = scaled_signature.rectangle.left
            h = scaled_signature.rectangle.height
            w = scaled_signature.rectangle.width
            crop = image[int(y):int(y + h), int(x):int(x + w)]

            signature_file_path = os.path.join(os.path.dirname(file.name), 'signature.jpg')
            cv2.imwrite(signature_file_path, crop,  [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    def extract_field_information(self):
        converted_fields = []
        with open(self.path_prodigy_labeled) as f:
            data = json.load(f)

            doc_name = data['text']
            page_width = data['width']
            page_height = data['height']

            fields = data['fields']

            for field in fields:
                page = field['page']
                rect = self.Rectangle(left=field['left'], top=field['top'], width=field['width'], height=field['height'])
                converted_field = self.Field(filename=doc_name, page_num=page, page_width=page_width,
                                   page_height=page_height, label=field['label'], rectangle=rect)
                converted_fields.append(converted_field)

            signature_rect = self.Rectangle(left=data['signature']['left'], top=data['signature']['top'], width=data['signature']['width'], height=data['signature']['height'])
            signature_field = self.Field(filename=doc_name, page_num=data['signature']['page'], page_width=page_width,
                                         page_height=page_height, label=field['label'], rectangle=signature_rect)
        return converted_fields, signature_field

    def write_results(self, data_extracts):
        result = pd.DataFrame(data_extracts)

        result.to_csv(os.path.join(self.output_root, 'extracted_values.csv'))
        result.to_excel(os.path.join(self.output_root, 'extracted_values.xlsx'))


    def area(self, a, b):  # returns None if rectangles don't intersect
        a_xmax = a.left + a.width
        b_xmax = b.left + b.width
        a_ymax = a.top + a.height
        b_ymax = b.top + b.height
        dx = min(a_xmax, b_xmax) - max(a.left, b.left)
        dy = min(a_ymax, b_ymax) - max(a.top, b.top)
        if (dx >= 0) and (dy >= 0):
            return dx * dy
        return -1

    def scale_annotations(self, doc_width, doc_height):
        result = []
        for annotation in self.fields:
            result.append(self.scale(annotation, doc_width, doc_height))
        return result

    def scale(self, field, doc_width, doc_height):
        factor_width = doc_width / field.page_width
        factor_height = doc_height / field.page_height
        scaled_rect = self.Rectangle(field.rectangle.left * factor_width,
                                     field.rectangle.top * factor_height,
                                     field.rectangle.width * factor_width,
                                     field.rectangle.height * factor_height)
        scaled = self.Field(field.filename, field.page_num, field.page_width, field.page_height,
                            field.label, scaled_rect)
        return scaled

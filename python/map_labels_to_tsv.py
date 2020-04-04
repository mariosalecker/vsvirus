
import re
import collections
import csv
import glob
import json
from loguru import logger
import pandas as pd

class LabelMapper():

    def __init__(self):
        self.path_prodigy_labeled = 'specs/kurzarbeit_voranmeldung_de_p1.json'

        self.Rectangle = collections.namedtuple("Rectangle", "left top width height")
        self.Field = collections.namedtuple("Field", "filename page_num page_width page_height label rectangle")

        self.fields = self.extract_field_information()


    def extract_for_all_docs(self):
        documents = self.get_tsvs_to_extract()
        extracted_data = self._extract_data_for_documents(documents)
        self.write_results(extracted_data)

    def _extract_data_for_documents(self, documents):
        extracted_data = []
        for document in documents:
            extracted_document_data = self._extract_data_for_document(document)
            extracted_data.append(extracted_document_data)

        return extracted_data

    def _extract_data_for_document(self, document):
        logger.info('Extracing document: {}'.format(document))
        df = pd.read_csv(document, sep='\t', error_bad_lines=False, quoting=csv.QUOTE_NONE, escapechar=None,
                         na_values='', encoding='utf-8')
        df = df.fillna('')

        doc_width = df.iloc[[0]].width.values[0]
        doc_height = df.iloc[[0]].height.values[0]

        scaled_fields = self.scale(doc_width, doc_height)


        extract = {'filename': document}
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
        return extract

    def get_tsvs_to_extract(self):
        return glob.glob('./results/**/*.tsv')

    def extract_field_information(self):
        converted_fields = []
        with open(self.path_prodigy_labeled) as f:
            data = json.load(f)

            m = re.search(r'(.*)_p-(\d+)', data['text'])
            doc_name = m.group(1)
            doc_page = int(m.group(2))
            page_width = data['width']
            page_height = data['height']

            fields = data['fields']

            for field in fields:
                rect = self.Rectangle(left=field['left'], top=field['top'], width=field['width'], height=field['height'])
                converted_field = self.Field(filename=doc_name, page_num=doc_page, page_width=page_width,
                                   page_height=page_height, label=field['label'], rectangle=rect)
                converted_fields.append(converted_field)

        return converted_fields

    def write_results(self, data_extracts):
        result = pd.DataFrame(data_extracts)

        result.to_csv('./results/extracted_values.csv')
        result.to_excel('./results/extracted_values.xlsx')


    def area(self, a, b):  # returns None if rectangles don't intersect
        a_xmax = a.left + b.width
        b_xmax = b.left + b.width
        a_ymax = a.top + a.height
        b_ymax = b.top + b.height
        dx = min(a_xmax, b_xmax) - max(a.left, b.left)
        dy = min(a_ymax, b_ymax) - max(a.top, b.top)
        if (dx >= 0) and (dy >= 0):
            return dx * dy
        return -1

    def scale(self, doc_width, doc_height):
        result = []
        for annotation in self.fields:
            factor_width = doc_width / annotation.page_width
            factor_height = doc_height / annotation.page_height
            scaled_rect = self.Rectangle(annotation.rectangle.left * factor_width, annotation.rectangle.top * factor_height, annotation.rectangle.width * factor_width, annotation.rectangle.height * factor_height)
            scaled = self.Field(annotation.filename, annotation.page_num, annotation.page_width, annotation.page_height, annotation.label, scaled_rect)
            result.append(scaled)
        return result

label_mapper = LabelMapper()
label_mapper.extract_for_all_docs()

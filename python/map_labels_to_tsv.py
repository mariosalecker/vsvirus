import collections
import csv
import glob
import json
from loguru import logger
import pandas as pd

#sample input: [{'image':'data:image/png;base64,...','text':'compliance04_p-00','_input_hash':656650123,'_task_hash':1781770524,'_session_id':null,'_view_id':'image_manual','width':1653,'height':2338,'spans':[{'id':'60d35128-24b9-491c-964d-d1785c610391','label':'To','points':[[548.6,350],[548.6,305.6],[284.7,305.6],[284.7,350]],'color':'yellow'},{'id':'0b679cea-bad7-4305-8598-f5b18ccc8f00','label':'From','points':[[702.7,431],[702.7,373.6],[282.1,373.6],[282.1,431]],'color':'cyan'},{'id':'16ac3305-e1dc-4059-8ee3-39ef9fe55773','label':'Dated','points':[[454.5,504.2],[454.5,451.9],[284.7,451.9],[284.7,504.2]],'color':'magenta'},{'id':'b145afb0-57f2-4311-8c27-bf79c373624d','label':'EURSubject','points':[[734.1,606.1],[734.1,569.5],[483.3,569.5],[483.3,606.1]],'color':'springgreen'},{'id':'b54011fd-99fa-47d0-8cad-47ce8318142d','label':'DatedSubject','points':[[812.4,642.6],[812.4,600.8],[658.3,600.8],[658.3,642.6]],'color':'tomato'},{'id':'29ab3629-e50a-4c77-a517-09f852064456','label':'ReferenceDate','points':[[663.5,945.6],[663.5,896],[496.3,896],[496.3,945.6]],'color':'deepskyblue'},{'id':'8f7763a7-6678-40d5-8fda-ab9120507e2b','label':'EUREquity3','points':[[689.6,1084.1],[689.6,1044.9],[438.9,1044.9],[438.9,1084.1]],'color':'orange'},{'id':'a7fd9278-c3b3-484a-aed4-4c7a12f61a46','label':'EURTotalAssets3','points':[[783.7,1165.1],[783.7,1120.7],[512,1120.7],[512,1165.1]],'color':'hotpink'},{'id':'682dfeda-71c0-4ded-86e3-405c16f714c2','label':'EUREquity4','points':[[645.2,1350.6],[645.2,1300.9],[475.4,1300.9],[475.4,1350.6]],'color':'aquamarine'},{'id':'865d6ac8-7aff-4cfa-ad37-18faeb0b7e55','label':'EURExceeds4','points':[[1050.1,1358.4],[1050.1,1303.5],[799.4,1303.5],[799.4,1358.4]],'color':'gold'},{'id':'5c2a32de-8a2b-4f05-ae50-3626bb0e5924','label':'SolvencyRatio','points':[[668.7,1418.5],[668.7,1379.3],[566.9,1379.3],[566.9,1418.5]],'color':'peachpuff'},{'id':'83af6344-691b-482e-b097-28b6282f2dba','label':'YoursFaithfully','points':[[606.1,1917.4],[606.1,1828.6],[162,1828.6],[162,1917.4]],'color':'greenyellow'}],'answer':'accept'}]

path_prodigy_labeled = 'specs/first_doc.json'

Rectangle = collections.namedtuple('Rectangle', 'left top width height')
Annotation = collections.namedtuple('Annotation', 'filename page_num page_width page_height label rectangle')

import cv2
import re

ra = Rectangle(3., 3., 5., 5.)
rb = Rectangle(1., 1., 4., 3.5)
# intersection here is (3, 3, 4, 3.5), or an area of 1*.5=.5

def area(a, b):  # returns None if rectangles don't intersect
    a_xmax = a.left+ b.width
    b_xmax = b.left+ b.width
    a_ymax = a.top+a.height
    b_ymax = b.top + b.height
    dx = min(a_xmax, b_xmax) - max(a.left, b.left)
    dy = min(a_ymax, b_ymax) - max(a.top, b.top)
    if (dx >= 0) and (dy >= 0):
        return dx*dy
    return -1

## get all the prodigy annotations in nicer format
annotations = []
with open(path_prodigy_labeled) as f:
    for line in f:
        data = json.loads(line)

        text = data['text']
        m = re.search(r'(.*)_p-(\d+)', text)

        doc_name = m.group(1)
        doc_page = int(m.group(2))
        page_width = data['width']
        page_height = data['height']
        if 'spans' not in data : continue
        spans = data['spans']
        for span in spans:
            label = span['label']
            points = span['points']
            left = min([x[0] for x in points])
            top = min([x[1] for x in points])
            width = max([x[0] for x in points])-left
            height = max([x[1] for x in points]) - top
            rect = Rectangle(left=left,top=top,width=width,height=height)
            annotation = Annotation(filename=doc_name,page_num=doc_page,page_width=page_width,page_height=page_height,label=label,rectangle=rect)
            annotations.append(annotation)
            logger.info(annotation)

# get the annotations for one document

doc_name = 'compliance01'

doc_annotations = [annot for annot in annotations if annot.filename == doc_name]

documents_all = glob.glob('./results/**/*.tsv')


data_extracts = []

for tsv_file in documents_all:
    logger.info('Going through document: {}'.format(tsv_file))
    df = pd.read_csv(tsv_file, sep='\t', error_bad_lines=False, quoting=csv.QUOTE_NONE, escapechar=None,
                     na_values='', encoding='utf-8')
    df = df.fillna('')

    extract = {'filename': tsv_file}
    for annotation in doc_annotations:
        words = []
        logger.info('Key: {}, {}'.format(annotation.label, annotation))
        for index, x in df.iterrows():
            word_rect = Rectangle(x['left'], x['top'], x['width'], x['height'])
            word = x['text']
            conf = x['conf']
            overlap_area = area(word_rect,annotation.rectangle)

            if overlap_area < 20 or conf < 10: continue
            logger.info(overlap_area)
            #logger.info('confidence: {} \t, text: {}'.format(conf,word))
            words.append(word)
        extract[annotation.label] = ' '.join(words)

    data_extracts.append(extract)

result = pd.DataFrame(data_extracts)

result.to_csv('./results/extracted_values.csv')
result.to_excel('./results/extracted_values.xlsx')
print(result)
    #df[df.apply(lambda x: x['b'] > x['c'], axis=1)]

# get the text in the field of the annotations
import csv
import glob

​import pandas as pd
from pytesseract import Output
from tqdm import tqdm
from pdf2image import convert_from_path, convert_from_bytes
import wand
from wand.color import Color
from wand.display import display
from loguru import logger

maindir="./data/tax_ch"

files=glob.glob(maindir+"/**/*.pdf")

from wand.image import Image as wi
from wand.color import Color
from pathlib import Path

import pytesseract
import os

path = '/anaconda3/envs/py36/bin/'

os.environ['PATH'] += ':'+path

def convert_pdf(filename, output_dir=None, resolution=200):
    name=str(Path(filename).stem)
    if output_dir is None:
        output_dir=os.path.join(Path(filename).parent,Path(filename).stem)

    os.makedirs(output_dir,exist_ok=True)
    out_txt = os.path.join(output_dir, "document.txt")
    if os.path.isfile(out_txt):
        logger.info("Skipping, already converted {}".format(filename))
        return

    images = convert_from_path(filename,dpi=resolution)

    outfiles=[]
    for index,image in enumerate(images):
        outpath = os.path.join(output_dir, "p-{:02d}.png".format(index))
        outfiles.append(outpath)
        image.save(outpath)

    # create list of page paths in a text file, which can be used by tesseract
    outtxt=os.path.join(output_dir, "pages-list.txt")
    with open(outtxt,"w") as f:
        f.write("\n".join(outfiles))

    # apply OCR on images and get the tsv data
    data=pytesseract.image_to_data(outtxt, lang=None, config='', nice=0, output_type=Output.STRING)
    out_tsv = os.path.join(output_dir, "document.tsv")
    with open(out_tsv,"w",encoding="utf8") as f:
        f.write(data)

    df=pd.read_csv(out_tsv,escapechar=None,sep='\t',encoding="utf8",quoting=csv.QUOTE_NONE)

    # convert tsv to raw text
    df=df.fillna("")

    line_group=df.groupby(['page_num', 'block_num', 'par_num', 'line_num'])
    line_words=line_group["text"].apply(list).values

    lines=[" ".join(l) for l in line_words]
    full_text="\n".join(lines)
    with open(out_txt, "w", encoding="utf8") as f:
        f.write(full_text)


for file in tqdm(files):
    logger.info("Converting {}".format(file))
    convert_pdf(file)

​

    #df[df.apply(lambda x: x['b'] > x['c'], axis=1)]

​
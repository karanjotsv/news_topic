import json
import os, re

import posixpath
from urllib import parse

import requests
import unidecode
from tqdm import tqdm
from goose3 import Goose

IMG_PATH = "./images"


def resolveComponents(url):
    parsed = parse.urlparse(url)
    path = posixpath.normpath(parsed.path)
    
    if parsed.path.endswith("/"): path += "/"
    clean = parsed._replace(path=path)

    return clean.geturl()


def clean_text(txt):
    txt = re.subn('[“,”]', '"', txt.strip())
    txt = re.subn('[‘,’]', "'", txt[0])

    return txt[0]


def clean_article(item, article):
    abstract, caption, article = item['abstract'], item['caption'], clean_text(article)

    tips = "As a subscriber, you have 10 gift articles to give each month. Anyone can read what you share."
    article = article.replace(abstract, "").replace(caption, "").replace(tips, "")
    
    while True:
        if article.startswith("\n"): article = article[1 : ]
        else: break

    return article


def get_image(item):  # to fetch image
    img = requests.get(item['image_url'], stream=True).content
    
    with open(os.path.join(IMG_PATH, "%s.jpg" % (item['image_id'])), 'wb') as f:
        f.write(img)


def get_text(item):  # to fetch text
    data = goose.extract(url=resolveComponents(item['article_url']))
    text = unidecode.unidecode(data.cleaned_text)
    
    return text


def check_dir(dir_path):  # to check if ./images exists and is empty
    if os.path.exists(dir_path):
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            
            try:
                if os.path.isfile(file_path):  
                    os.remove(file_path)
            except Exception as e:
                print("Failed to delete %s. %s" % (file_path, e))
    
    else:
        os.mkdir(dir_path)


if __name__ == '__main__':
    goose = Goose()
    
    check_dir(IMG_PATH)
    meta_data, data = json.load(open("nytimes_metadata.json", 'r', encoding='utf8')), []
    
    for i in tqdm(meta_data):
        try:
            get_image(i)
            i['body'] = clean_article(i, get_text(i))
            data.append(i)
        except Exception as e: pass

    json.dump(data, open("data.json", 'w', encoding='utf8'))

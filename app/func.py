import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import requests
from werkzeug.utils import secure_filename
import base64
import os

wolfram_alpha_ID = os.environ.get("wolfram_alpha_ID")
mathpix_id = os.environ.get("mathpix_id")
mathpix_secret = os.environ.get("mathpix_secret")

def get_question(file, isByte=False):
    if not isByte:
        #secure the user upload image and base64 encode it for mathpix
        file_path = secure_filename(file.filename)
        image_uri = "data:image/jpg;base64," + base64.b64encode(open(file_path, "rb").read()).decode()
    else:
        image_uri = "data:image/jpg;base64," + base64.b64encode(file).decode()
    #process request
    r = requests.post("https://api.mathpix.com/v3/latex",\
    data=json.dumps({'src': image_uri, 'formats': ['latex_normal']}),\
    headers={"app_id": mathpix_id, "app_key": mathpix_secret, "Content-type": "application/json"})
    data = json.loads(r.text)

    #If there is an error wit the question, flash, else return the question
    if 'error' in data:
        flash(data['error'] + '\n Try Again!')
    else:
        question = data['latex_normal']
    return question

def get_answer(question):
    
    #Remove empty string from question, url encode
    question.replace(" ","")
    question = urllib.parse.quote(question)

    ret = []
    API_BASE = f"http://api.wolframalpha.com/v2/query?appid={wolfram_alpha_ID}&input=solve+{question}&podstate=Result__Step-by-step+solution&format=plaintext"
    
    #parse the xml data
    xml_data = urllib.request.urlopen(API_BASE).read()
    root = ET.fromstring(xml_data)
    
    for pt in root.findall('.//plaintext'):
        if pt.text:
            for line in pt.text.split('\n'):
                ret.append(line)

    return ret


#Check if the uploaded file is allowed
ALLOWED_EXTENSIONS = {'png', 'jpg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
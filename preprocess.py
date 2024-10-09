import nltk
import re
import spacy
import pandas as pd
import numpy as np
spacy_nlp = spacy.load('en_core_web_lg')

def prepare_doc(max_tokens,sent_list):
    num_tokens = 0
    i = 0
    doc = ""
    num_sent = sent_list.shape[0]
    while i<num_sent:
        tokens = nltk.word_tokenize(sent_list[i])
        num_tokens += len(tokens) + 2
        if num_tokens>max_tokens:
            break
        doc += sent_list[i]
        doc += ' '
        i += 1
    doc = doc.replace('\n',' ')
    doc = re.sub(' +',' ',doc)   
    return doc

def process_date(date):
	months = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'june':6,'jun':6,
			  'jul':7,'july':7,'aug':8,'sept':9,'oct':10,'nov':11,'dec':12}
	date = date.split(', ')[1].split(' ')[:3]
	date[1] = str(months[date[1].lower()])
	if len(date[1])==1:
	    date[1] = '0'+date[1]
	date = '/'.join(date)
	return date

def process_text(text):
	if not text:
		return None
	char_replace_dict = {chr(8221):'\"',chr(8211):'-',chr(8217):"\'",chr(8220):'\"','|':'-','\n':'. ','\t':' ','\'s':''}
	for ch in char_replace_dict.keys():
		text = text.replace(ch,char_replace_dict[ch])

	text = ''.join([i if ord(i)<128 else ' ' for i in text])
	text = text.replace('*',' ')
	text = text.replace('$ ',' ')
	text = text.replace('% ',' ')
	text = re.sub(' +',' ',text)
	text = re.sub(r'\.+','.',text)
	text = text.strip()
	return text

def get_entities(df,vendor):
    df['refs'] = 0
    Entities = []
    for i in df.index:
        body = df.loc[i,'content']
        if type(body) != str:
            Entities.append(None)
            continue

        title = df.loc[i,'title']
        article = title + '\n' + body
        vendor_tokens = vendor.lower().split(' ')
        article = spacy_nlp(article)
        counter1 = 0
        counter2 = 0
        for v in vendor_tokens:
            for ent in article.ents:
                if v in ent.text.lower().split(' '):
                    counter1 += 1
                    if ent.label_ == 'ORG':
                        counter2 += 1
        df.loc[i,'refs'] = counter2
        Entities.append(article.ents)
        if counter2 < 0.9 * counter1:
            df.loc[i,'refs'] = -1 
    df['entities'] = Entities
    return df


	







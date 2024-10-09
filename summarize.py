import pandas as pd
import numpy as np
import nltk
import re
import copy
import warnings
warnings.filterwarnings('ignore')
from transformers import pipeline
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer, util
from LexRank import degree_centrality_scores
from preprocess import prepare_doc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

MODEL_NAME = "mrm8488/bert-small2bert-small-finetuned-cnn_daily_mail-summarization"
MAX_TOKENS = 512
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME,use_fast=False)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
summarizer = pipeline('summarization',model=model,tokenizer=tokenizer)
sentence_model = SentenceTransformer('paraphrase-distilroberta-base-v1')

def rank_sentences(document):
    sentences = nltk.sent_tokenize(document)
    embeddings = sentence_model.encode(sentences, convert_to_tensor=True)
    cos_scores = util.pytorch_cos_sim(embeddings, embeddings).numpy()
    centrality_scores = degree_centrality_scores(cos_scores, threshold=None)
    sent_order = np.argsort(-centrality_scores)
    return np.array(sentences)[sent_order]

def overall_summary(df,num_sent=10):
	titles = df[(df['refs']>0) & (df['article sentiment']=='negative')].sort_values(by='refs',ascending=False)['title'].values.tolist()
	title_text = ''
	for title in titles:
		if title[-1] not in ['.','?','!']:
			title += '.'
		title_text += title
		title_text += ' '
	sentences = rank_sentences(title_text)
	num_sent = min(len(sentences),num_sent)
	summary = ""
	for sent in sentences[:num_sent]:
	    summary += sent.strip()
	    summary += " "
    summary = summary.replace('\n',' ')
	summary = re.sub(' +',' ',summary)
	return summary

def summarize_all(df,max_articles=20):
	summaries = [None for i in range(len(df))]
	order = df[(df['refs']>0) & (df['heading sentiment']=='negative')].sort_values(by='refs',ascending=False).index
	order = order[:min(len(order),max_articles)].tolist()
	documents = df.loc[order,'content'].values.tolist()
	with ThreadPoolExecutor() as executor:
		results = executor.map(summarize_article,documents)
		i = 0
		for res in results:
			summaries[order[i]] = res
			i += 1

	df['summary'] = summaries
	return df

def summarize_article(document):
    max_tokens = copy.copy(MAX_TOKENS)
    if type(document) != str:
        return None
    token_len = copy.copy(MAX_TOKENS)
    while token_len>=MAX_TOKENS:
        sent_list = np.array(nltk.sent_tokenize(document))
        doc = prepare_doc(max_tokens,sent_list)
        tokens = tokenizer.encode(doc)
        token_len = len(tokens)
        max_tokens -= max(token_len - max_tokens,0)

    if token_len < 200:
        max_length = token_len-1
    else:
        max_length = 200

    summary = summarizer(doc,max_length=max_length)[0]['summary_text']
    summary = clean_summary(summary)
    summary = capitalize_summary(doc,summary)

    return summary

def clean_summary(summary):
    summary = summary.replace(' .','.')
    summary = summary.replace(' , ',', ')
    summary = summary.replace(' : ',': ')
    summary = summary.replace(" ' " ,"'")
    summary = summary.replace(" "+chr(8217)+" " ,"'")
    
    summary_ = ''
    i = 0
    while i < len(summary):
        if summary[i].isdigit():
            try:
                if summary[i+1] == ',' and summary[i+2]==' ' and summary[i+3].isdigit():
                    summary_ += summary[i:i+2]+summary[i+3]
                    i += 4
                else:
                    summary_ += summary[i]
                    i += 1
            except:
                summary_ += summary[i]
                i += 1
        else:
            summary_ += summary[i]
            i+=1
    summary = summary_
    if summary[-1] == ' ':
        summary = summary[:-1]

    sentences = nltk.sent_tokenize(summary)

    punkts = ['.','!','?',';']
    if sentences[-1][-1] not in punkts:
        summary = ' '.join(sentences[:-1])

    summary = '. '.join([s.capitalize() for s in summary.split('. ')])
    summary = summary.replace('$ ','$')
    return summary
    
def capitalize_summary(doc,summary):
    stop_words = nltk.corpus.stopwords.words('english')[1:]
    doc_words = nltk.word_tokenize(doc)
    cap_words = []

    for w in doc_words:
        if w.islower()==False:
            cap_words.append(w)
    for w in cap_words:
        if w.lower() in summary and w.lower() not in stop_words and len(w)>1:
            summary = summary.replace(w.lower(),w)
    summary_words = summary.split(' ')
    new_words = []
    for w in summary_words:
        if w=='i':
            new_words.append('I')
        elif len(w)>1:
            if w[1:].isupper()==False and w[1:].islower()==False:
                new_words.append(w[0]+w[1:].lower())
            else:
                new_words.append(w)
        else:
            new_words.append(w)


    summary = ' '.join(new_words)
            
    
    return summary




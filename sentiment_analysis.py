import pandas as pd
import numpy as np
import re
import nltk
import torch
import spacy
from rake_nltk import Rake
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from concurrent.futures import ThreadPoolExecutor

MAX_TOKENS = 512
spacy_nlp = spacy.load('en_core_web_lg')

MODEL_NAME = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
sentimenter = pipeline("sentiment-analysis",model=model,tokenizer=tokenizer)


def get_heading_sentiment(df):

	titles = df['title'].values.tolist()

	for i in range(len(titles)):
		if len(tokenizer.encode(titles[i])) > MAX_TOKENS:
			titles[i] = ""

	sentiments = sentimenter(titles)

	df['heading sentiment'] = 'neutral'
	df['heading sentiment score'] = 0
	for i in range(len(sentiments)):
		df.loc[i,'heading sentiment'] = sentiments[i]['label']
		df.loc[i,'heading sentiment score'] = sentiments[i]['score']

	return df

def get_articles_sentiment(df,max_articles=20):
	Sents = [None for i in range(len(df))]
	order = df[(df['refs']>0) & (df['heading sentiment']=='negative')].sort_values(by='refs',ascending=False).index
	order = order[:min(len(order),max_articles)].tolist()
	for i in order:
		document = df.loc[i,'content']
		sentiments = sentiment_analyser(document)
		for j in range(len(sentiments)):
			sentiments[j]['label'] = sentiments[j]['label']
		Sents[i] = sentiments

	df['body sentiment'] = Sents
	return df

def sentiment_analyser(document):
	if type(document) != str:
		return None
	doc_sents = nltk.sent_tokenize(document)

	for j in range(len(doc_sents)):
		if len(tokenizer.encode(doc_sents[j]))>MAX_TOKENS:
			doc_sents[j] = ""
	sentiments = sentimenter(doc_sents)	
	return sentiments

def get_summary_sentiment(df):
	df['summary sentiment'] = None
	for i in df.index:
		if type(df.loc[i,'summary']) == str:
			sentiment = sentimenter(df.loc[i,'summary'])[0]['label']
			df.loc[i,'summary sentiment'] = sentiment
	return df

def get_overall_sentiment(df):
	df['article sentiment'] = df['heading sentiment']
	for i in df.index:
		if df.loc[i,'heading sentiment']=='negative':
			if df.loc[i,'summary sentiment']!='negative' and df.loc[i,'num_neg_sents']<2:
				df.loc[i,'article sentiment'] = 'neutral'
		if type(df.loc[i,'content'])!=str:
			df.loc[i,'article sentiment'] = None
	return df

def get_neg_sents(df,max_articles=20):
    order = df[(df['heading sentiment']=='negative')&(df['refs']>0)].sort_values(by='refs',ascending=False).index
    df['neg_para'] = ''
    df['num_neg_sents'] = 0
    for i in order[:min(len(order),max_articles)]:
        df.loc[i,'neg_para'] = df.loc[i,'title']
        if type(df.loc[i,'content']) != str:
            continue
        doc_sents = nltk.sent_tokenize(df.loc[i,'content'])
        sentiments = df.loc[i,'body sentiment']
        num_neg_sents = 0
        if type(sentiments)!=list:
            continue
        for j in range(len(sentiments)):
            if sentiments[j]['label']=='negative':
                num_neg_sents += 1
                df.loc[i,'neg_para'] += doc_sents[j]
        df.loc[i,'num_neg_sents'] = num_neg_sents
    return df

def get_neg_ents(df):
	neg_para = ' '.join(df['neg_para'].values.tolist())
	neg_para = re.sub(' +',' ',neg_para)
	doc = spacy_nlp(neg_para)
	ent_dict = {}
	for ent in doc.ents:
		if ent.label_ in ['ORG','PERSON']:
			try:
				ent_dict[ent.text] += 1
			except:
				ent_dict[ent.text] = 1

	return ent_dict

def get_neg_phrases(df):
	neg_para = ' '.join(df['neg_para'].values.tolist())
	r = Rake()
	r.extract_keywords_from_text(neg_para)
	keyphrases = r.get_ranked_phrases()
	return keyphrases[:min(15,len(keyphrases))]

def get_neg_refs(df,vendor):
	ent_dict = get_neg_ents(df)
	refs = 0
	for k in ent_dict.keys():
		if vendor.lower() in k.lower():
			refs += ent_dict[k]
	return refs
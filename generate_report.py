from fpdf import FPDF
from matplotlib import rcParams
import matplotlib as mpl
from pathlib import Path
import os.path

afm_filename = Path(mpl.get_data_path(), 'fonts', 'afm', 'ptmr8a.afm')
from matplotlib.afm import AFM
afm = AFM(open(afm_filename, "rb"))

class PDF(FPDF):
    def header(self):
        self.image('fidelity logo.jpeg', 10, 5, 33)
        self.set_font('Arial','', 13)
        self.set_y(10)
        self.set_x(165)
        self.cell(60, 0, 'Analysis Report', 'C')
        self.set_y(13)
        self.set_x(10)
        self.cell(190,0,border=1)
        self.ln(5)
    
    def footer(self):
        self.set_y(-10)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no())+' (Fidelity internal document)', 0, 0, 'C')
    
    def add_input_details(self,vendor,duration=7,include_words=[],exclude_words=[]):
        epw = self.w - 2*self.l_margin
        self.set_font('Arial', '',size=11)
        th = self.font_size
        colw = epw/5
        if include_words==[]:
            inc_words = '-'
        else:
            inc_words = ', '.join(include_words)
        if exclude_words==[]:
            exc_words = '-'
        else:      
            exc_words = ', '.join(exclude_words)
        col2_width = 0
        self.cell(colw,1.5*th,"Vendor's Name",border=1)
        self.cell(4*colw,1.5*th,vendor,border=1)
        self.ln(1.5*th)
        self.cell(colw,1.5*th,"Duration",border=1)
        self.cell(4*colw,1.5*th,"Past "+str(duration)+" days",border=1)
        self.ln(1.5*th)
        self.cell(colw,1.5*th,"Include Words",border=1)
        self.cell(4*colw,1.5*th,inc_words,border=1)
        self.ln(1.5*th)
        self.cell(colw,1.5*th,"Exclude Words",border=1)
        self.cell(4*colw,1.5*th,exc_words,border=1)
        self.ln(1.5*th)
    
    def add_article_details(self,title,summary,publish_date='08-07-2021',
                            source='CNBC',sentiment_score=0.5,polarity='positive',
                            num_neg_sents=0,top_neg_entities=[]):
        th = self.font_size
        self.ln(1.5*th)
        epw = self.w - 2*self.l_margin
        colw = epw/2
        self.cell(colw,1.5*th,'Source: '+source,border=1,align='C')
        self.cell(colw,1.5*th,'Publish Date: '+publish_date,border=1,align='C')
        self.ln(1.5*th)
        for c in title:
            if ord(c)>126:
                title = title.replace(c,'')
        title = title.encode("ascii",'ignore').decode()
        
        for c in summary:
            if ord(c)>126:
                summary = summary.replace(c,'')
        summary = summary.encode("ascii",'ignore').decode()
        title_words = title.split(' ')
        multi_line_title = ''
        line = 'Title: '
        for w in title_words: 
            if afm.string_width_height(line+w+' ')[0] > 43200:
                multi_line_title += line
                multi_line_title += '\n'
                line = ''
            line += w
            line += ' '
        multi_line_title += line
        self.multi_cell(epw,1.5*th,multi_line_title,border=1)

        summary_words = summary.split(' ')
        multi_line_summary = ''
        line = 'Summary: '
        for w in summary_words:
            if afm.string_width_height(line+w)[0] > 43200:
                multi_line_summary += line
                multi_line_summary += ' \n'
                line = ''
            line += w
            line += ' ' 
        multi_line_summary += line
        self.multi_cell(epw,1.2*th,multi_line_summary,border=1)
        
        self.cell(colw,1.5*th,'Title Sentiment Polarity: '+polarity,border=1,align='C')
        self.cell(colw,1.5*th,'Title Sentiment Confidence: '+str(round(sentiment_score,3)),border=1,align='C')
        self.ln(1.5*th)
        self.cell(2*colw,1.5*th,'Number of Negative Sentences: '+str(int(num_neg_sents)),border=1)
        self.ln(1.5*th)

    def add_overall_details(self,summary,keyphrases,neg_ents,num_neg_sents,num_neg_art,num_neg_refs):
        th = self.font_size
        self.ln(1.5*th)
        epw = self.w - 2*self.l_margin

        self.cell(epw,1.5*th,'Summary of Negative Articles',border=1,align='C')
        self.ln(1.5*th)
        summary_words = summary.split(' ')
        multi_line_summary = ''
        line = ''
        for w in summary_words:
            if afm.string_width_height(line+w+' ')[0] > 43200:
                multi_line_summary += line
                multi_line_summary += '\n'
                line = ''
            line += w
            line += ' ' 
        multi_line_summary += line
        self.multi_cell(epw,1.2*th,multi_line_summary,border=1)
        self.ln(1.5*th)

        self.cell(epw,1.5*th,'Keyphrases Associated with Negative Articles',border=1,align='C')
        self.ln(1.5*th)
        phrase_words = '; '.join(keyphrases).split(' ')
        multi_line_phrase = ''
        line = ''
        for w in phrase_words:
            if afm.string_width_height(line+w+" ")[0] > 43200:
                multi_line_phrase += line
                multi_line_phrase += '\n'
                line = ''
            line += w
            line += ' ' 
        multi_line_phrase += line
        self.multi_cell(epw,1.2*th,multi_line_phrase,border=1)
        self.ln(1.5*th)

        self.cell(epw,1.5*th,'Entities Associated with Negative Articles',border=1,align='C')
        self.ln(1.5*th)
        ent_words = '; '.join(neg_ents).split(' ')
        multi_line_ent = ''
        line = ''
        for w in ent_words:
            if afm.string_width_height(line+w+' ')[0] > 43200:
                multi_line_ent += line
                multi_line_ent += '\n'
                line = ''
            line += w
            line += ' ' 
        multi_line_ent += line
        self.multi_cell(epw,1.2*th,multi_line_ent,border=1)
        self.ln(1.5*th)

        self.cell(epw,1.5*th,'Number of articles with negative sentiment: '+str(num_neg_art),border=1)
        self.ln(1.5*th)
        self.cell(epw,1.5*th,'Number of sentences with negative sentiment: '+str(num_neg_sents),border=1)
        self.ln(1.5*th)
        self.cell(epw,1.5*th,'Number of references to the vendor in the negative context: '+str(num_neg_refs),border=1)


        



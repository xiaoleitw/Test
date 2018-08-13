# encoding:utf-8

import os
import re
import copy
import json
import codecs
import nltk
from nltk.tokenize import WordPunctTokenizer

extra_abbreviations = ['mr', 'mrs', 'miss', 'ms',
                       'dr', 'vs', 'prof', 'inc', 'i.e', 'cf', 'st']
# https://en.wikipedia.org/wiki/English_honorifics
sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
sentence_tokenizer._params.abbrev_types.update(extra_abbreviations)
word_tokenizer = WordPunctTokenizer()


def strip_str(sent):
    sent = re.sub(' +', ' ', sent)
    sent = re.sub('\t+', ' ', sent)
    return sent

def extract_anchor_wikify(sent, is_entity = True):
    sent = sent.replace('">', '"> ') # 解决有些标签后面没有空格的问题
    sent = re.sub(' +', ' ', sent)
    sent = re.sub('\t+', ' ', sent)
    sent = re.sub('(<br>)+', '\n', sent)
    start = 0
    new_line = ''
    for match in re.finditer('<b>(.*?)</b>', sent):
        s, e = match.start(), match.end()
        # anchor = sent[s:e]
        anchor = match.group(1)
        new_line += sent[start:s]
        new_line += anchor + ' '
        start = e
    if start < len(sent):
        new_line += sent[start:]
    sent = new_line
    sent = re.sub(' +', ' ', sent)
    line_words = []
    for part_sent in sent.split("\n"):
        part_sent = part_sent.strip()
        if len(part_sent) < 1:
            continue
        for sub_sent in sentence_tokenizer.tokenize(part_sent):
            basic_words, men_starts, men_ends, men_cats, entities = [], [], [], [], []
            start = 0
            for match in re.finditer('<a class="wiki" href="(.*?)" cat="(.*?)">(.*?)</a>', sub_sent):
                entity = match.group(1)[len('http://en.wikipedia.org/wiki/'):]
                cat = match.group(2)
                mention = match.group(3)
                s, e = match.start(), match.end()
                if s > start:
                    words1 = word_tokenizer.tokenize(sub_sent[start:s])
                    words1 = [x for x in words1 if len(x) > 0]
                    basic_words.extend(words1)
                if is_entity: # 把锚文本作为看做一个整体
                    words2 = [mention.strip()]
                else:
                    words2 = word_tokenizer.tokenize(mention.strip())
                    words2 = [x for x in words2 if len(x) > 0]
                men_starts.append(len(basic_words))
                if is_entity:
                    men_ends.append(len(basic_words) + 1)
                else:
                    men_ends.append(len(basic_words) + len(words2))
                men_cats.append(cat.strip())
                entities.append(entity.strip())
                basic_words.extend(words2)
                start = e
            if start < len(sub_sent):
                words1 = word_tokenizer.tokenize(sub_sent[start:])
                words1 = [x for x in words1 if len(x) > 0]
                basic_words.extend(words1)
            line_words.append((basic_words, men_starts, men_ends, men_cats, entities))
    return line_words


def extract_anchor_origin(sent, is_entity=True):
    sent = sent.replace('">', '"> ')  # 解决有些标签后面没有空格的问题
    sent = re.sub(' +', ' ', sent)
    sent = re.sub('\t+', ' ', sent)
    sent = re.sub('(<br>)+', '\n', sent)
    sent = re.sub(' +', ' ', sent)
    line_words = []
    for part_sent in sent.split("\n"):
        part_sent = part_sent.strip()
        if len(part_sent) < 1:
            continue
        for sub_sent in sentence_tokenizer.tokenize(part_sent):
            basic_words, men_starts, men_ends, entities = [], [], [], []
            start = 0
            for match in re.finditer('<a href="(.*?)">(.*?)</a>', sub_sent):
                entity = match.group(1)
                mention = match.group(2)
                s, e = match.start(), match.end()
                if s > start:
                    words1 = word_tokenizer.tokenize(sub_sent[start:s])
                    words1 = [x for x in words1 if len(x) > 0]
                    basic_words.extend(words1)
                if is_entity:  # 把锚文本作为看做一个整体
                    words2 = [mention.strip()]
                else:
                    words2 = word_tokenizer.tokenize(mention.strip())
                    words2 = [x for x in words2 if len(x) > 0]
                men_starts.append(len(basic_words))
                if is_entity:
                    men_ends.append(len(basic_words) + 1)
                else:
                    men_ends.append(len(basic_words) + len(words2))
                entities.append(entity.strip())
                basic_words.extend(words2)
                start = e
            if start < len(sub_sent):
                words1 = word_tokenizer.tokenize(sub_sent[start:])
                words1 = [x for x in words1 if len(x) > 0]
                basic_words.extend(words1)
            line_words.append((basic_words, men_starts, men_ends, entities))
    return line_words

# 从原始的wiki中抽取链接信息
def extract_origin_wiki(data_dir, out_path):

    # 识别实体重定向
    id2title, redirects = dict(), dict()
    with codecs.open(os.path.join(in_dir, 'page-info'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            t_id, title = terms[0].strip(), terms[2].strip()
            id2title[t_id] = title
    print "page num: ", len(id2title)
    with codecs.open(os.path.join(in_dir, 'page-redirect'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            t_id, title = terms[0].strip(), terms[1].strip()
            if t_id not in id2title:
                continue
            redirects[id2title[t_id]] = title
    print "redirects: ", len(redirects)

    writer = codecs.open(out_path, 'wb', 'utf-8')
    label_sent_num = 0
    with codecs.open(os.path.join(data_dir, 'wiki_sent'), 'rb', 'utf-8') as wf:
        for line in wf:
            if line.startswith('<doc id=') or line.startswith('</doc>'):
                continue
            if line.startswith('<a href="Category'):
                continue
            if len(line.strip().split(' ')) < 3:
                continue
            line_words = extract_anchor_origin(line)
            for words, men_starts, men_ends, entities in line_words:
                if len(entities) < 2:
                    continue
                entities = [w.replace(' ', '_') for w in entities]
                entities = [redirects.get(w, w) for w in entities]
                label_sent_num += 1
                words = [w.replace(' ', '_') for w in words]
                line = ' '.join(words)
                line += '\t' + '\t'.join([str(x) for x in men_starts])
                line += '\t' + '\t'.join(entities)
                writer.write("%s\n" % line)
    writer.close()
    print "label_sent_num: ", label_sent_num


def extract_patterns_type1(data_dir, out_path):
    writer = codecs.open(out_path, 'ab', 'utf-8')
    label_sent_num = 0
    for dir_one in os.listdir(data_dir):
        real_dir_one = os.path.join(in_dir, dir_one)
        print "deal with dir: ", real_dir_one
        for dir_two in os.listdir(real_dir_one):
            file_path = os.path.join(real_dir_one, dir_two)
            # print file_path
            lines = codecs.open(file_path, 'rb', 'utf-8').readlines()
            for line in lines:
                line_words = extract_anchor_wikify(line)
                for words, men_starts, men_ends, men_cats, entities in line_words:
                    if len(entities) < 2:
                        continue
                    label_sent_num += 1
                    words = [w.replace(' ', '_') for w in words]
                    line = ' '.join(words)
                    line += '\t' + '\t'.join([str(x) for x in men_starts])
                    line += '\t' + '\t'.join(entities)
                    line += '\t' + '\t'.join([w.replace(' ', '_') for w in men_cats])
                    writer.write("%s\n" % line)
            # print label_sent_num
    writer.close()

    pass

if __name__ == '__main__':

    # extract_origin_wiki()

    data_dir = '/data/liuc/kb/wikipedia/enwiki-20160501/extracted/wikifier/FULL_UNAMBIGUOUS' # wikifier预测结果存储目录
    out_path = '/data/hesz/wikipedia/wikifier/FULL_UNAMBIGUOUS/labeled_wiki_sentences' # 抽取文件存储结果
    extract_patterns_type1(data_dir, out_path) # 从wikifier结果中提取标记文本




# encoding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import re
import copy
import random
import codecs
import gzip
import json
import urllib
from collections import Counter
import networkx as nx


def extract_mid_wiki(data_dir):
    writer = codecs.open(os.path.join(data_dir, 'wiki_title_mids'), 'wb', 'utf-8')
    with gzip.open(os.path.join(data_dir, 'wikidata-20170227-all-BETA.ttl.gz'), 'r') as fb_f:
        curr_line, is_start = 0, False
        title, mid = '', ''
        for line in fb_f:
            curr_line += 1
            if curr_line % (10 * 1000 * 1000) == 0:
                print 'deal with: ', curr_line
            line = line.strip()
            if line.startswith("<https://en.wikipedia.org/wiki/") \
                and line.endswith("> a schema:Article ;"):
                is_start = True
                title = line[len('<https://en.wikipedia.org/wiki/'):-1*len('> a schema:Article ;')]
                continue
            elif is_start and line.startswith('schema:about wd:') and line.endswith(' ;'):
                mid = line[len('schema:about wd:'):-1*len(' ;')]
                writer.write("%s\t%s\n" % (title, mid))
                is_start = False
    writer.close()


def extract_mid_name(data_dir):
    writer_lang1 = codecs.open(os.path.join(data_dir, 'mid_names_en'), 'wb', 'utf-8')
    writer_lang2 = codecs.open(os.path.join(data_dir, 'mid_names_zh'), 'wb', 'utf-8')
    with gzip.open(os.path.join(data_dir, 'wikidata-20170227-all-BETA.ttl.gz'), 'r') as fb_f:
        curr_line, is_start = 0, False
        mid = ''
        for line in fb_f:
            curr_line += 1
            if curr_line % (10 * 1000 * 1000) == 0:
                print 'deal with: ', curr_line
            if line.strip().startswith('wd:'):
                mid = line.strip().split(' ')[0]
                is_start = True
            if is_start:
                try:
                    matcher = re.match("(.*?)rdfs:label \"(.*?)\"@en ;", line)
                    if matcher:
                        label = matcher.group(2)
                        writer_lang1.write("%s\t%s\n" % (mid, label))
                    else:
                        matcher = re.match("(.*?)rdfs:label \"(.*?)\"@zh-cn ;", line)
                        if matcher:
                            label = matcher.group(2)
                            writer_lang2.write("%s\t%s\n" % (mid, label))
                except:
                    pass
    writer_lang1.close()
    writer_lang2.close()

    writer_lang1 = codecs.open(os.path.join(data_dir, 'mid_description_en'), 'wb', 'utf-8')
    writer_lang2 = codecs.open(os.path.join(data_dir, 'mid_description_zh'), 'wb', 'utf-8')
    with gzip.open(os.path.join(data_dir, 'wikidata-20170227-all-BETA.ttl.gz'), 'r') as fb_f:
        curr_line, is_start = 0, 0
        mid = ''
        for line in fb_f:
            curr_line += 1
            if curr_line % (10 * 1000 * 1000) == 0:
                print 'deal with: ', curr_line
            if line.strip().startswith('wd:'):
                mid = line.strip().split(' ')[0]
                is_start = 0
            if 'schema:description' in line:
                is_start = 1
            if is_start > 0:
                try:
                    matcher = re.match("(.*?)\"(.*?)\"@en,", line)
                    if matcher:
                        label = matcher.group(2)
                        writer_lang1.write("%s\t%s\n" % (mid, label))
                    else:
                        matcher = re.match("(.*?)\"(.*?)\"@zh-cn,", line)
                        if matcher:
                            label = matcher.group(2)
                            writer_lang2.write("%s\t%s\n" % (mid, label))
                except:
                    pass
    writer_lang1.close()
    writer_lang2.close()


def extract_triple(data_dir):
    count = 0
    f1 = codecs.open(os.path.join(data_dir, 'triple'), 'w')
    with gzip.open(os.path.join(data_dir, '20170227.json.gz'), 'r') as f:
        for line in f:
            count += 1
            try:
                data = json.loads(line[:-2])
                for k in data['claims'].keys():
                    for mainsnak in data['claims'][k]:
                        try:
                            if 'id' in mainsnak['mainsnak']['datavalue']['value'].keys():
                                f1.write(data['id'] + '\t' + mainsnak['mainsnak']['property'] + '\t' +
                                         mainsnak['mainsnak']['datavalue']['value']['id'] + '\n')
                                if 'qualifiers' in mainsnak.keys():
                                    for kk in mainsnak['qualifiers'].keys():
                                        if 'id' in mainsnak['qualifiers'][kk]['datavalue']['value'].keys():
                                            f2.write(kk + '\t' + mainsnak['qualifiers'][kk]['property'] + '\t' +
                                                     mainsnak['qualifiers'][kk]['datavalue']['value']['id'] + '\n')
                        except:
                            continue
            except:
                print 'error json line:', line[:-2]
                continue

    f1.close()
    print count


def extract_wikidata_info(kb_dir, need_fact=False):
    mid2name, mid2desp, mid2types = dict(), dict(), dict()
    wiki2mid = dict()
    if need_fact:
        ent_facts = dict()
    with codecs.open(os.path.join(kb_dir, 'wiki_title_mids'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            if len(terms) != 2:
                continue
            title, mid = [x.strip() for x in terms]
            title = urllib.unquote(title).replace(' ', '_')
            wiki2mid[title] = mid
        print "title: ", len(wiki2mid)
    with codecs.open(os.path.join(kb_dir, 'mid_names_en'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            if len(terms) != 2:
                continue
            terms = [x.strip() for x in terms]
            mid = terms[0][3:]
            if mid not in mid2name:
                mid2name[mid] = terms[1].replace('\t', ' ').replace(' ', '_')
    with codecs.open(os.path.join(kb_dir, 'mid_description_en'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            if len(terms) != 2:
                continue
            terms = [x.strip() for x in terms]
            mid = terms[0][3:]
            if mid in mid2desp:
                continue
            desp = terms[1].strip()
            mid2desp[mid] = desp.replace('\t', ' ').replace(' ', '_')
    print "prop desp name: ", len(mid2desp)

    with codecs.open(os.path.join(kb_dir, 'triple'), 'rb', 'utf-8') as wf:
        for line in wf:
            terms = line.split("\t")
            if len(terms) != 3:
                continue
            sub, rel, obj = [w.strip() for w in terms][:3]
            if rel.strip() == 'P31':
                tmp_types = mid2types.get(sub, list())
                tmp_types.append(obj)
                mid2types[sub] = tmp_types
            if need_fact:
                tmp_rels = ent_facts.get((sub, obj), set())
                tmp_rels.add(rel)
                ent_facts[(sub, obj)] = tmp_rels
    if need_fact:
        print "entity pair num: ", len(ent_facts)
        print "fact num: ", sum([len(x) for x in ent_facts.values()])
    if need_fact:
        return mid2name, mid2desp, mid2types, wiki2mid, ent_facts
    else:
        return mid2name, mid2desp, mid2types, wiki2mid, None


if __name__ == '__main__':
    data_dir = '/data/hesz/wikidata/temp'

    # extract_mid_wiki(data_dir) # 提取wikidata中的机器码（mid）与wikpedia中的页面名称（title）对应表
    # extract_mid_name(data_dir) # 提取wikidata中的机器码（mid）对应的name和description
    extract_triple(data_dir) # 抽取wikidata中的三元组信息

    # mid2name, mid2desp, mid2types, wiki2mid, ent_facts = extract_wikidata_info(data_dir, True)
    pass

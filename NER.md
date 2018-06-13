# 模板抽取流程文档

# 1.	下载和处理Wikipedia数据 \
a)	地址：https://dumps.wikimedia.org/backup-index.html \
b)	下载应为维基百科，如：https://dumps.wikimedia.org/enwiki/20180601/ \
c)	下载网页数据（pages-articles）如: https://dumps.wikimedia.org/enwiki/20180601/enwiki-20180601-pages-articles.xml.bz2\
d)	把XML文档转换为无格式文本数据，使用wikiextractor工具（https://github.com/attardi/wikiextractor），如利用如下命令：bzip2 -dc enwiki-20180601-pages-articles.xml.bz2 | python WikiExtractor.py -l -b 10000m -o extracted\
该步骤得到如下图的纯文本数据
 
e)	把各个子文件合并成一个文件，如：cat wiki_00 wiki_01 > wiki_sent\

# 2.	对Wikipedia文本进行实体链接
a)	利用Wikifier工具：https://cogcomp.org/page/software_view/Wikifier\
b)	下载文件的目录（Wikifier2013）下，参考runSimpleTest.sh，运行命令： java -Xmx10G -jar dist/wikifier-3.0-jar-with-dependencies.jar -annotateData data/testSample/sampleText/test.txt data/testSample/sampleOutput/ falseconfigs/STAND_ALONE_NO_INFERENCE.xml。“data/testSample/sampleText/test.txt”是输入的待链接文本文件，链接结果存储在“data/testSample/sampleOutput/”文件夹中
该步骤得到的链接结果如下
test.txt.NER.tagged——命名实体识别的结果；test.txt.wikification.tagged.flat.html——实体链接结果的html格式，通常解析此文件得到所需的实体链接结果；
test.txt.wikification.tagged.full.xml：实体链接详细结果的xml文件
c)	实际操作中，将b)中输入的待链接文本文件“data/testSample/sampleText/test.txt”替换成待链接的文本文件，或替换成包含待链接文本文件的文件夹（单个待链接文本文件太大时，拆分成小文本文件，放置在一个文件夹），将“data/testSample/sampleOutput/”替换成输出文件夹。参考b)运行程序，在输出文件夹下解析html文件，即可得到实体链接结果。
d)	使用我们自行编写的脚本从Wikifier的分析结果（html页面文件）提取文本信息：wikification.py
wikification.py脚本的主函数如下：
data_dir = '/data/liuc/kb/wikipedia/enwiki-20160501/extracted/wikifier/FULL_UNAMBIGUOUS' # wikifier预测结果存储目录
out_path = '/data/hesz/wikipedia/wikifier/FULL_UNAMBIGUOUS/labeled_wiki_sentences' # 抽取文件存储结果
extract_patterns_type1(data_dir, out_path) # 从wikifier结果中提取标记文本

# 3.	对Wikipedia文本进行开放式关系抽取（open ie）
a)	利用华盛顿大学的Reverb工具：https://github.com/knowitall/reverb
b)	下载Reverb工具，如利用下述命令：wget http://reverb.cs.washington.edu/reverb-latest.jar
c)	对文本进行开放式信息抽取，如利用下述命令： java -Xmx512m -jar reverb-latest.jar wiki_sent > wiki_sent.reverb
d)	抽取结果如下所示
 

# 4.	下载Wikidata知识图谱数据
a)	数据描述网页：https://www.wikidata.org/wiki/Wikidata:Database_download
b)	Json格式数据下载地址：https://dumps.wikimedia.org/wikidatawiki/entities/
c)	下载wikidata数据，如使用如下命令：
wget https://dumps.wikimedia.org/wikidatawiki/entities/20180604/wikidata-20180604-all.json.gz
wget https://dumps.wikimedia.org/wikidatawiki/entities/20180604/wikidata-20180604-all-BETA.ttl.gz
d)	使用我们自行编写的脚本从wikidata原始数据中提取实体、类型、事实相关信息：wikidata_pro.py 
wikidata_pro.py脚本的主函数如下：

data_dir = '/data/hesz/wikidata/temp' # 数据存放位置
extract_mid_wiki(data_dir) # 提取wikidata中的机器码（mid）与wikpedia中的页面名称（title）对应表
extract_mid_name(data_dir) # 提取wikidata中的机器码（mid）对应的name和description
extract_triple(data_dir) # 抽取wikidata中的三元组信息
mid2name, mid2desp, mid2types, wiki2mid, ent_facts = extract_wikidata_info(data_dir, True)

# 5.	抽取模板
a)	标记了实体信息的文本数据：wikipedia/labeled_wiki_sentences
b)	知识图谱数据目录：wikidata
c)	开放式关系抽取数据：wiki_sent.reverb_np_triples
d)	使用我们自行编写的脚本从利用上述信息抽取模板：wikidata_pro.py
wikidata_pro.py 脚本的主函数如下：
# 利用Open IE的结果进行模板的抽取
reverb_dir = 'wikipedia'  # reverb数据存在目录
filter_reverb_triple(reverb_dir)

# 首先把实体以及实体间的关系提取出来
kb_dir = 'wikidata' # wikidata数据存放目录
wikidata_infos = extract_wikidata_info(kb_dir, True)

# 句子中的短语实体的链接是使用Wikifier标注出来的
txt_file = 'wikipedia/labeled_wiki_sentences' # wikifier结果

save_dir = 'patterns/reverb_patterns' # 模板数据存放目录
extract_re_patterns(txt_file, reverb_dir, save_dir, wikidata_infos)

# 利用提取出来的连接数据进行关系模板的整理
patt_dir = "/data/hesz/datasets/wiki_patterns/reverb_patterns"
pattern_stat(patt_dir, mid2name)


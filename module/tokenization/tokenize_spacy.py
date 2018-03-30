import spacy
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--lang', help='input language', 
                    type=str, required=True)
parser.add_argument('--input', help='input file path', 
                    type=str, required=True)
parser.add_argument('--output', help='output file path', 
                    type=str, required=True)
parser.add_argument('--batch', help='process batch size', 
                    type=int, default=10000)
parser.add_argument('--thread', help='number of thread', 
                    type=int, default=4)
args = parser.parse_args()

if args.lang == 'en':
    lang_model = 'en_core_web_lg'
elif args.lang == 'fr':
    lang_model = 'fr_core_news_md'
else:
    lang_model = 'en_core_web_lg'

nlp = spacy.load(lang_model, disable=['tagger', 'parser', 'ner'])

docs = []
with open(args.input, 'r') as f:
    for line in f:
        docs.append(line.strip('\n'))

docs_tok = []
count = 0
for doc in nlp.pipe(docs, batch_size=args.batch, n_threads=args.thread):
    # show index
    if count%10000 == 0:
        print(count)
    count += 1
    # process
    docs_tok.append(' '.join([w.text.strip() for w in doc if w.text.strip() != '']))

with open(args.output, 'w') as f:
    f.write('\n'.join(docs_tok))
    f.write('\n')

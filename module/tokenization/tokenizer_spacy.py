# created by Yuhan

import spacy
import argparse


def create_parser():
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="tokenizer of spacy"
    )
    
    parser.add_argument('--lang', '-l', help='input language', 
                        type=str, required=True)

    parser.add_argument('--input', '-i', help='input file path', 
                        type=str, required=True)

    parser.add_argument('--output', '-o', help='output file path', 
                        type=str, required=True)

    parser.add_argument('--encoding', '-e', help='file encoding', 
                        type=str, default='UTF-8')

    parser.add_argument('--batch', '-b', help='process batch size', 
                        type=int, default=10000)

    parser.add_argument('--thread', '-t', help='number of thread', 
                        type=int, default=2)

    return parser


def tok_spacy(lang_model, input_path, encoding='UTF-8', batch_size=10000, num_thread=2):

    # load spacy model and disable useless module
    nlp = spacy.load(lang_model, disable=['tagger', 'parser', 'ner'])

    # read input data
    docs = []
    with open(input_path, 'r', encoding=encoding) as f:
        for line in f:
            docs.append(line.strip())

    # stats
    docs_tok = []
    num_doc = len(docs_tok)
    count = 0
    
    for doc in nlp.pipe(docs, batch_size=batch_size, n_threads=num_thread):
        # show progress
        if count%50000 == 0 or count == num_doc-1:
            print(count, '/', num_doc, 'have been processed')
        count += 1
        # processing
        docs_tok.append(' '.join([w.text.strip() for w in doc if w.text.strip() != '']))
    
    return docs_tok

if __name__ == "__main__":
    
    parser = create_parser()
    args = parser.parse_args()

    # select model by language
    if args.lang == 'en':
        lang_model = 'en_core_web_lg'
    elif args.lang == 'fr':
        lang_model = 'fr_core_news_md'
    else:
        lang_model = 'en_core_web_lg'

    # tokenize input file
    docs_tok = tok_spacy(lang_model, args.input, args.encoding, args.batch, args.thread)

    # write to output
    with open(args.output, 'w') as f:
        f.write('\n'.join(docs_tok))
        f.write('\n')

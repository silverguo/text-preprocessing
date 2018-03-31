# created by yuhan

import fastText
import argparse


def create_parser():
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="language identification by fasttext"
    )
    
    parser.add_argument('--input', '-i', help='input file path', 
                        type=str, required=True)

    parser.add_argument('--output', '-o', help='output file path', 
                        type=str, required=True)

    parser.add_argument('--model', '-m', help='model path', 
                        type=str, required=True)
    
    parser.add_argument('--encoding', '-e', help='file encoding', 
                        type=str, default='UTF-8')

    parser.add_argument('--kmost', '-k', help='most possible k lang', 
                        type=int, default=1)

    return parser


def get_lang(docs, model_path, kmost=1):

    lang_classifier = fastText.load_model(model_path)

    return lang_classifier.predict(docs, kmost)


if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    # read input
    docs = []
    with open(args.input, encoding=args.encoding) as f:
        for line in f:
            docs.append(line.strip())

    # get tuple of lang code and its proba
    doc_lang = get_lang(docs, args.model, args.kmost)

    # write to output
    with open(args.output, 'w') as f:
        # output list of possible lang code for each line
        f.write('\n'.join([' '.join(l) for l in doc_lang[0]]))
        f.write('\n')
    

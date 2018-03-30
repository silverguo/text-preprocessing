"""Use byte pair encoding (BPE) to learn a variable-length encoding of the vocabulary in a text.
This script learns BPE jointly on a concatenation of a list of texts (typically the source and target side of a parallel corpus,
applies the learned operation to each and (optionally) returns the resulting vocabulary of each text.
The vocabulary can be used in apply_bpe.py to avoid producing symbols that are rare or OOV in a training text.

Reference:
Rico Sennrich, Barry Haddow and Alexandra Birch (2016). Neural Machine Translation of Rare Words with Subword Units.
Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (ACL 2016). Berlin, Germany.
"""

# python3 only

import sys
import os
import argparse
import tempfile
from collections import Counter

# local module
import learn_bpe
import apply_bpe


def create_parser():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="learn and apply BPE-based word segmentation")

    parser.add_argument(
        '--input', '-i', type=argparse.FileType('r', encoding='UTF-8'),
        metavar='PATH', required=True, nargs = '+',
        help="Input texts (multiple allowed).")

    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w', encoding='UTF-8'),
        metavar='PATH', required=True,
        help="Output file for BPE codes.")

    parser.add_argument(
        '--symbols', '-s', type=int, default=10000,
        help="Create this many new symbols (each representing a character n-gram) (default: %(default)s))")

    parser.add_argument(
        '--separator', type=str, default='@@', metavar='STR',
        help="Separator between non-final subword units (default: '%(default)s'))")

    parser.add_argument(
        '--write-vocabulary', type=argparse.FileType('w', encoding='UTF-8'), 
        nargs = '+', default=None,
        metavar='PATH', dest='vocab',
        help='Write to these vocabulary files after applying BPE. One per input text. Used for filtering in apply_bpe.py')

    parser.add_argument(
        '--min-frequency', type=int, default=2, metavar='FREQ',
        help='Stop if no symbol pair has frequency >= FREQ (default: %(default)s))')
        
    parser.add_argument(
        '--verbose', '-v', action="store_true",
        help="verbose mode.")

    return parser


if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    # equal input and vocab file
    if args.vocab and len(args.input) != len(args.vocab):
        sys.stderr.write('Error: number of input files and vocabulary files must match\n')
        sys.exit(1)

    # get combined vocabulary of all input texts
    full_vocab = Counter()
    for f in args.input:
        full_vocab += learn_bpe.get_vocabulary(f)
        f.seek(0)

    vocab_list = ['{0} {1}'.format(key, freq) for (key, freq) in full_vocab.items()]

    # learn BPE on combined vocabulary
    learn_bpe.main(vocab_list, args.output, args.symbols, args.min_frequency, args.verbose, is_dict=True)

    with open(args.output.name, 'r', encoding='UTF-8') as codes:
        bpe = apply_bpe.BPE(codes, separator=args.separator)

    # apply BPE to each training corpus and get vocabulary
    for train_file, vocab_file in zip(args.input, args.vocab):

        # temp file to save segmented data
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()

        tmpout = open(tmp.name, 'w', encoding='UTF-8')

        train_file.seek(0)
        for line in train_file:
            tmpout.write(bpe.segment(line).strip())
            tmpout.write('\n')

        tmpout.close()
        tmpin = open(tmp.name, 'r', encoding='UTF-8')

        # get vocab from segmented data
        vocab = learn_bpe.get_vocabulary(tmpin)
        tmpin.close()
        os.remove(tmp.name)

        # vocab freq descending
        for key, freq in sorted(vocab.items(), key=lambda x: x[1], reverse=True):
            vocab_file.write("{0} {1}\n".format(key, freq))
        vocab_file.close()

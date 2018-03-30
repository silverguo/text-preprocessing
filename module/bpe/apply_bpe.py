"""Use operations learned with learn_bpe.py to encode a new text.
The text will not be smaller, but use only a fixed vocabulary, with rare words
encoded as variable-length sequences of subword units.

Reference:
Rico Sennrich, Barry Haddow and Alexandra Birch (2015). Neural Machine Translation of Rare Words with Subword Units.
Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (ACL 2016). Berlin, Germany.
"""

# python3 only

import sys
import argparse
import re


class BPE(object):

    def __init__(self, codes, merges=-1, separator='@@', vocab=None, glossaries=None):

        codes.seek(0)

        # check version information
        firstline = codes.readline()
        if firstline.startswith('# version'):
            self.version = firstline.strip().split()[-1]
        else:
            self.version = 'unknown'
            codes.seek(0)

        # limited by number of merge
        self.bpe_codes = [tuple(item.split()) for (n, item) in enumerate(codes) if (n < merges or merges == -1)]

        # some hacking to deal with duplicates (only consider first instance)
        self.bpe_codes = dict([(code,i) for (i,code) in reversed(list(enumerate(self.bpe_codes)))])
        
        self.bpe_codes_reverse = dict([(pair[0] + pair[1], pair) for pair,i in self.bpe_codes.items()])

        self.separator = separator

        # avoid oov
        self.vocab = vocab

        # protected subword
        self.glossaries = glossaries if glossaries else []

        self.cache = {}

    def segment(self, sentence):
        """segment single sentence (whitespace-tokenized string) with BPE encoding"""
        output = []

        # tokenized by space
        for word in sentence.split(' '):
            # eliminate double spaces
            if not word:
                continue
            new_word = [out for segment in self._isolate_glossaries(word)
                        for out in encode(segment,
                                          self.bpe_codes,
                                          self.bpe_codes_reverse,
                                          self.vocab,
                                          self.separator,
                                          self.version,
                                          self.cache,
                                          self.glossaries)]

            # add separator except last subword
            for item in new_word[:-1]:
                output.append(item + self.separator)
            output.append(new_word[-1])

        return ' '.join(output)

    def _isolate_glossaries(self, word):
        word_segments = [word]

        # depend on order of glossary
        for gloss in self.glossaries:

            # split word by glossaries
            word_segments = [out_segments for segment in word_segments
                                 for out_segments in isolate_glossary(segment, gloss)]
        return word_segments


def create_parser():
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="apply BPE-based word segmentation")

    parser.add_argument(
        '--input', '-i', type=argparse.FileType('r', encoding='UTF-8'),
        metavar='PATH', required=True, 
        help="Input file (required)")

    parser.add_argument(
        '--codes', '-c', type=argparse.FileType('r', encoding='UTF-8'), 
        metavar='PATH', required=True,
        help="File with BPE codes (created by learn_bpe.py)")

    parser.add_argument(
        '--merges', '-m', type=int, default=-1,
        metavar='INT',
        help="Use this many BPE operations (<= number of learned symbols)"+
             "default: Apply all the learned merge operations")
             
    parser.add_argument(
        '--output', '-o', type=argparse.FileType('w', encoding='UTF-8'),
        metavar='PATH', required=True,
        help="Output file (required)")

    parser.add_argument(
        '--separator', '-s', type=str, default='@@', metavar='STR',
        help="Separator between non-final subword units (default: '%(default)s'))")

    parser.add_argument(
        '--vocabulary', type=argparse.FileType('r', encoding='UTF-8'), default=None,
        metavar="PATH",
        help="Vocabulary file (built with get_vocab.py). If provided, this script reverts any merge operations that produce an OOV.")

    parser.add_argument(
        '--vocabulary-threshold', type=int, default=None,
        metavar="INT",
        help="Vocabulary threshold. If vocabulary is provided, any word with frequency < threshold will be treated as OOV")
        
    parser.add_argument(
        '--glossaries', type=str, nargs='+', default=None,
        metavar="STR",
        help="Glossaries. The strings provided in glossaries will not be affected"+
             "by the BPE (i.e. they will neither be broken into subwords, nor concatenated with other subwords")

    return parser


def get_pairs(word):
    """Return set of symbol pairs in a word.

    word is represented as tuple of symbols (symbols being variable-length strings)
    """
    pairs = set()
    prev_char = word[0]
    for char in word[1:]:
        pairs.add((prev_char, char))
        prev_char = char
    return pairs


def encode(orig, bpe_codes, bpe_codes_reverse, vocab, separator, version, cache, glossaries=None):
    """Encode word based on list of BPE merge operations, which are applied consecutively
    """

    # if already in cache
    if orig in cache:
        return cache[orig]

    # same subword in glossary
    if orig in glossaries:
        cache[orig] = (orig,)
        return (orig,)

    # tuple of char and last char with '</w>'
    if version.startswith('0.2.'):
        word = tuple(orig[:-1]) + (orig[-1]+'</w>',)
    else:
        raise NotImplementedError

    # set of bigram
    pairs = get_pairs(word)

    if not pairs:
        return orig

    while True:
        
        bigram = min(pairs, key=lambda pair: bpe_codes.get(pair, float('inf')))

        # not contain this bigram
        if bigram not in bpe_codes:
            break
        
        first, second = bigram
        new_word = []
        
        i = 0
        while i < len(word):
            try:
                j = word.index(first, i)
                new_word.extend(word[i:j])
                i = j
            # if cannot find the pair
            except:
                new_word.extend(word[i:])
                break

            if word[i] == first and i < len(word)-1 and word[i+1] == second:
                new_word.append(first+second)
                i += 2
            else:
                new_word.append(word[i])
                i += 1

        # list to tuple
        new_word = tuple(new_word)
        word = new_word

        # all merged
        if len(word) == 1:
            break
        else:
            pairs = get_pairs(word)

    # do not print end-of-word symbols
    if word[-1] == '</w>':
        word = word[:-1]
    elif word[-1].endswith('</w>'):
        word = word[:-1] + (word[-1].replace('</w>',''),)

    # reverse merge for oov
    if vocab:
        word = check_vocab_and_split(word, bpe_codes_reverse, vocab, separator)

    cache[orig] = word
    return word


def recursive_split(segment, bpe_codes_reverse, vocab, separator, final=False):
    """Recursively split segment into smaller units (by reversing BPE merges)
    until all units are either in-vocabulary, or cannot be split futher."""

    try:
        # final means last subword
        if final:
            left, right = bpe_codes_reverse[segment + '</w>']
            right = right[:-4]
        else:
            left, right = bpe_codes_reverse[segment]
    except:
        #sys.stderr.write('cannot split {0} further.\n'.format(segment))
        yield segment
        return

    if left + separator in vocab:
        yield left
    else:
        for item in recursive_split(left, bpe_codes_reverse, vocab, separator, False):
            yield item

    if (final and right in vocab) or (not final and right + separator in vocab):
        yield right
    else:
        for item in recursive_split(right, bpe_codes_reverse, vocab, separator, final):
            yield item


def check_vocab_and_split(orig, bpe_codes_reverse, vocab, separator):
    """Check for each segment in word if it is in-vocabulary,
    and segment OOV segments into smaller units by reversing the BPE merge operations"""

    out = []

    for segment in orig[:-1]:
        if segment + separator in vocab:
            out.append(segment)
        else:
            # sys.stderr.write('OOV: {0}\n'.format(segment))
            for item in recursive_split(segment, bpe_codes_reverse, vocab, separator, False):
                out.append(item)

    # last subword
    segment = orig[-1]
    if segment in vocab:
        out.append(segment)
    else:
        #sys.stderr.write('OOV: {0}\n'.format(segment))
        for item in recursive_split(segment, bpe_codes_reverse, vocab, separator, True):
            out.append(item)

    return out


def read_vocabulary(vocab_file, threshold):
    """read vocabulary file produced by get_vocab.py, and filter according to frequency threshold.
    """

    vocabulary = set()

    for line in vocab_file:
        word, freq = line.split()
        freq = int(freq)
        if threshold == None or freq >= threshold:
            vocabulary.add(word)

    return vocabulary


def isolate_glossary(word, glossary):
    """
    Isolate a glossary present inside a word.

    Returns a list of subwords. In which all 'glossary' glossaries are isolated 

    For example, if 'USA' is the glossary and '1934USABUSA' the word, the return value is:
        ['1934', 'USA', 'B', 'USA']
    """
    if word == glossary or glossary not in word:
        return [word]
    else:
        splits = word.split(glossary)
        segments = [segment.strip() for sp in splits[:-1] for segment in [sp, glossary] if segment != '']
        return segments + [splits[-1].strip()] if splits[-1] != '' else segments


if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    if args.vocabulary:
        vocabulary = read_vocabulary(args.vocabulary, args.vocabulary_threshold)
    else:
        vocabulary = None

    # get bpe codes
    bpe = BPE(args.codes, args.merges, args.separator, vocabulary, args.glossaries)

    for line in args.input:

        # keep leading whitespace
        leading_whitespace = len(line)-len(line.lstrip())
        if leading_whitespace:
            args.output.write(line[:leading_whitespace])

        args.output.write(bpe.segment(line.strip()))

        # keep trailing whitespace
        trailing_whitespace = len(line)-len(line.rstrip())
        if trailing_whitespace:
            args.output.write(line[-trailing_whitespace:])
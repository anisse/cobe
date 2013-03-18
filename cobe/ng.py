# Copyright (C) 2013 Peter Teichman
# coding=utf-8

import collections
import heapq
import io
import itertools
import logging
import operator
import os
import tempfile
import varint

START_TOKEN = u"<∅>"
END_TOKEN = u"</∅>"


def ngrams(grams, n):
    """Yield successive n-length ranges from grams"""
    for i in xrange(0, len(grams) - n + 1):
        yield grams[i:i+n]


def many_ngrams(grams, orders):
    return itertools.chain(*(ngrams(grams, o) for o in orders))


def iter_ngrams(tokenize, iterable, orders=(3,)):
    """Yield the ngrams found in iterable.

    Args:
        tokenize: a function that takes a string and returns a token list
        iterable: an iterable of tokenizable text

    """
    for text in iterable:
        for each in many_ngrams(tokenize(text), orders):
            yield each


def dict_counts(dictionary):
    """Return sorted item, count tuples from a dict of item -> count"""
    return sorted(dictionary.iteritems(), key=operator.itemgetter(0))


def transactions(generator):
    """yield ngram transactions, as bracketed by <∅> and </∅>"""
    pending = []

    for ngram in generator:
        if ngram[0] == START_TOKEN and len(pending) > 0:
            logging.warn("Skipping incomplete ngram transaction")
            pending = []

        pending.append(ngram)

        if ngram[-1] == END_TOKEN:
            yield pending
            pending = []

    if len(pending) > 0:
        logging.warn("Skipping incomplete ngram transaction at end")


def merge_counts(*iters):
    """Merge the counts on already-sorted iterators of (item, count) pairs"""
    merge = heapq.merge(*iters)
    prev, accum = next(merge)

    for item, count in merge:
        if item == prev:
            accum += count
        else:
            yield prev, accum
            prev = item
            accum = count

    yield prev, accum


def _flush_chunk(strs):
    fd, _ = tempfile.mkstemp()
    out = io.open(fd, mode="w+b")

    for s in strs:
        varint.write_one(len(s), out)
        out.write(s)

    # seek automatically writes the io stream's buffer
    out.seek(0)
    return out


def _read_chunk(fd):
    while 1:
        # read string length, then string
        l = varint.read_one(fd)
        if l is None:
            break
        yield fd.read(l)


def sorted_external(strs):
    """Sort the strings yielded by an iterable

    This operates externally when necessary, so the items need not fit
    into memory.

    """
    memitems = []
    chunks = []

    def close_after(iterable, chunks):
        try:
            for item in iterable:
                yield item
        finally:
            for c in chunks:
                c.close()

    for s in strs:
        memitems.append(s)
#        if len(memitems) > 10000000:
#            print "chunk"
#            chunks.append(_flush_chunk(sorted(memitems)))
#            memitems = []

    print "sorting"
    iters = [sorted(memitems)]
    iters.extend(_read_chunk(c) for c in chunks)

    print "merging"
    return close_after(heapq.merge(*iters), chunks)
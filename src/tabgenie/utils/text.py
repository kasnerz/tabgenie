#!/usr/bin/env python3

# from sacremoses import MosesDetokenizer
import re


def normalize(
    s,
    remove_whitespace=True,
    remove_quotes=True,
    remove_underscores=True,
    remove_parentheses=True,
    split_camelcase=True,
):
    if remove_whitespace:
        s = s.strip()

    if remove_underscores:
        s = re.sub(r"_", r" ", s)

    if remove_quotes:
        s = re.sub(r'"', r"", s)
        s = re.sub(r"``", r"", s)
        s = re.sub(r"''", r"", s)

    if remove_parentheses:
        s = re.sub(r"\(", r"", s)
        s = re.sub(r"\)", r"", s)

    if split_camelcase:
        # split basic camel case, lowercase first letters
        s = re.sub(r"([a-z])([A-Z])", lambda m: rf"{m.group(1)} {m.group(2).lower()}", s)

    return s


# class Detokenizer:
#     def __init__(self):
#         self.detokenizer = MosesDetokenizer(lang='en')

#     def detokenize(self, s):
#         tokens = s.split()
#         return self.detokenizer.detokenize(tokens)

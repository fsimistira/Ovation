#!/usr/bin/env python
# coding: utf8
"""
Example of training an additional entity type

This script shows how to add a new entity type to an existing pre-trained NER
model. To keep the example short and simple, only four sentences are provided
as examples. In practice, you'll need many more — a few hundred would be a
good start. You will also likely need to mix in examples of other entity
types, which might be obtained by running the entity recognizer over unlabelled
sentences, and adding their annotations to the training set.

The actual training is performed by looping over the examples, and calling
`nlp.entity.update()`. The `update()` method steps through the words of the
input. At each word, it makes a prediction. It then consults the annotations
provided on the GoldParse instance, to see whether it was right. If it was
wrong, it adjusts its weights so that the correct action will score higher
next time.

After training your model, you can save it to a directory. We recommend
wrapping models as Python packages, for ease of deployment.

For more details, see the documentation:
* Training the Named Entity Recognizer: https://spacy.io/docs/usage/train-ner
* Saving and loading models: https://spacy.io/docs/usage/saving-loading

Developed for: spaCy 1.9.0
Last tested for: spaCy 1.9.0
"""
from __future__ import unicode_literals, print_function

import random
from pathlib import Path
import io

def main(fname, entTAG):
    print("Creating test file from ", fname)

    fname_ent=fname+'.ent'
    fname_sent=fname+'.proc'
    entName_start='<'+entTAG+'_start>'
    entName_end='<'+entTAG+'_end>'

    sent_table = [line.rstrip('\n') for line in io.open(fname, encoding='utf8')]

    outF1 = open(fname_ent, 'w')
    outF2 = open(fname_sent, 'w')

    for i in range(len(sent_table)):
        locStarts=sent_table[i].find(entName_start)+len(entName_start)
        locEnds=sent_table[i].find(entName_end)
        print(sent_table[i][locStarts:locEnds])
        linetmp=sent_table[i][locStarts:locEnds]
        outF1.write(linetmp.encode('utf8'))
        outF1.write('\n')
        linetmp2 = sent_table[i].replace(entName_start, '').replace(entName_end, '')
        outF2.write(linetmp2.encode('utf8'))
        outF2.write('\n')        
    outF1.close()
    outF2.close()
    print("DONE")

if __name__ == '__main__':
    import plac
    plac.call(main)

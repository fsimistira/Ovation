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

import io
import spacy

def main(modelA, modelB, fname):
#    fname='testAreaSent'    
    temp = [line.rstrip('\n') for line in io.open(fname, encoding='utf8')]
    test_sent=temp[0]
    print(test_sent)
    nlp1 = spacy.load('en', path=modelA)
    nlp1.entity.add_label('area')
    docAREA = nlp1(test_sent)
    for ent in docAREA.ents:
        print(ent.label_.upper()+':', ent.text)

    nlp2 = spacy.load('en', path=modelB)
    nlp2.entity.add_label('street-name')
    docADDRESS = nlp2(test_sent)
    for ent in docADDRESS.ents:
        print(ent.label_.upper()+':', ent.text)


if __name__ == '__main__':
    import plac
    plac.call(main)

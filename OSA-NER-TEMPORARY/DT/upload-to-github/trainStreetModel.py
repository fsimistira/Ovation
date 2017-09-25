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

import spacy
from spacy.gold import GoldParse
from spacy.tagger import Tagger


def train_ner(nlp, train_data, output_dir):
    # Add new words to vocab
    for raw_text, _ in train_data:
        doc = nlp.make_doc(raw_text)
        for word in doc:
            _ = nlp.vocab[word.orth]
    random.seed(0)
    # You may need to change the learning rate. It's generally difficult to
    # guess what rate you should set, especially when you have limited data.
    nlp.entity.model.learn_rate = 0.0001
    for itn in range(1000):
        random.shuffle(train_data)
        loss = 0.
        for raw_text, entity_offsets in train_data:
            doc = nlp.make_doc(raw_text)
            gold = GoldParse(doc, entities=entity_offsets)
            # By default, the GoldParse class assumes that the entities
            # described by offset are complete, and all other words should
            # have the tag 'O'. You can tell it to make no assumptions
            # about the tag of a word by giving it the tag '-'.
            # However, this allows a trivial solution to the current
            # learning problem: if words are either 'any tag' or 'ANIMAL',
            # the model can learn that all words can be tagged 'ANIMAL'.
           # for i in range(len(gold.ner)):
            #    if not gold.ner[i].endswith('unit-area'):
             #       gold.ner[i] = '-'
            nlp.tagger(doc)
            # As of 1.9, spaCy's parser now lets you supply a dropout probability
            # This might help the model generalize better from only a few
            # examples.
            #loss += nlp.entity.update(doc, gold, drop=0.1)
            loss += nlp.entity.update(doc, gold)
        if loss == 0:
            break
    # This step averages the model's weights. This may or may not be good for
    # your situation --- it's empirical.
    nlp.end_training()
    if output_dir:
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.save_to_directory(output_dir)


def main(model_name, output_directory=None):
    print("Loading initial model", model_name)
    nlp = spacy.load(model_name)
    fname='synth.address.corpus'
    fname_ent='synth.address.corpus.ent'
    fname_sent='synth.address.corpus.proc'
    entName_start='<ADDRESS_start>'
    entName_end='<ADDRESS_end>'

    if output_directory is not None:
        output_directory = Path(output_directory)
    sent_table = [line.rstrip('\n') for line in io.open(fname, encoding='utf8')]

    #for sentence in sent_table:
     #   print(sentence )
    #fname='street.names.corpus.ent'
    #inst_table = [line.rstrip('\n') for line in io.open(fname, encoding='utf8')]
    #for sentence2 in inst_table:
     #   print(sentence2 )

    train_data = []

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
    print("START")
    fname2='synth.address.corpus.proc'
    sent_table2 = [line.rstrip('\n') for line in io.open(fname2, encoding='utf8')]
    for sentence2 in sent_table2:
        print(sentence2 )
    fname2='synth.address.corpus.ent'
    inst_table2 = [line.rstrip('\n') for line in io.open(fname2, encoding='utf8')]
    for sentence2 in inst_table2:
        print(sentence2 )

    train_data = []

    for i in range(len(sent_table2)):
        locStarts=sent_table2[i].find(inst_table2[i])
        locEnds=locStarts+len(inst_table2[i])
        #print(sent_table[i][locStarts:locEnds])
        item_tuple=(sent_table2[i], [(locStarts, locEnds, 'ADDRESS')])
        print(item_tuple)
        train_data.append(item_tuple)

    nlp.entity.add_label('ADDRESS')
    train_ner(nlp, train_data, output_directory)
    print("Saving model",output_directory)

if __name__ == '__main__':
    import plac
    plac.call(main)
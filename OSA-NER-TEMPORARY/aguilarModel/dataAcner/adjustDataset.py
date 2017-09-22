import sys

inTrain = open(sys.argv[1], 'rt')
outTrain = open(sys.argv[2], 'w')
trainSent = inTrain.readlines()
ll = len(trainSent)
for j,ts in enumerate(trainSent):
    if j%1000 ==0:
        print(str(j)+"/"+str(ll))
    text = ""
    tss = ts.split("\t")
    words = tss[0].split()
    ents = tss[1].split()  #pos
    #ents = tss[2].split() #entities
    try:
        for i in range(len(words)):
            #text = text+words[i]+"\t"+poss[i]+"\t"+ents[i]+"\n"
            text = text+words[i]+"\t"+ents[i]+"\n"
    except IndexError:
        print("ERROR "+str(j)+" "+str(i))
        print(ts)
        print(text)
    text = text+"\n"
    outTrain.write(text)

inTrain.close()
outTrain.close()


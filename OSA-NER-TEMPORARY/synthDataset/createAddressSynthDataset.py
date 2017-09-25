addr = open("tourpedia/ok-berlin.txt", 'tr').readlines() 
random.shuffle(addr)
conv = open("Frames-dataset/customer.txt", 'tr').readlines()
random.shuffle(conv)
addr = list(map(lambda s: s.strip("\n"), addr))   
addrT = list(map(lambda s: "<ADDRESS_start>"+s+"<ADDRESS_end>", addr))
with open("synth1.txt", 'wt', encoding='utf-8') as out:
    for i,c in enumerate(conv):
        cc = c.split()
        cc.insert(random.randint(0,len(cc)), addrT[i])
        cc = " ".join(cc)
        out.write(cc+"\n")


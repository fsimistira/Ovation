import random

spacing = ["", " "]
sm = ["SM", "sm", "M2", "m2", "S.M.", "s.m.", "S.m.", "Square meters", "square meters", "Square Meters", "square meter", "Square meter", "Square Meter"]

conv = open("Frames-dataset/customer.txt", 'tr').readlines()
random.shuffle(conv)
with open("synthArea1.txt", 'wt', encoding='utf-8') as out:
    for i,c in enumerate(conv):
        cc = c.split()
        cc.insert(random.randint(0,len(cc)), "<AREA_start>"+str(random.randint(40, 200))+spacing[random.randint(0,len(spacing)-1)]+sm[random.randint(0,len(sm)-1)]+"<AREA_end>")
        cc = " ".join(cc)
        out.write(cc+"\n")


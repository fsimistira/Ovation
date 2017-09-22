#$/bin/bash

csvtool -t SPACE -u TAB cat $1 -o appo.txt
cut -f3 --complement appo.txt >appo2.txt
cut -f3 --complement appo2.txt >$1
sed -i -- 's/" "/"\tO/g' $1
rm appo.txt
rm appo2.txt


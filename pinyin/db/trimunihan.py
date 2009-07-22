#!/usr/bin/env python

# You can get the list of fields you need to keep by examining
# the output of the database builder:
keepfields = ["kMandarin", "kXHC1983", "kHanyuPinlu"]

# Extract trimmed old data
unihan = open('Unihan.txt','r')
try:
    outputlines = []
    for line in unihan:
        skip = not(line.startswith("#"))
        for keepfield in keepfields:
            if line[7:].startswith(keepfield):
                skip = False
        
        if skip:
            continue
        
        outputlines.append(line)
finally:
    unihan.close()

# Overwrite with new data
unihan = open('Unihan.txt','w+')
try:
    unihan.writelines(outputlines)
finally:
    unihan.close()
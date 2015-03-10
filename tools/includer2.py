#tool for automatically importing all files in a directory into one file

import os, os.path

projectdir = '..'
mainfile = 'calcmain'
prefiles = ['helpers']
postfiles = ['armasm_new', 'assembler']
outfile = 'bundledmain.py'
ignorefiles = ['main']
importstr = 'import '
startmarker = '##########IMPORT START############\n'
endmarker = '##########IMPORT END############\n'

filedict = {}#dict filename -> content

for dirname, dirs, files in os.walk(projectdir):
    for file in files:
        if not file.endswith('.py'):#ignore binaries and stuff
            continue
        f = open(os.path.join(dirname, file))
        s = f.read()
        f.close()
        filedict[file[:-3]] = s
    while len(dirs):#don't recurse through subdirs
        dirs.pop()

for name in ignorefiles:
    filedict.pop(name)

mainfilesrc = filedict[mainfile]
filedict.pop(mainfile)

filelist = list(filedict)
for f in prefiles:
    if not f in filelist:
        print(f, 'is missing')
        exit(-1)
    filelist.insert(0, f)
    filelist.pop(filelist.index(f, 1))
for f in postfiles:
    if not f in filelist:
        print(f, 'is missing')
        exit(-1)
    filelist.append(f)
    filelist.remove(f)

print(filelist)

s = ''
for name in filelist:
    print('importing %s' % name)
    imported = filedict[name].splitlines()
    imported = startmarker + '\n'.join(imported) + '\n' + endmarker + '\n'
    s = s + imported + endmarker

s = s + mainfilesrc

#remove all imported import statements:
for name in filelist:
    while s.find(importstr+name) != -1:
        s = s[:s.find(importstr+name)]+s[s.find('\n',s.find(importstr+name)):]
if s.find(importstr) != -1:
    print('Warning: did not import: %s' % (s[s.find(importstr):s.find(importstr)+20]))

for name in filelist:
    s = s.replace(name+'.', '')#no namespaces are here anymore
    print('removed all', name+'.')

f = open(outfile, 'w')
f.write(s)
f.close()
print('Finished')

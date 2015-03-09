#assembly language details:
#of the operations dealing with the coprocessor only MRC and MCR are supported (the others (LDC, STC, CDP) are useless on the nspire)
#labels may not have any whitespace before them, instructions have to have whitespace before them

import armasm_new

def printerror(filename, linenum, line, msg):
    print('Error in file "%s" on line %i:%s' % (filename, linenum, line))
    print('\t%s' % (msg))

def printmsg(msg):
    print(msg)

def gettext(filename):
    """returns a list of all lines in the file"""
    f = open(filename, 'r')
    text = f.read()
    f.close()
    return text.split('\n')

def assembler(infile, outfile):
    """assembles infile and writes the binary to outfile
returns -1 on failure, 0 on success"""
    numerrs = 0
    curaddr = 0
    labeldict = {}
    text = gettext(infile)
    code = []
    #create list of Sourceline objects containing the lines of code
    for l in text:
        code.append(armasm_new.Sourceline(l))

    #stage 1: parse comments, labels and operation names
    for i, c in enumerate(code):
        if c.parse_comments() == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in parse_comments')
            numerrs += 1
            continue
        if c.parse_labelpart() == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in parse_labelpart')
            numerrs += 1
            continue
        if c.parse_namepart() == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in parse_namepart')
            numerrs += 1
            continue
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    #stage 2: calculate length and address of every instruction
    curaddr = 0
    for i, c in enumerate(code):
        if c.set_length_and_address(curaddr) == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in set_length_and_address')
            numerrs += 1
            continue
        curaddr += c.get_length()
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    #stage 3: create a dictionary of labels
    for i, c in enumerate(code):
        if len(c.label) > 0:
            if c.label in labeldict:
                printerror(infile, i, c.line, 'Label name already used (at offset 0x%x)' % (labeldict[c.label]))
                numerrs += 1
                continue
            labeldict[c.label] = c.address
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    #stage 4: evaluate/replace pseudo-instructions and some directives (not implemented yet, todo)
    for i, c in enumerate(code):
        if c.replace_pseudoinstructions() == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in replace_pseudoinstructions')
            numerrs += 1
            continue    
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    #stage 5: check syntax, encode all instructions and directives
    for i, c in enumerate(code):
        if c.assemble(labeldict) == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in replace_pseudoinstructions')
            numerrs += 1
            continue
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    #stage 6: write output to file
    binary = b''
    for c in code:
        binary += c.get_hex()
    f = open(outfile, 'wb')
    f.write(b'PRG\x00')
    f.write(binary)
    f.close()

##    #debug cmdline output:
##    for i, c in enumerate(code):
##        print(''.join(['%.2x' % (b) for b in c.get_hex()]), c.line)
##    
##    for i, c in enumerate(code):
##        print(''.join(['%.2x' % (b) for b in c.get_hex()]), end = ' ')

def calc_assemble():
    inf = input('in:')
    outf = input('out:')
    return assembler(inf, outf)

calc_assemble()

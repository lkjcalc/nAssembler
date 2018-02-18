# assembly language details:
# of the operations dealing with the coprocessor only MRC and MCR are supported (the others (LDC, STC, CDP) are useless on the nspire)
# labels may not have any whitespace before them, instructions have to have whitespace before them

import armasm_new
import filedict


def printerror(filename, linenum, line, msg):
    """Print an error message using the supplied information."""
    print('Error in file "%s" on line %i:%s' % (filename, linenum, line))
    print('\t%s' % (msg))


def printmsg(msg):
    """Print msg."""
    print(msg)


def read_file_and_stage1_parse(infile, filestack=tuple()):
    numerrs = 0
    filedict.set_sourcepath(infile)
    text = filedict.get_sourcecode()
    code = []
    includedcode = [] # list of (index, code,) tuples
    # create list of Sourceline objects containing the lines of code
    for l in text:
        code.append(armasm_new.Sourceline(l))

    # stage 1: parse comments, labels and operation names
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
        # read binary files included with INCBIN
        if c.is_incbin():
            if filedict.add_file(c.operands) < 0:
                printerror(infile, i, c.line, 'error in add_file')
                numerrs += 1
                continue
        # recursively add INCLUDEd files
        if c.is_include():
            incfile = c.operands
            if incfile in filestack:
                printerror(infile, i, c.line, 'circular dependence in includes')
                numerrs += 1
                continue
            incnumerrs, inccode = read_file_and_stage1_parse(c.operands, filestack=filestack+(infile,))
            filedict.set_sourcepath(infile)
            numerrs += incnumerrs
            includedcode.append((i,inccode,))
    if numerrs != 0:
        return numerrs, []

    # concatenate all snippets of the code in this file and the included files
    fullcode = []
    currpos = 0
    for i, cd in includedcode:
        fullcode += code[currpos:i]
        fullcode += cd
        currpos = i+1
    fullcode += code[currpos:]
    return numerrs, fullcode


def assembler(infile, outfile):
    """
    Assemble infile and write the binary to outfile.
    Return -1 on failure, 0 on success.
    """

    # extended stage 1: parse comments, labels and operation names, read files included with INCBIN,
    #                   and recursively do the same for all INCLUDEs
    numerrs, code = read_file_and_stage1_parse(infile)
    if numerrs > 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    # stage 2: calculate length and address of every instruction
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

    # stage 3: create a dictionary of labels
    labeldict = {}
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

    # stage 4: evaluate/replace pseudo-instructions and some directives
    for i, c in enumerate(code):
        if c.replace_pseudoinstructions(labeldict) == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in replace_pseudoinstructions')
            numerrs += 1
            continue
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    # stage 5: check syntax, encode all instructions and directives
    for i, c in enumerate(code):
        if c.assemble(labeldict) == -1:
            if len(c.errmsg) > 0:
                printerror(infile, i, c.line, c.errmsg)
            else:
                printerror(infile, i, c.line, 'unknown error in assemble')
            numerrs += 1
            continue
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    # stage 6: write output to file
    binary = bytearray()
    for c in code:
        for b in c.get_hex():
            binary.append(b)
    f = open(outfile, 'wb')
    f.write(bytearray([ord(c) for c in 'PRG\x00']))
    f.write(binary)
    f.close()

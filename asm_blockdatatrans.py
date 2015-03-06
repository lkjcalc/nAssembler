import helpers

def check_blockdatatransop(name, operands):
    """Assumes valid name, valid name+flags combination, valid condcode
checks the operands and returns an error string if invalid, empty string otherwise"""
    operands = [x.strip() for x in operands.split(',', maxsplit=1)]
    if len(operands) < 2:
        return 'Too few operands'
    if len(operands[0]) < 2:
        return 'Invalid operand'
    if operands[0][-1] == '!':
        writeback = True
        operands[0] = operands[0][:-1].strip()
    else:
        writeback = False
    if not helpers.is_reg(operands[0]):
        return 'Expected register'
    base = helpers.get_reg_num(operands[0])
    if base == 15:
        return 'PC is not allowed here'
    if len(operands[1]) < 2:
        return 'Invalid operand'
    if operands[1][-1] == '^':
        sbit = True
        operands[1] = operands[1][:-1].strip()
    else:
        sbit = False
    if operands[1][0] != '{' or operands[1][-1] != '}':
        return 'Missing {} around register list'
    operands[1] = operands[1][1:-1].strip()
    operands[1] = [x.strip() for x in operands[1].split(',')]
    if len(operands[1]) < 1:
        return 'Invalid register list'
    reglist = []
    for op in operands[1]:
        if '-' in op:
            r = op.split('-')
            if len(r) > 2:
                return 'Invalid syntax'
            if not helpers.is_reg(r[0]) or not helpers.is_reg(r[1]):
                return 'Expected register'
            start = helpers.get_reg_num(r[0])
            end = helpers.get_reg_num(r[1])
            if start >= end:
                return 'Registers must be specified in ascending order'
            reglist += range(start, end+1)
        else:
            if not helpers.is_reg(op):
                return 'Expected register'
            reglist.append(helpers.get_reg_num(op))
    for i in range(0, len(reglist)-1):
        if reglist[i] >= reglist[i+1]:
            return 'Registers must be specified in ascending order'
    if sbit and writeback and (name == 'STM' or (name == 'LDM' and not 15 in reglist)):
        return 'Writeback may not be used combined with user bank transfer'
    if writeback and name == 'LDM' and base in reglist:
        return 'Attention: Writeback is useless here because the loaded value will overwrite it'
    return ''    

def encode_blockdatatransop(name, flags, condcode, operands):
    """check_blockdatatransop must be called before this
encodes the instruction and returns it as a bytes object"""
    operands = [x.strip() for x in operands.split(',')]
    if operands[0][-1] == '!':
        writeback = True
        operands[0] = operands[0][:-1].strip()
    else:
        writeback = False
    base = helpers.get_reg_num(operands[0])
    if operands[-1][-1] == '^':
        sbit = True
        operands[-1] = operands[-1][:-1].strip()
    else:
        sbit = False
    operands[1] = operands[1][1:].strip()#strip the curly brackets
    operands[-1] = operands[-1][:-1].strip()
    reglist = []
    for op in operands[1:]:
        if '-' in op:
            (start, end) = [helpers.get_reg_num(r) for r in op.split('-')]
            reglist += range(start, end+1)
        else:
            print(op, helpers.get_reg_num(op))
            reglist.append(helpers.get_reg_num(op))
    regfield = 0
    for r in reglist:
        regfield |= (1 << r)
    lflag = (name == 'LDM')
    addrmodedict = {'ED' : (lflag, lflag), 'IB' : (1, 1), 'FD' : (lflag, not lflag), 'IA' : (1, 0), 'EA' : (not lflag, lflag), 'DB' : (0, 1), 'FA' : (not lflag, not lflag), 'DA' : (0, 0)}
    (uflag, pflag) = addrmodedict[flags]
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (25, 3, 0x4), (24, 1, pflag), (23, 1, uflag), (22, 1, sbit), (21, 1, writeback), (20, 1, lflag), (16, 4, base), (0, 16, regfield)])
    return helpers.bigendian_to_littleendian(encoded)

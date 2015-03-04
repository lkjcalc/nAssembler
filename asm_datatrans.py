import helpers

def is_valid_addresspart(hsflag, addresspart, tflag, address, labeldict):
    """hsflag = True -> selects syntax checking for halfword or signed data transfer instructions, False selects normal unsigned word/byte transfer syntax
address must be the address of this instruction
returns empty string if addresspart is valid according to the syntax rules for datatransfer address part
error string otherwise"""
    if len(addresspart) < 1:
        return 'Address part is missing'
    if addresspart[0] != '[':#must be an expression (label) if not starting with a bracket
        if not addresspart in labeldict:
            return 'Expected bracket or label'
        offset = labeldict[addresspart] - address - 8
        addresspart = '[PC, #'+str(offset)+']'#range check done below
    if addresspart[-2:] in [']!', ']']:
        preindexed = True
        if addresspart[-1] == '!':
            writeback = True
            addresspart = addresspart[:-2]#strip the trailing ]!
        else:
            writeback = False
            addresspart = addresspart[:-1]#strip the trailing ]
    else:
        preindexed = False
        writeback = True
    addresspart = addresspart[1:]#strip the leading [
    addresspart = [x.strip() for x in addresspart.split(',')]
    if len(addresspart) < 1 or len(addresspart) > 3 or (hsflag and len(addresspart) > 2):
        return 'Invalid addresspart'
    if not preindexed:
        if addresspart[0][-1:] != ']':
            return 'Expected closing ]'
        addresspart[0] = addresspart[0][:-1]#strip the trailing ]
    #there should be no syntax differences between pre- and post-indexing left
    if not helpers.is_reg(addresspart[0]):
        return 'Expected register as base'
    if writeback and helpers.get_reg_num(addresspart[0]) == 15:
        return 'Write-back should not be used when PC is the base register'
    if preindexed and tflag:
        return 'T-flag is not allowed when pre-indexing is used'
    if len(addresspart) == 1:
        return ''
    if helpers.is_valid_imval(addresspart[1]):
        n = helpers.imval_to_int(addresspart[1])
        if hsflag:
            limit = 2**8-1
        else:
            limit = 2**12-1
        if n > limit:
            return 'Offset too high (max. %i)' % (limit)
        if n < -limit:
            return 'Offset too low (min. %i)' % (-limit)
        if len(addresspart) > 2:
            return 'Too many operands'
        return ''
    else:
        if len(addresspart[1]) < 2:
            return 'Invalid offset'
        if addresspart[1][0] in ['+', '-']:
            addresspart[1] = addresspart[1][1:]
        if not helpers.is_reg(addresspart[1]):
            return 'Invalid offset: must be register or immediate value'
        if helpers.get_reg_num(addresspart[1]) == 15:
            return 'PC is not allowed as offset'
        if not preindexed and helpers.get_reg_num(addresspart[0]) == helpers.get_reg_num(addresspart[1]):
            return 'Manual says: post-indexed with Rm = Rn should not be used'
        if len(addresspart) == 2:
            return ''
        if hsflag:
            return 'Expected less operands'
        #addresspart[2] should be a shift:
        if len(addresspart[2]) < 3:
            return 'Invalid shift expression'
        shift = addresspart[2]
        if shift.upper() == 'RRX':
            return ''
        shift = shift.split()
        if len(shift) != 2:
            return 'Invalid shift expression'
        if not helpers.is_shiftname(shift[0]):
            return 'Invalid shift name'
        if helpers.is_reg(shift[1]):
            return 'Register specified shift amount is not allowed in data transfer instructions'
        if not helpers.is_valid_imval(shift[1])
            return 'Invalid shift amount'
        n = helpers.imval_to_int(shift[1])
        if n >= 0 and n <= 31:
            return ''
        elif n == 32 and shift[0] not in ['LSR', 'ASR']:
            return 'Shift by 32 is only allowed for LSR'
        return 'Invalid immediate shift amount. Must be 0 <= amount <= 31 (or 32 for special LSR, ASR)'


def check_singledatatransop(flags, operands, address, labeldict):
    """Assumes valid name, valid name+flags combination, valid condcode
Checks the operands and returns an error string if invalid, empty string otherwise"""
    tflag = t in flags
    operands = [x.strip() for x in operands.split(',', maxsplit=1)]
    if len(operands) != 2:
        return 'Expected more operands'
    if not helpers.is_reg(operands[0]):
        return 'Expected register'
    err = is_valid_addresspart(False, operands[1], tflag, address, labeldict)
    if len(err) > 0:
        return err
    return ''

def check_halfsigneddatatransop(operands, address, labeldict):
    """Assumes valid name, valid name+flags combination, valid condcode
Checks the operands and returns an error string if invalid, empty string otherwise"""
    operands = [x.strip() for x in operands.split(',', maxsplit=1)]
    if len(operands) != 2:
        return 'Expected more operands'
    if not helpers.is_reg(operands[0]):
        return 'Expected register'
    err = is_valid_addresspart(True, operands[1], False, address, labeldict)
    if len(err) > 0:
        return err
    return ''
    

def parse_datatrans(operands, address, labeldict):
    """check_singledatatransop or check_halfsigneddatatransop must be called before this
Does the work common to halfsigned and normal datatrans encoding"""
    if operands.count('[') == 0:
        label = operands.split(',')[1].strip()
        offset = labeldict[label] - address - 8
        operands = operands.split(',')[0] + ',[PC, #'+str(offset)+']'
    writeback = (operands[-1] == '!')
    if writeback:
        operands = operands[:-1]
    preindexed = (operands[-1] == ']')
    if preindexed:
        operands = operands[:-1]
    loadflag = (name == 'LDR')
    operands = [x.strip() for x in operands.split(',')]
    if operands[0][-1] == ']':
        operands[0] = operands[0][:-1]
    rd = helpers.get_reg_num(operands[0])
    rn = helpers.get_reg_num(operands[1])
    offset = 0
    upflag = False
    iflag = False
    if len(operands) > 2:
        if helpers.is_valid_imval(operands[2]):
            iflag = False #!!!
            offset = helpers.imval_to_int(operands[2])
            upflag = (offset >= 0)
            offset = abs(offset)
        else:
            iflag = True
            upflag = True
            if operands[2][0] == '-':
                upflag = False
                operands[2] = operands[2][1:]
            elif operands[2][0] == '+':
                operands[2] = operands[2][1:]
            rm = helpers.get_reg_num(operands[2])
            shiftfield = 0
            if len(operands) == 4:
                shift = [x.strip() for x in operands[3].split()]
                if len(shift) == 1:#RRX
                    shifttype = 'ROR'
                    shiftby = 0
                else:
                    shifttype = shift[0]
                    shiftby = helpers.imval_to_int(shift[1])
                    if shiftby == 0:
                        shifttype = 'LSL'
                    if shifttype.upper() in ['LSR', 'ASR'] and shiftby == 32:
                        shiftby = 0
                shiftfield = (shiftby << 3) | {'LSL' : 0, 'ASL' : 0, 'LSR' : 1, 'ASR' : 2, 'ROR' : 3}[shifttype.upper()] << 1
            offset = (shiftfield << 4) | rm
    return (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset)

def encode_singledatatransop(name, flags, condcode, operands, address, labeldict):
    """check_singledatatransop must be called before this
Encodes the instruction and returns it as a bytes object"""
    (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset) = parse_datatrans(operands, address, labeldict)
    if 'T' in flags:
        writeback = True
    byteflag = ('B' in flags)
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (26, 2, 0x1), (25, 1, iflag), (24, 1, preindexed), (23, 1, upflag), (22, 1, byteflag), (21, 1, writeback), (20, 1, loadflag), (16, 4, rn), (12, 4, rd), (0, 12, offset)])
    return helpers.bigendian_to_littleendian(encoded)

def encode_halfsigneddatatransop(name, flags, condcode, operands, address, labeldict):
    """check_halfsigneddatatransop must be called before this
Encodes the instruction and returns it as a bytes object"""
    (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset) = parse_datatrans(operands, address, labeldict)
    assert not (offset & 0xF00)#either iflag and only lowest 4 bit used or not iflag and only lowest 8 bit used
    assert (not iflag) or not (offset & 0xFF0)
    hflag = ('H' in flags)
    sflag = ('S' in flags)
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (24, 1, preindexed), (23, 1, upflag), (22, 1, not iflag), (21, 1, writeback), (20, 1, loadflag), (16, 4, rn), (12, 4, rd), (8, 4, offset<<4), (7, 1, 0x1), (6, 1, sflag), (5, 1, hflag), (4, 1, 0x1), (0, 4, offset)])
    return helpers.bigendian_to_littleendian(encoded)

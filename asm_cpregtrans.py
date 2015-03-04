import helpers

def check_coprocregtransop(name, operands):
    """Assumes valid name, valid name+flags combination, valid condcode
checks the operands and returns an error string if invalid, empty string otherwise"""
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 5 and len(operands) != 6:
        return 'Invalid number of operands. Expected 5 or 6, got %i' % len(operands)
    if not helpers.is_coproc(operands[0]):
        return 'Expected coprocessor (e.g. p15)'
    if not helpers.is_valid_numeric_literal(operands[1]):
        return 'Expected numeric literal'
    if not 0 <= helpers.numeric_literal_to_int(operands[1]) <= 7:
        return 'Must be in range 0 to 7'
    if not helpers.is_reg(operands[2]):
        return 'Expected register'
    if not helpers.is_coprocreg(operands[3]) or not helpers.is_coprocreg(operands[4]):
        return 'Expected coprocessor register (e.g. c0)'
    if len(operands) == 5:
        return ''
    if not helpers.is_valid_numeric_literal(operands[5]):
        return 'Expected numeric literal'
    if not 0 <= helpers.numeric_literal_to_int(operands[5]) <= 7:
        return 'Must be in range 0 to 7'
    return ''

def encode_coprocregtransop(name, condcode, operands):
    """check_coprocregtransop must be called before this
encodes the instruction and returns it as a bytes object"""
    operands = [x.strip() for x in operands.split(',')]
    cpnum = int(operands[0][1:])
    cpopc = helpers.numeric_literal_to_int(operands[1])
    rd = helpers.get_reg_num(operands[2])
    crn = int(operands[3][1:])
    crm = int(operands[4][1:])
    if len(operands) == 6:
        cp = helpers.numeric_literal_to_int(operands[5])
    else:
        cp = 0
    lflag = (name == 'MRC')
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (24, 4, 0xE), (21, 3, cpopc), (20, 1, lflag), (16, 4, crn), (12, 4, rd), (8, 4, cpnum), (5, 3, cp), (4, 1, 0x1), (0, 4, crm)])
    return helpers.bigendian_to_littleendian(encoded)

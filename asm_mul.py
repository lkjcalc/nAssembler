import helpers


def check_mulop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if name == 'MUL' and len(operands) != 3:
        return 'Expected 3 operands, got %i' % len(operands)
    if name == 'MLA' and len(operands) != 4:
        return 'Expected 4 operands, got %i' % len(operands)
    for o in operands:
        if not helpers.is_reg(o):
            return 'Expected a register'
    operands = [helpers.get_reg_num(x) for x in operands]
    if 15 in operands:
        return 'PC is not allowed here'
    if operands[0] == operands[1]:
        return 'Rd must be different from Rm'
    return ''


def encode_mulop(name, flags, condcode, operands):
    """
    check_mulop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [helpers.get_reg_num(x.strip()) for x in operands.split(',')]
    sflag = (flags == 'S')
    (rd, rm, rs) = operands[0:3]
    if name == 'MUL':
        rn = 0
        aflag = False
    else:
        rn = operands[3]
        aflag = True
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (21, 1, aflag), (20, 1, sflag), (16, 4, rd),
                                    (12, 4, rn), (8, 4, rs), (4, 4, 0x9), (0, 4, rm)])
    return helpers.bigendian_to_littleendian(encoded)


def check_longmulop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 4:
        return 'Expected 4 operands, got %i' % len(operands)
    for o in operands:
        if not helpers.is_reg(o):
            return 'Expected a register'
    operands = [helpers.get_reg_num(x) for x in operands]
    if 15 in operands:
        return 'PC is not allowed here'
    if operands[0] == operands[1] or operands[0] == operands[2] or operands[1] == operands[2]:
        return 'RdHi, RdLo and Rm must all be different registers'
    return ''


def encode_longmulop(name, flags, condcode, operands):
    """
    check_longmulop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    (rdlo, rdhi, rm, rs) = [helpers.get_reg_num(x.strip()) for x in operands.split(',')]
    sflag = (flags == 'S')
    signedflag = (name[0] == 'S')
    aflag = (name[3] == 'A')
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (23, 5, 0x1), (22, 1, signedflag), (21, 1, aflag),
                                    (20, 1, sflag), (16, 4, rdhi), (12, 4, rdlo), (8, 4, rs), (4, 4, 0x9), (0, 4, rm)])
    return helpers.bigendian_to_littleendian(encoded)

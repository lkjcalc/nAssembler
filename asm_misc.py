import helpers
# branch, psr, swi


def check_branchop(name, operands, address, labeldict):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 1:
        return 'Invalid number of operands: expected 1, got %i' % (len(operands))
    operands = operands[0]
    if name == 'BX':
        operands = operands.strip()
        if not helpers.is_reg(operands):
            return 'Invalid Operand: Expected register'
        rn = helpers.get_reg_num(operands)
        if rn == 15:
            return 'PC not allowed here (causes undefined behaviour)'
        return ''
    else:
        operands = operands.strip()
        err = helpers.check_pcrelative_expression(operands, labeldict)
        if len(err) != 0:
            return 'Invalid Operand: Expected pc relative expression (%s)' % (err)
        offset = helpers.pcrelative_expression_to_int(operands, address, labeldict)
        if offset % 4 != 0:
            return 'Offset must be aligned to four bytes'
        offset >>= 2
        if offset < -2**23 or offset > 2**23-1:
            return 'Branch target too far away'
        return ''


def encode_branchop(name, condcode, operands, address, labeldict):
    """
    check_branchop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = operands.strip()
    if name == 'BX':
        rn = helpers.get_reg_num(operands)
        ccval = helpers.get_condcode_value(condcode)
        encoded = helpers.encode_32bit([(28, 4, ccval), (4, 24, 0x12FFF1), (0, 4, rn)])
        return helpers.bigendian_to_littleendian(encoded)
    else:
        offset = helpers.pcrelative_expression_to_int(operands, address, labeldict)
        offset >>= 2
        offset = offset + (offset < 0)*(1 << 24)  # correction for negative offsets
        ccval = helpers.get_condcode_value(condcode)
        lflag = (name == 'BL')
        encoded = helpers.encode_32bit([(28, 4, ccval), (25, 3, 0x5), (24, 1, lflag), (0, 24, offset)])
        return helpers.bigendian_to_littleendian(encoded)


def check_psrtransop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 2:
        return 'Invalid number of operands: expected 2, got %i' % (len(operands))
    if name == 'MRS':
        if not helpers.is_reg(operands[0]):
            return 'Invalid operand: expected register'
        rd = helpers.get_reg_num(operands[0])
        if rd == 15:
            return 'PC is not allowed here'
        if not operands[1].upper() in ['SPSR', 'SPSR_ALL', 'CPSR', 'CPSR_ALL']:
            return 'Invalid operand: expected psr'
        return ''
    else:
        if not helpers.is_psr(operands[0]):
            return 'Invalid operand: expected psr'
        if not operands[0].upper().endswith('FLG'):
            if not helpers.is_reg(operands[1]):  # immediate is only allowed for PSR_FLG
                return 'Invalid operand: expected register'
            if helpers.get_reg_num(operands[1]) == 15:
                return 'PC is not allowed here'
            return ''
        if helpers.is_reg(operands[1]):
            if helpers.get_reg_num(operands[1]) == 15:
                return 'PC is not allowed here'
            return ''
        if not helpers.is_valid_imval(operands[1]):
            return 'Invalid operand: expected register or immediate value'
        if not helpers.is_expressable_imval(operands[1]):
            return 'This immediate value cannot be encoded'
        return ''


def encode_psrtransop(name, condcode, operands):
    """
    check_psrtransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    if name == 'MRS':
        rd = helpers.get_reg_num(operands[0])
        if operands[1].upper()[0] == 'C':  # CPSR
            spsrflag = False
        else:
            spsrflag = True
        ccval = helpers.get_condcode_value(condcode)
        encoded = helpers.encode_32bit([(28, 4, ccval), (23, 5, 0x2), (22, 1, spsrflag), (16, 6, 0xF), (12, 4, rd)])
        return helpers.bigendian_to_littleendian(encoded)
    else:
        if operands[0].upper()[0] == 'C':  # CPSR
            spsrflag = False
        else:
            spsrflag = True
        if operands[0].upper().endswith('FLG'):
            allflag = False
        else:
            allflag = True
        if helpers.is_reg(operands[1]):
            iflag = False
            rm = helpers.get_reg_num(operands[1])
            op2field = rm
        else:
            iflag = True
            op2field = helpers.encode_imval(operands[1])
        ccval = helpers.get_condcode_value(condcode)
        encoded = helpers.encode_32bit([(28, 4, ccval), (25, 1, iflag), (23, 2, 0x2),
                                        (22, 1, spsrflag), (17, 5, 0x14), (16, 1, allflag),
                                        (12, 4, 0xF), (0, 12, op2field)])
        return helpers.bigendian_to_littleendian(encoded)


def check_swiop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 1:
        return 'Invalid number of operands: expected 1, got %i' % (len(operands))
    operands = operands[0]
    if not helpers.is_valid_imval(operands):
        return 'Invalid operand: expected immediate value'
    com = helpers.imval_to_int(operands)
    if com > 2**24-1:
        return 'Operand greater than 2^24-1'
    if com < -2**23:
        return 'Operand lower than -2^23'
    return ''


def encode_swiop(name, condcode, operands):
    """
    check_swiop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = operands.strip()
    ccval = helpers.get_condcode_value(condcode)
    com = helpers.imval_to_int(operands)
    encoded = helpers.encode_32bit([(28, 4, ccval), (24, 4, 0xF), (0, 24, com)])
    return helpers.bigendian_to_littleendian(encoded)


def check_miscarithmeticop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 2:
        return 'Invalid number of operands: expected 2, got %i' % (len(operands))
    if not helpers.is_reg(operands[0]):
        return 'Invalid operand: expected register'
    rd = helpers.get_reg_num(operands[0])
    if not helpers.is_reg(operands[1]):
        return 'Invalid operand: expected register'
    rm = helpers.get_reg_num(operands[1])
    if rd == 15 or rm == 15:
        return 'PC is not allowed here'
    return ''

def encode_miscarithmeticop(name, condcode, operands):
    """
    check_miscarithmeticop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    rd = helpers.get_reg_num(operands[0])
    rm = helpers.get_reg_num(operands[1])
    ccval = helpers.get_condcode_value(condcode)
    encoded = helpers.encode_32bit([(28, 4, ccval), (16, 12, 0x16F), (12, 4, rd), (4, 8, 0xF1), (0, 4, rm)])
    return helpers.bigendian_to_littleendian(encoded)

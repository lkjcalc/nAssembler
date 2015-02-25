import helpers

def check_op2(op2):
    """Checks Op2 of a dataprocop
Returns an error string if invalid, empty string otherwise"""
    operands = [x.strip() for x in op2.split(',')]
    if len(operands) == 1:
        if helpers.is_reg(operands[0]):#op2 = reg
            return ''
        if not helpers.is_valid_imval(operands[0]):#op2 = immediate
            return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
        #constant must be expressable as "8bit unsigned int" rotated right by 2*n with n an "4 bit unsigned int"
        const = helpers.imval_to_int(operands[0])
        for i in range(0, 32, 2):#range is [0, 2, 4, ..., 30]
            if helpers.rotateleft32(const, i) < 256:#-> ans ror i = const with ans 8bit and i 4bit
                return ''
        return 'This immediate value cannot be encoded as op2'
    if len(operands) != 2:
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    #->must be of form "reg, shift"
    if not helpers.is_reg(operands[0]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    shift = [x.strip() for x in operands[1].split()]
    if len(shift) == 1:#"RRX" or "shiftname reg" or "shiftname immediate"
        if shift[0] != 'RRX':
            return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
        return ''
    elif len(shift) > 2:
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    if not helpers.is_shiftname(shift[0]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    if helpers.is_reg(shift[1]):
        if helpers.get_reg_num(shift[1]) == 15:
            return 'PC may not be used here'
        return ''
    if not helpers.is_valid_imval(shift[1]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    amount = helpers.imval_to_int(shift[1])
    if amount >= 0 and amount <= 31:
        return ''
    elif amount == 32 and shift[0] not in ['LSR', 'ASR']:
        return 'Shift by 32 is only allowed for LSR'
    return 'Invalid immediate shift amount. Must be 0 <= amount <= 31 (or 32 for special LSR, ASR)'    

def check_dataprocop(name, flags, condcode, operands):
    """Assumes valid name, valid name+flags combination, valid condcode
Checks the operands and returns an error string if invalid, empty string otherwise"""
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) < 2:
        return 'Expected more operands'
    if not helpers.is_reg(operands[0]):#operands can be (reg, op2) or (reg, reg, op2)
        return 'Expected a register as first operand'
    operands.pop(0)
    if name in ['AND', 'EOR', 'SUB', 'RSB', 'ADD', 'ADC', 'SBC', 'RSC', 'ORR', 'BIC']:
        if not helpers.is_reg(operands[0]):
            return 'Expected a register as second operand'
        operands.pop(0)
    if len(operands) < 1:
        return 'Expected more operands'
    return check_op2(','.join(operands))

def encode_dataprocop(name, flags, condcode, operands):
    """check_dataprocop must be called before this
Encodes the instruction and returns it as a bytes object"""
    operands = [x.strip() for x in operands.split(',')]
    sflag = (flags == 'S')
    if helpers.is_dataproc_fullop(name):
        dest = helpers.get_reg_num(operands[0])
        op1 = helpers.get_reg_num(operands[1])
        (iflag, op2) = encode_op2(','.join(operands[2:]))
    elif helpers.is_dataproc_testop(name):
        dest = 0
        op1 = helpers.get_reg_num(operands[0])
        (iflag, op2) = encode_op2(','.join(operands[1:]))
        sflag = True
    else:#movop
        dest = get_reg_num(operands[0])
        op1 = 0
        (iflag, op2) = encode_op2(','.join(operands[1:]))
    ccval = helpers.get_condcode_value(condcode)
    dpn = helpers.get_dataprocop_num(name)
    return helpers.bigendian_to_littleendian(bytes([(ccval << 4) | (iflag << 1) | (dpn >> 3),
                                                    ((dpn & 0x7) << 5) | (sflag << 4) | op1,
                                                    (dest << 4) | ((op2 & 0xF) >> 8),
                                                    op2 & 0xFF]))

def encode_op2(op2):
    """check_op2 must be called before this
Argument op2 must be a string
Encodes the op2. Returns a tuple of I-flag and an integer containing the other 12 bits"""
    operands = [x.strip() for x in op2.split(',')]
    if len(operands) == 1:
        if helpers.is_reg(operands[0]):#op2 = reg
            iflag = False
            reg = helpers.get_reg_num(operands[0])
            shifttype = 'LSL'
            shiftby = 0
            shiftbyreg = False
        else:#op2 = immediate value
            iflag = True
            imval = helpers.imval_to_int(operands[0])
            for i in range(0, 32, 2):#range is [0, 2, 4, ..., 30]
                if helpers.rotateleft32(imval, i) < 256:#-> ans ror i = const with ans 8bit and i 4bit
                    op2field = (i//2 << 8) | helpers.rotateleft32(imval, i)
                    break
    else:
        iflag = False
        reg = helpers.get_reg_num(operands[0])
        shift = [x.strip() for x in operands[1].split()]
        if len(shift) == 1:#RRX
            shifttype = 'ROR'
            shiftby = 0
            shiftbyreg = False
        else:
            shifttype = shift[0]
            if helpers.is_reg(shift[1]):
                shiftby = helpers.get_reg_num(shift[1])
                shiftbyreg = True
            else:
                shiftby = helpers.imval_to_int(shift[1])
                shiftbyreg = False
                if shiftby == 0:
                    shifttype = 'LSL'
                if shifttype in ['LSR', 'ASR'] and shiftby == 32:
                    shiftby = 0
    if not iflag:
        shiftfield = ({'LSL' : 0, 'ASL' : 0, 'LSR' : 1, 'ASR' : 2, 'ROR' : 3}[shifttype] << 1) | shiftbyreg
        if shiftbyreg:
            shiftfield = (shiftby << 4) | shiftfield
        else:
            shiftfield = (shiftby << 3) | shiftfield
        op2field = (shiftfield << 4) | reg
    return (iflag, op2field)

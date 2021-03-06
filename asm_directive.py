import helpers
import filedict


def check_directive(name, operands):
    """
    Assumes valid name.
    Check the operands.
    Return an error string if invalid, empty string otherwise.
    """
    if name == 'DCD' or name == 'DCDU':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0:
            return 'Missing operands after DCD: expected at least one immediate value'
        for op in operands:
            if not helpers.is_valid_numeric_literal(op):
                return 'Invalid numeric literal'
            i = helpers.numeric_literal_to_int(op)
            if i > (2**32)-1:
                return 'Numeric literal outside of 32bit range: greater than 2^32-1'
            if i < -(2**31):
                return 'Numeric literal outside of 32bit range: lower than -2^31'
        return ''
    if name == 'DCW' or name == 'DCWU':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0:
            return 'Missing operands after DCW: expected at least one immediate value'
        for op in operands:
            if not helpers.is_valid_numeric_literal(op):
                return 'Invalid numeric literal'
            i = helpers.numeric_literal_to_int(op)
            if i > (2**16)-1:
                return 'Numeric literal outside of 16bit range: greater than 2^16-1'
            if i < -(2**15):
                return 'Numeric literal outside of 32bit range: lower than -2^15'
        return ''
    if name == 'ALIGN':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0 or len(operands[0]) == 0:  # implicit alignment to 4 bytes
            return ''
        if len(operands) > 2:
            return 'Only two arguments are allowed: alignment, offset'
        if not helpers.is_valid_numeric_literal(operands[0]):
            return 'Invalid numeric literal'
        alignment = helpers.numeric_literal_to_int(operands[0])
        if alignment == 0 or (alignment & (alignment-1)) != 0:
            return 'Only powers of two are allowed as alignment boundaries'
        if len(operands) == 1:
            return ''
        if not helpers.is_valid_numeric_literal(operands[1]):
            return 'Invalid numeric literal'
        return ''
    if name == 'DCB':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0 or len(operands[0]) == 0:
            return 'Missing operands after DCB: expected at least one numeric or string literal'
        for op in operands:
            if len(op) == 0:
                return 'Unexpected comma'
            if op[0] == '"':
                if len(op) < 3:
                    return 'Invalid string literal: empty'
                if op[-1] != '"':
                    return 'Invalid string literal: not terminated'
                op = op[1:-1]
                for c in op:
                    c = ord(c)
                    if c < 0 or c > 255:
                        return 'Invalid character'
            elif helpers.is_valid_numeric_literal(op):
                i = helpers.numeric_literal_to_int(op)
                if i < -128:
                    return 'Numeric literal outside of 8bit range: lower than -2^7'
                if i > 255:
                    return 'Numeric literal outside of 8bit range: greater than 2^8-1'
            else:
                return 'Expected numeric or string literal'
        return ''
    if name == 'INCBIN':
        s = filedict.filecontents(operands)
        if s is None:
            return 'Could not open file "%s"' % (operands)
        return ''
    return 'Invalid name (failed in check_directive) (report as bug)'


def encode_directive(name, operands, address):
    """
    check_directive must be called before this.
    Address must be the address of the directive.
    Encode the directive and return it as a bytes object.
    """
    if name == 'DCD' or name == 'DCDU':
        operands = [x.strip() for x in operands.split(',')]
        encoded = b''
        if name == 'DCD':
            encoded += b'\x00'*((4 - (address % 4)) % 4)  # align
        for op in operands:
            i = helpers.numeric_literal_to_int(op)
            encoded += helpers.bigendian_to_littleendian(helpers.encode_32bit([(0, 32, i)]))
        return encoded
    if name == 'DCW' or name == 'DCWU':
        operands = [x.strip() for x in operands.split(',')]
        encoded = b''
        if name == 'DCW':
            encoded += b'\x00'*(address % 2)  # align
        for op in operands:
            i = helpers.numeric_literal_to_int(op)
            encoded += helpers.bigendian_to_littleendian_16bit(helpers.encode_16bit([(0, 16, i)]))
        return encoded
    if name == 'ALIGN':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0 or len(operands[0]) == 0:  # implicit alignment to 4 bytes
            alignment = 4
        else:
            alignment = helpers.numeric_literal_to_int(operands[0])
        if len(operands) < 2:
            offset = 0
        else:
            offset = helpers.numeric_literal_to_int(operands[1])
        padsize = ((alignment - ((address+alignment-offset) % alignment)) % alignment)
        return padsize*b'\x00'
    if name == 'DCB':
        operands = [x.strip() for x in operands.split(',')]
        encoded = b''
        for op in operands:
            if op[0] == '"':
                op = op[1:-1]
                for c in op:
                    c = ord(c)
                    encoded += bytes([c])
            else:  # is valid numeric literal because has to be checked before
                i = helpers.numeric_literal_to_int(op)
                encoded += bytes([i])
        return encoded
    if name == 'INCBIN':
        return filedict.filecontents(operands)
    return b''  # should never be reached

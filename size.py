import helpers


def get_size(name, operands, address):
    """
    name must be the name of a directive or instruction in uppercase, operands the operands, address the address where it is.
    Return the length of op (in bytes) (assuming passed address),
    or return -1 on failure (invalid name)
    """
    if not helpers.is_opname(name):
        print('DEBUG: TODO remove. not is_opname. "%s"' % (name))
        return -1
    if helpers.is_directive(name):
        return get_directive_size(name, operands, address)
    elif helpers.is_opname(name):
        return get_instruction_size(name, operands, address)
    else:
        issueerror('internal error in get_length')
        return -1


def get_directive_size(name, operands, address):
    """
    Do not check the syntax or the content, just return how many bytes it will be if it is valid.
    name must be the name of a directive in uppercase, operands the operands, address the address where it is.
    Return -1 on failure (invalid name).
    """
    if name == 'DCD' or name == 'DCDU':
        padding = 0
        if name == 'DCD':
            padding = ((4 - (address % 4)) % 4)
        operands = operands.split(',')
        return padding + 4*len(operands)
    elif name == 'DCW' or name == 'DCWU':
        padding = 0
        if name == 'DCW':
            padding = address % 2
        operands = operands.split(',')
        return padding + 2*len(operands)
    elif name == 'ALIGN':
        operands = operands.split(',')
        alignment = 4
        offset = 0
        if operands[0] != '':
            alignment = helpers.imval_to_int('#'+operands[0])
        if len(operands) > 1:
            offset = helpers.imval_to_int('#'+operands[1])
        return ((alignment - ((address+alignment-offset) % alignment)) % alignment)
    elif name == 'DCB':
        size = 0
        operands = operands.split(',')
        for i in operands:
            i = i.strip()
            if i[0] == '"':
                i = i[1:-1]
                size += len(i)
            else:
                size += 1
        return size
    else:
        return -1


def get_instruction_size(name, operands, address):
    """
    Do not check the syntax or the content, just return how many bytes it will be if it is valid.
    name must be the name of a directive in uppercase, operands the operands, address the address where it is.
    Return -1 on failure (invalid name).
    """
    return 4

import helpers


def check_pseudoinstruction(name, operands, address, labeldict):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    if name == 'ADR':
        reg, expr = [x.strip() for x in operands.split(',', maxsplit=1)]
        if not helpers.is_reg(reg):
            return 'Invalid operand: expected register'
        err = helpers.check_pcrelative_expression(expr, labeldict)
        if len(err) != 0:
            return err
        offs = helpers.pcrelative_expression_to_int(expr, address, labeldict)
        sri = helpers.int_to_signrotimv(offs)
        if sri is None:
            return 'Invalid offset: cannot be encoded'
        return ''
    return 'Unknown pseudoinstruction (bug)'


def get_replacement(name, operands, address, labeldict):
    """
    check_pseudoinstruction must be called before this, and it must be a pseudoinstruction.
    Return replacement opname and operands.
    """
    if name == 'ADR':
        reg, expr = [x.strip() for x in operands.split(',', maxsplit=1)]
        offs = helpers.pcrelative_expression_to_int(expr, address, labeldict)
        sign, rot, imv = helpers.int_to_signrotimv(offs)
        if sign == 1:
            newop = 'ADD'
        else:
            newop = 'SUB'
        newoperands = '%s, PC, #%i' % (reg, sign*offs)
        return (newop, newoperands)
    return None

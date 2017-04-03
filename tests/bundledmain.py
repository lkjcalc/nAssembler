##########IMPORT START############
_files = {}
_sourcefolder = None

def set_sourcepath(path):
    """
    Set the path of the source file which is currently being assembled.
    """
    global _sourcefolder
    bs = path.rfind('/')
    _sourcefolder = path[:bs+1]

def _abspath(curpath, path):
    """
    Calculate absolute path of path assuming current directory is curpath.
    """
    if path.startswith('../'):
        parpath = curpath
        while path.startswith('../'):
            pari = parpath.rfind('/', 0, -1)
            parpath = parpath[:pari+1]
            path = path[3:]
        abspath = parpath + path
    elif path.startswith('./'):
        abspath = curpath + path[2:]
    elif path.startswith('/'):
        abspath = path
    else:
        abspath = curpath + path
    return abspath

def add_file(path):
    """
    Read the file at path, return size or if fails return -1.
    set_sourcepath needs to be called at some point before using this function.
    If the same file has been added before, it is not read again, and the same size is returned.
    """
    abspath = _abspath(_sourcefolder, path)
    if abspath in _files:
        return len(_files[abspath])
    try:
        f = open(abspath, 'rb')
        s = f.read()
        f.close()
        size = len(s)
        _files[abspath] = s
    except Exception as e:
        print(e)
        size = -1
    return size

def filecontents(path):
    """
    Return the contents of file at path, or None if file is not in 
    add_file needs to be called on the same file before using this.
    """
    abspath = _abspath(_sourcefolder, path)
    return _files.get(abspath)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############
def reverse(b):  # needed because no [::-1] available in upy
    """Return the reversed bytearray b."""
    tmp = []
    for c in b:
        tmp.insert(0, c)
    return bytearray(tmp)


def int_to_signrotimv(n):
    """
    Return a tuple (sign, rot, imv) such that sign*ROR(imv,2*rot) == n,
    and such that sign = +-1, 0<=rot<=15, 0<=imv<=255, or None if that is impossible.
    """
    for i in range(0, 32, 2):
        if rotateleft32(n, i) < 256:  # -> ans ror i = n with ans 8bit and i 4bit
            sign = 1
            rot = i//2
            imv = rotateleft32(n, i)
            return (sign, rot, imv)
        if rotateleft32(-n, i) < 256:
            sign = -1
            rot = i//2
            imv = rotateleft32(-n, i)
            return (sign, rot, imv)
    return None


def _check_aropexpr(s):
    """
    Return '' if s specifies an aropexpr, otherwise nonempty error string,
    where an aropexpr is an expression of the form arop expr,
    where arop is + or - and expr is num or num aropexpr, where is_valid_imval('#'+num) returns True.
    """
    s = s.strip()
    if len(s) == 0:
        return 'invalid epxression: expected nonempty string'
    if s[0] not in ('+', '-'):
        return 'invalid expression: expected "+" or "-"'
    s = s[1:]
    i = len(s)
    if '+' in s:
        i = s.find('+')
    if '-' in s:
        i = min(i, s.find('-'))
    num = s[:i].strip()
    rest = s[i:].strip()
    if not is_valid_imval('#'+num):
        return 'invalid expression: expected numeric immediate value'
    if len(rest) == 0:
        return ''
    return _check_aropexpr(rest)


def check_pcrelative_expression(s, labeldict):
    """Return '' if s specifies a pc relative expression, otherwise nonempty error string."""
    for i in range(len(s)):
        if (not isalnum(s[i])) and s[i] != '_':
            label = s[:i]
            rest = s[i:]
            break
    else:
        label = s
        rest = ''
    label.strip()
    rest.strip()
    if label not in labeldict:
        return 'invalid pc relative expression: undefined label'
    if len(rest) == 0:
        return ''
    return _check_aropexpr(rest)


def _aropexpr_to_int(s):
    """
    s must be a valid aropexpr.
    Return the integer that the expression evaluates to.
    """
    s = s.strip()
    sign = 1
    if s[0] == '-':
        sign = -1
    s = s[1:]
    i = len(s)
    if '+' in s:
        i = s.find('+')
    if '-' in s:
        i = min(i, s.find('-'))
    num = s[:i].strip()
    rest = s[i:].strip()
    numint = imval_to_int('#'+num)
    if len(rest) == 0:
        return sign*numint
    return sign*numint + _aropexpr_to_int(rest)


def pcrelative_expression_to_int(s, address, labeldict):
    """
    s must be a valid pc relative expression.
    Return the offset that the expression evaluates to (with correction for PC==address+8).
    """
    for i in range(len(s)):
        if (not isalnum(s[i])) and s[i] != '_':
            label = s[:i]
            rest = s[i:]
            break
    else:
        label = s
        rest = ''
    label.strip()
    rest.strip()
    offset = labeldict[label] - (address + 8)
    if len(rest) == 0:
        return offset
    return offset + _aropexpr_to_int(rest)


def is_coprocreg(s):
    """Return True if s specifies a coprocessor register, False otherwise."""
    coprocreglist = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10', 'c11', 'c12', 'c13', 'c14', 'c15']
    return s.lower() in coprocreglist


def is_coproc(s):
    """Return True if s specifies a coprocessor, False otherwise."""
    coproclist = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15']
    return s.upper() in coproclist


def encode_imval(s):
    """
    s must be a syntactically valid, encodable immediate value.
    Return the imval encoded as in psrtrans/dataproc.
    """
    imval = imval_to_int(s)
    op2field = 0
    for i in range(0, 32, 2):  # range is [0, 2, 4, ..., 30]
        if rotateleft32(imval, i) < 256:  # -> ans ror i = const with ans 8bit and i 4bit
            op2field = (i//2 << 8) | rotateleft32(imval, i)
            break
    return op2field


def is_expressable_imval(s):
    """
    s must be a syntactically valid immediate value.
    Return True if s can be expressed as an 8 bit imval and 4 bit shift (like in psrtrans or dataproc), False otherwise.
    """
    const = imval_to_int(s)
    for i in range(0, 32, 2):  # range is [0, 2, 4, ..., 30]
        if rotateleft32(const, i) < 256:  # -> ans ror i = const with ans 8bit and i 4bit
            return True
    return False


def is_psr(s):
    """Returns True if s is the name of a cpsr or spsr, False otherwise."""
    psrlist = ['CPSR', 'SPSR', 'CPSR_ALL', 'SPSR_ALL', 'SPSR_FLG', 'CPSR_FLG']
    return s.upper() in psrlist


def encode_32bit(l):
    """
    Encode an instruction (32 bit only) using l to determine contents and positions.
    l must be a list of tuples of 3 integers: (offset, length, value). LSB has offset 0.
    Attention: does not change endianness.
    Return the encoded instruction as a bytearray object.
    """
    word = 0
    for e in l:
        word = word | ((e[2] & ((1 << e[1])-1)) << e[0])
    return bytearray([(word >> 24) & 0xFF, (word >> 16) & 0xFF, (word >> 8) & 0xFF, word & 0xFF])


def encode_16bit(l):
    """
    Encode a 16bit value using l to determine contents and positions.
    l must be a list of tuples of 3 integers: (offset, length, value). LSB has offset 0.
    Attention: does not change endianness.
    Return the encoded instruction as a bytearray object.
    """
    word = 0
    for e in l:
        word = word | ((e[2] & ((1 << e[1])-1)) << e[0])
    return bytearray([(word >> 8) & 0xFF, word & 0xFF])


def is_valid_numeric_literal(s):
    """Return True if '#'+s is a valid immediate value, False otherwise."""
    return is_valid_imval('#'+s)


def numeric_literal_to_int(s):
    """
    Return value of the numeric literal s.
    s must be a syntactically valid numeric literal, or the result is meaningless.
    """
    return imval_to_int('#'+s)


def bigendian_to_littleendian(b):
    """
    Convert bytearray object b from big endian to little endian.
    len(b)%4 must be 0.
    """
    outstr = bytearray()
    if len(b) % 4:
        return bytearray()
    for i in range(0, len(b), 4):
        r = reverse(b[i:i+4])
        for c in r:
            outstr.append(c)
    return outstr


def bigendian_to_littleendian_16bit(b):
    """
    Convert bytearray object b from big endian to little endian,
    assuming it is an array of 16bit values.
    len(b)%2 must be 0.
    """
    outstr = bytearray()
    if len(b) % 2:
        return bytearray()
    for i in range(0, len(b), 2):
        r = reverse(b[i:i+2])
        for c in r:
            outstr.append(c)
    return outstr


def rotateleft32(n, r):
    """Return n % (2**32) rotated left by r bits, using a word size of 32 bits."""
    n &= 0xFFFFFFFF
    r %= 32
    n <<= r
    carry = (n & (0xFFFFFFFF << 32)) >> 32
    n &= 0xFFFFFFFF
    n += carry
    return n


def isalnum(s):
    """Return True if s contains at least one char and only alphanumeric chars (0...9A...Za...z), False otherwise."""
    if len(s) == 0:
        return False
    for c in s:
        if c not in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            return False
    return True


def isxdigit(s):
    """Return True if s contains at least one char and only xdigits (0...9A...Fa...f), False otherwise."""
    if len(s) == 0:
        return False
    for c in s:
        if c not in '0123456789ABCDEFabcdef':
            return False
    return True


def isoctdigit(s):
    """Return True if s contains at least one char and only digits 0...7, False otherwise."""
    if len(s) == 0:
        return False
    for c in s:
        if c not in '01234567':
            return False
    return True


def isbindigit(s):
    """Return True if s contains at least one char and only digits 0 and 1, False otherwise."""
    if len(s) == 0:
        return False
    for c in s:
        if c not in '01':
            return False
    return True


def is_shiftname(s):
    """Return True if s is a shiftname (excluding RRX), False otherwise."""
    shiftnamelist = ['ASL', 'LSL', 'LSR', 'ASR', 'ROR']
    return s.upper() in shiftnamelist


def is_valid_imval(s):
    """Return True if s is a syntactically valid immediate value, False otherwise."""
    if len(s) < 2:
        return False
    if s[0] != '#':
        return False
    if s[1] in ['-', '+'] and len(s) >= 3:
        s = s[0]+s[2:]
    if s == '#0':
        return True
    if s.startswith('#\'') and s[-1] == '\'' and len(s) == 4 and ord(s[2]) <= 255:
        return True
    if s.startswith('#0x') and len(s) >= 4 and isxdigit(s[3:]):
        return True
    if s.startswith('#0') and len(s) >= 3 and isoctdigit(s[2:]):
        return True
    if s.startswith('#0b') and len(s) >= 4 and isbindigit(s[3:]):
        return True
    if s[1] != '0' and str.isdigit(s[1:]):
        return True
    return False


def imval_to_int(s):
    """
    Return value of the immediate value s.
    s must be a syntactically valid immediate value, or the result is meaningless.
    """
    sign = 1
    if s[1] == '-':
        sign = -1
        s = s[0]+s[2:]
    elif s[1] == '+':
        s = s[0]+s[2:]
    if s == '#0':
        val = 0
    elif s.startswith('#\'') and s[-1] == '\'' and len(s) == 4:
        val = ord(s[2])
    elif s.startswith('#0x'):
        val = int(s[3:], 16)
    elif s.startswith('#0b'):
        val = int(s[3:], 2)
    elif s.startswith('#0'):
        val = int(s[2:], 8)
    else:
        val = int(s[1:])
    return sign*val


def is_valid_label(s):
    """
    Return True if s is a syntactically valid label, False otherwise.
    Rules: must start with an alphabetic character, must only contain alphanumeric characters or underscores.
    """
    if not s[0].isalpha():
        return False
    for c in s:
        if isalnum(c) or c == '_':
            continue
        return False
    return True


def is_private_label(s):
    """
    Return True if s is a reserved label name, False otherwise.
    Currently, only assembly "keywords" are reserved
    """
    if is_directive(s) or is_opname(s) or is_reg(s) or is_otherkeyword(s):
        return True
    return False


def is_otherkeyword(s):
    """Return True if s is another keyword than an opname, directive or reg, False otherwise."""
    if s.upper() in ['LSL', 'LSR', 'ASL', 'ASR', 'ROR', 'RRX']:
        return True
    if s.upper() in ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15']:
        return True
    if s.upper() in ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15']:
        return True
    if s.upper() in ['CPSR', 'SPSR', 'CPSR_ALL', 'SPSR_ALL', 'SPSR_FLG', 'CPSR_FLG']:
        return True
    return False


def get_reg_num(s):
    """Return the register number of the register with name s, or -1 if no such register exists."""
    regdict = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7, 'R8': 8, 'R9': 9, 'R10': 10,
               'R11': 11, 'R12': 12, 'R13': 13, 'SP': 13, 'R14': 14, 'LR': 14, 'R15': 15, 'PC': 15}
    s = s.upper()
    if s in regdict:
        return regdict[s]
    return -1


def is_reg(s):
    """Return True if s names a register, False otherwise."""
    return get_reg_num(s) != -1


def get_condcode_value(s):
    """Return the number corresponding to s or -1 if s is not a valid condition code.s"""
    condcodedict = {'EQ': 0, 'NE': 1, 'HS': 2, 'CS': 2, 'LO': 3, 'CC': 3, 'MI': 4, 'PL': 5, 'VS': 6, 'VC': 7, 'HI': 8,
                    'LS': 9, 'GE': 10, 'LT': 11, 'GT': 12, 'LE': 13, 'AL': 14}
    if s.upper() in condcodedict:
        return condcodedict[s.upper()]
    return -1


def is_condcode(s):
    """Return True if s is a valid condcode, False otherwise."""
    return get_condcode_value(s) != -1


def is_directive(s):
    """Return True if s is an (implemented) directive, False otherwise."""
    directivelist = ['DCD', 'DCDU', 'DCW', 'DCWU', 'ALIGN', 'DCB', 'INCBIN']
    return s.upper() in directivelist


def is_dataproc_fullop(s):
    fulloplist = ['ADC', 'ADD', 'RSB', 'RSC', 'SBC', 'SUB', 'AND', 'BIC', 'EOR', 'ORR']
    return s.upper() in fulloplist


def is_dataproc_testop(s):
    testoplist = ['CMP', 'CMN', 'TEQ', 'TST']
    return s.upper() in testoplist


def is_dataproc_movop(s):
    movoplist = ['MOV', 'MVN']
    return s.upper() in movoplist


def get_dataprocop_num(s):
    dataprocopdict = {'ADC': 5, 'ADD': 4, 'RSB': 3, 'RSC': 7, 'SBC': 6, 'SUB': 2, 'AND': 0, 'BIC': 14,
                      'EOR': 1, 'ORR': 12, 'CMP': 10, 'CMN': 11, 'TEQ': 9, 'TST': 8, 'MOV': 13, 'MVN': 15}
    if s.upper() in dataprocopdict:
        return dataprocopdict[s.upper()]
    return -1


def is_dataprocop(s):
    dataprocoplist = ['ADC', 'ADD', 'RSB', 'RSC', 'SBC', 'SUB', 'AND', 'BIC', 'EOR', 'ORR', 'CMP', 'CMN', 'TEQ', 'TST', 'MOV', 'MVN',
                      'ADCS', 'ADDS', 'RSBS', 'RSCS', 'SBCS', 'SUBS', 'ANDS', 'BICS', 'EORS', 'ORRS', 'MOVS', 'MVNS']
    return s.upper() in dataprocoplist


def is_branchop(s):
    branchoplist = ['BX', 'B', 'BL']
    return s.upper() in branchoplist


def is_psrtransop(s):
    psrtransoplist = ['MSR', 'MRS']
    return s.upper() in psrtransoplist


def is_mulop(s):
    muloplist = ['MUL', 'MLA', 'MULS', 'MLAS']
    return s.upper() in muloplist


def is_longmulop(s):
    longmuloplist = ['UMULL', 'SMULL', 'UMLAL', 'SMLAL', 'UMULLS', 'SMULLS', 'UMLALS', 'SMLALS']
    return s.upper() in longmuloplist


def is_swiop(s):
    swioplist = ['SWI', 'SVC']
    return s.upper() in swioplist


def is_singledatatransop(s):
    singledatatransoplist = ['LDR', 'STR', 'LDRB', 'STRB', 'LDRT', 'STRT', 'LDRBT', 'STRBT']
    return s.upper() in singledatatransoplist


def is_halfsigneddatatransop(s):
    halfsigneddatatransoplist = ['LDRH', 'LDRSH', 'LDRSB', 'STRH']
    return s.upper() in halfsigneddatatransoplist


def is_swapop(s):
    swapoplist = ['SWP', 'SWPB']
    return s.upper() in swapoplist


def is_blockdatatransop(s):
    blockdatatransoplist = ['LDMFD', 'LDMED', 'LDMFA', 'LDMEA', 'LDMIA', 'LDMIB', 'LDMDA', 'LDMDB',
                            'STMFD', 'STMED', 'STMFA', 'STMEA', 'STMIA', 'STMIB', 'STMDA', 'STMDB']
    return s.upper() in blockdatatransoplist


def is_coprocregtransop(s):
    coprocregtransoplist = ['MRC', 'MCR']
    return s.upper() in coprocregtransoplist


def is_pseudoinstructionop(s):
    pseudoinstructionoplist = ['ADR']
    return s.upper() in pseudoinstructionoplist


def is_miscarithmeticop(s):
    miscarithmeticoplist = ['CLZ']
    return s.upper() in miscarithmeticoplist


def is_opname(s):
    """Return True if s is a valid operation or directive name (full name, i.e. with flags!), False otherwise."""
    return is_directive(s) or is_dataprocop(s) or is_branchop(s) or is_psrtransop(s) or is_mulop(s)\
        or is_longmulop(s) or is_swiop(s) or is_singledatatransop(s) or is_halfsigneddatatransop(s)\
        or is_swapop(s) or is_blockdatatransop(s) or is_coprocregtransop(s) or is_pseudoinstructionop(s)\
        or is_miscarithmeticop(s)


def is_conditionable(s):
    """Check if s can be conditionally executed. Return True if yes, False if no."""
    return not is_directive(s) and is_opname(s)


def is_pseudoinstruction(opname, operands):
    """Check if opname operands is a pseudoinstruction. Return True if yes, False if no."""
    return is_pseudoinstructionop(opname)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



def check_pseudoinstruction(name, operands, address, labeldict):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    if name == 'ADR':
        reg, expr = [x.strip() for x in operands.split(',', 1)]
        if not is_reg(reg):
            return 'Invalid operand: expected register'
        err = check_pcrelative_expression(expr, labeldict)
        if len(err) != 0:
            return err
        offs = pcrelative_expression_to_int(expr, address, labeldict)
        sri = int_to_signrotimv(offs)
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
        reg, expr = [x.strip() for x in operands.split(',', 1)]
        offs = pcrelative_expression_to_int(expr, address, labeldict)
        sign, rot, imv = int_to_signrotimv(offs)
        if sign == 1:
            newop = 'ADD'
        else:
            newop = 'SUB'
        newoperands = '%s, PC, #%i' % (reg, sign*offs)
        return (newop, newoperands)
    return None
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



def check_op2(op2):
    """
    Check Op2 of a dataprocop.
    Return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in op2.split(',')]
    if len(operands) == 1:
        if is_reg(operands[0]):  # op2 = reg
            return ''
        if not is_valid_imval(operands[0]):  # op2 = immediate
            return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
        # constant must be expressable as "8bit unsigned int" rotated right by 2*n with n an "4 bit unsigned int"
        if not is_expressable_imval(operands[0]):
            return 'This immediate value cannot be encoded as op2'
        return ''
    if len(operands) != 2:
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    # ->must be of form "reg, shift"
    if not is_reg(operands[0]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    if '#' in operands[1]:
        operands[1] = operands[1][:operands[1].find('#')]+' '+operands[1][operands[1].find('#'):]  # make it legal to omit the space between shiftname and immediate value
    shift = [x.strip() for x in operands[1].split()]
    if len(shift) == 1:  # "RRX" or "shiftname reg" or "shiftname immediate"
        if shift[0] != 'RRX':
            return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
        return ''
    elif len(shift) > 2:
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    if not is_shiftname(shift[0]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    if is_reg(shift[1]):
        if get_reg_num(shift[1]) == 15:
            return 'PC may not be used here'
        return ''
    if not is_valid_imval(shift[1]):
        return 'Invalid op2 (must be of the form "reg" or "reg, shift" or "immediate value")'
    amount = imval_to_int(shift[1])
    if amount >= 0 and amount <= 31:
        return ''
    elif amount == 32 and shift[0] not in ['LSR', 'ASR']:
        return 'Shift by 32 is only allowed for LSR'
    return 'Invalid immediate shift amount. Must be 0 <= amount <= 31 (or 32 for special LSR, ASR)'


def check_dataprocop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) < 2:
        return 'Expected more operands'
    if not is_reg(operands[0]):  # operands can be (reg, op2) or (reg, reg, op2)
        return 'Expected a register as first operand'
    operands.pop(0)
    if name in ['AND', 'EOR', 'SUB', 'RSB', 'ADD', 'ADC', 'SBC', 'RSC', 'ORR', 'BIC']:
        if not is_reg(operands[0]):
            return 'Expected a register as second operand'
        operands.pop(0)
    if len(operands) < 1:
        return 'Expected more operands'
    return check_op2(','.join(operands))


def encode_dataprocop(name, flags, condcode, operands):
    """
    check_dataprocop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    sflag = (flags == 'S')
    if is_dataproc_fullop(name):
        dest = get_reg_num(operands[0])
        op1 = get_reg_num(operands[1])
        (iflag, op2) = encode_op2(','.join(operands[2:]))
    elif is_dataproc_testop(name):
        dest = 0
        op1 = get_reg_num(operands[0])
        (iflag, op2) = encode_op2(','.join(operands[1:]))
        sflag = True
    else:  # movop
        dest = get_reg_num(operands[0])
        op1 = 0
        (iflag, op2) = encode_op2(','.join(operands[1:]))
    ccval = get_condcode_value(condcode)
    dpn = get_dataprocop_num(name)
    encoded = encode_32bit([(28, 4, ccval), (25, 1, iflag), (21, 4, dpn), (20, 1, sflag),
                                    (16, 4, op1), (12, 4, dest), (0, 12, op2)])
    return bigendian_to_littleendian(encoded)


def encode_op2(op2):
    """
    check_op2 must be called before this.
    Argument op2 must be a string.
    Encode the op2. Return a tuple of I-flag and an integer containing the other 12 bits.
    """
    operands = [x.strip() for x in op2.split(',')]
    if len(operands) == 1:
        if is_reg(operands[0]):  # op2 = reg
            iflag = False
            reg = get_reg_num(operands[0])
            shifttype = 'LSL'
            shiftby = 0
            shiftbyreg = False
        else:  # op2 = immediate value
            iflag = True
            op2field = encode_imval(operands[0])
    else:
        iflag = False
        reg = get_reg_num(operands[0])
        if '#' in operands[1]:
            operands[1] = operands[1][:operands[1].find('#')]+' '+operands[1][operands[1].find('#'):]  # make it legal to omit the space between shiftname and immediate value
        shift = [x.strip() for x in operands[1].split()]
        if len(shift) == 1:  # RRX
            shifttype = 'ROR'
            shiftby = 0
            shiftbyreg = False
        else:
            shifttype = shift[0]
            if is_reg(shift[1]):
                shiftby = get_reg_num(shift[1])
                shiftbyreg = True
            else:
                shiftby = imval_to_int(shift[1])
                shiftbyreg = False
                if shiftby == 0:
                    shifttype = 'LSL'
                if shifttype.upper() in ['LSR', 'ASR'] and shiftby == 32:
                    shiftby = 0
    if not iflag:
        shiftfield = ({'LSL': 0, 'ASL': 0, 'LSR': 1, 'ASR': 2, 'ROR': 3}[shifttype.upper()] << 1) | shiftbyreg
        if shiftbyreg:
            shiftfield = (shiftby << 4) | shiftfield
        else:
            shiftfield = (shiftby << 3) | shiftfield
        op2field = (shiftfield << 4) | reg
    return (iflag, op2field)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



def is_valid_addresspart(hsflag, addresspart, tflag, address, labeldict):
    """
    hsflag = True -> selects syntax checking for halfword or signed data transfer instructions, False selects normal unsigned word/byte transfer syntax.
    Address must be the address of this instruction.
    Return empty string if addresspart is valid according to the syntax rules for datatransfer address part, error string otherwise.
    """
    if len(addresspart) < 1:
        return 'Address part is missing'
    if addresspart[0] != '[':  # must be an expression (label) if not starting with a bracket
        if addresspart not in labeldict:
            return 'Expected bracket or label'
        offset = labeldict[addresspart] - address - 8
        addresspart = '[PC, #'+str(offset)+']'  # range check done below
    writeback = False
    if addresspart[-1] == '!':
        writeback = True
        addresspart = addresspart[:-1].strip()  # strip the trailing !
    if addresspart[-1] == ']':
        preindexed = True
        addresspart = addresspart[:-1].strip()  # strip the trailing ]
    else:
        if writeback:
            return '! is only allowed for preindexed addressing'
        preindexed = False
    addresspart = addresspart[1:].strip()  # strip the leading [
    addresspart = [x.strip() for x in addresspart.split(',')]
    if len(addresspart) < 1 or len(addresspart) > 3 or (hsflag and len(addresspart) > 2):
        return 'Invalid addresspart'
    if not preindexed:
        if addresspart[0][-1:] != ']':
            return 'Expected closing ]'
        addresspart[0] = addresspart[0][:-1].strip()  # strip the trailing ]
    # there should be no syntax differences between pre- and post-indexing left
    if not is_reg(addresspart[0]):
        return 'Expected register as base'
    if writeback and get_reg_num(addresspart[0]) == 15:
        return 'Write-back should not be used when PC is the base register'
    if preindexed and tflag:
        return 'T-flag is not allowed when pre-indexing is used'
    if len(addresspart) == 1:
        return ''
    if is_valid_imval(addresspart[1]):
        n = imval_to_int(addresspart[1])
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
        if not is_reg(addresspart[1]):
            return 'Invalid offset: must be register or immediate value'
        if get_reg_num(addresspart[1]) == 15:
            return 'PC is not allowed as offset'
        if not preindexed and get_reg_num(addresspart[0]) == get_reg_num(addresspart[1]):
            return 'Manual says: post-indexed with Rm = Rn should not be used'
        if len(addresspart) == 2:
            return ''
        if hsflag:
            return 'Expected less operands'
        # addresspart[2] should be a shift:
        if len(addresspart[2]) < 3:
            return 'Invalid shift expression'
        shift = addresspart[2]
        if shift.upper() == 'RRX':
            return ''
        shift = shift.split()
        if len(shift) == 1 and '#' in shift[0]:
            shift = shift[0].split('#')
            shift[1] = '#' + shift[1]
        if len(shift) != 2:
            return 'Invalid shift expression'
        if not is_shiftname(shift[0]):
            return 'Invalid shift name'
        if is_reg(shift[1]):
            return 'Register specified shift amount is not allowed in data transfer instructions'
        if not is_valid_imval(shift[1]):
            return 'Invalid shift amount'
        n = imval_to_int(shift[1])
        if n >= 0 and n <= 31:
            return ''
        elif n == 32 and shift[0] not in ['LSR', 'ASR']:
            return 'Shift by 32 is only allowed for LSR'
        return 'Invalid immediate shift amount. Must be 0 <= amount <= 31 (or 32 for special LSR, ASR)'


def check_singledatatransop(flags, operands, address, labeldict):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    tflag = 'T' in flags
    operands = [x.strip() for x in operands.split(',', 1)]
    if len(operands) != 2:
        return 'Expected more operands'
    if not is_reg(operands[0]):
        return 'Expected register'
    err = is_valid_addresspart(False, operands[1], tflag, address, labeldict)
    if len(err) > 0:
        return err
    return ''


def check_halfsigneddatatransop(operands, address, labeldict):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',', 1)]
    if len(operands) != 2:
        return 'Expected more operands'
    if not is_reg(operands[0]):
        return 'Expected register'
    err = is_valid_addresspart(True, operands[1], False, address, labeldict)
    if len(err) > 0:
        return err
    return ''


def parse_datatrans(name, operands, address, labeldict):
    """
    check_singledatatransop or check_halfsigneddatatransop must be called before this.
    Does the stuff common to halfsigned and normal datatrans encoding.
    """
    if operands.count('[') == 0:
        label = operands.split(',')[1].strip()
        offset = labeldict[label] - address - 8
        operands = operands.split(',')[0] + ',[PC, #'+str(offset)+']'
    writeback = (operands[-1] == '!')
    if writeback:
        operands = operands[:-1].strip()
    preindexed = (operands[-1] == ']')
    if preindexed:
        operands = operands[:-1].strip()
    loadflag = (name == 'LDR')
    operands = [x.strip() for x in operands.split(',')]
    operands[1] = operands[1][1:].strip()
    if operands[1][-1] == ']':
        operands[1] = operands[1][:-1].strip()
    rd = get_reg_num(operands[0])
    rn = get_reg_num(operands[1])
    offset = 0
    upflag = True
    iflag = False
    if len(operands) > 2:
        if is_valid_imval(operands[2]):
            iflag = False  # !!!
            offset = imval_to_int(operands[2])
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
            rm = get_reg_num(operands[2])
            shiftfield = 0
            if len(operands) == 4:
                shift = [x.strip() for x in operands[3].split()]
                if len(shift) == 1:  # RRX
                    shifttype = 'ROR'
                    shiftby = 0
                else:
                    shifttype = shift[0]
                    shiftby = imval_to_int(shift[1])
                    if shiftby == 0:
                        shifttype = 'LSL'
                    if shifttype.upper() in ['LSR', 'ASR'] and shiftby == 32:
                        shiftby = 0
                shiftfield = (shiftby << 3) | {'LSL': 0, 'ASL': 0, 'LSR': 1, 'ASR': 2, 'ROR': 3}[shifttype.upper()] << 1
            offset = (shiftfield << 4) | rm
    return (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset)


def encode_singledatatransop(name, flags, condcode, operands, address, labeldict):
    """
    check_singledatatransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset) = parse_datatrans(name, operands, address, labeldict)
    if 'T' in flags:
        writeback = True
    byteflag = ('B' in flags)
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (26, 2, 0x1), (25, 1, iflag),
                                    (24, 1, preindexed), (23, 1, upflag), (22, 1, byteflag),
                                    (21, 1, writeback), (20, 1, loadflag), (16, 4, rn),
                                    (12, 4, rd), (0, 12, offset)])
    return bigendian_to_littleendian(encoded)


def encode_halfsigneddatatransop(name, flags, condcode, operands, address, labeldict):
    """
    check_halfsigneddatatransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    (writeback, preindexed, loadflag, upflag, iflag, rd, rn, offset) = parse_datatrans(name, operands, address, labeldict)
    assert not (offset & 0xF00)  # either iflag and only lowest 4 bit used or not iflag and only lowest 8 bit used
    assert (not iflag) or not (offset & 0xFF0)
    hflag = ('H' in flags)
    sflag = ('S' in flags)
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (24, 1, preindexed), (23, 1, upflag),
                                    (22, 1, not iflag), (21, 1, writeback), (20, 1, loadflag),
                                    (16, 4, rn), (12, 4, rd), (8, 4, offset >> 4), (7, 1, 0x1),
                                    (6, 1, sflag), (5, 1, hflag), (4, 1, 0x1), (0, 4, offset)])
    return bigendian_to_littleendian(encoded)


def check_swapop(operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 3:
        return 'Expected 3 operands, got %i' % (len(operands))
    if len(operands[2]) < 4:
        return 'Invalid syntax'
    if operands[2][0] != '[' or operands[2][-1] != ']':
        return 'Missing brackets around third operand of swap instruction'
    operands[2] = operands[2][1:-1].strip()
    for op in operands:
        if not is_reg(op):
            return 'Only registers are allowed here'
    for op in operands:
        if get_reg_num(op) == 15:
            return 'PC is not allowed here'
    return ''


def encode_swapop(name, flags, condcode, operands):
    """
    check_swapop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    operands[2] = operands[2][1:-1].strip()
    operands = [get_reg_num(x) for x in operands]
    byteflag = (flags == 'B')
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (23, 5, 0x2), (22, 1, byteflag),
                                    (16, 4, operands[2]), (12, 4, operands[0]),
                                    (4, 4, 0x9), (0, 4, operands[1])])
    return bigendian_to_littleendian(encoded)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



def check_coprocregtransop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 5 and len(operands) != 6:
        return 'Invalid number of operands. Expected 5 or 6, got %i' % len(operands)
    if not is_coproc(operands[0]):
        return 'Expected coprocessor (e.g. p15)'
    if not is_valid_numeric_literal(operands[1]):
        return 'Expected numeric literal'
    if not 0 <= numeric_literal_to_int(operands[1]) <= 7:
        return 'Must be in range 0 to 7'
    if not is_reg(operands[2]):
        return 'Expected register'
    if not is_coprocreg(operands[3]) or not is_coprocreg(operands[4]):
        return 'Expected coprocessor register (e.g. c0)'
    if len(operands) == 5:
        return ''
    if not is_valid_numeric_literal(operands[5]):
        return 'Expected numeric literal'
    if not 0 <= numeric_literal_to_int(operands[5]) <= 7:
        return 'Must be in range 0 to 7'
    return ''


def encode_coprocregtransop(name, condcode, operands):
    """
    check_coprocregtransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    cpnum = int(operands[0][1:])
    cpopc = numeric_literal_to_int(operands[1])
    rd = get_reg_num(operands[2])
    crn = int(operands[3][1:])
    crm = int(operands[4][1:])
    if len(operands) == 6:
        cp = numeric_literal_to_int(operands[5])
    else:
        cp = 0
    lflag = (name == 'MRC')
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (24, 4, 0xE), (21, 3, cpopc),
                                    (20, 1, lflag), (16, 4, crn), (12, 4, rd),
                                    (8, 4, cpnum), (5, 3, cp), (4, 1, 0x1), (0, 4, crm)])
    return bigendian_to_littleendian(encoded)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



def check_blockdatatransop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',', 1)]
    if len(operands) < 2:
        return 'Too few operands'
    if len(operands[0]) < 2:
        return 'Invalid operand'
    if operands[0][-1] == '!':
        writeback = True
        operands[0] = operands[0][:-1].strip()
    else:
        writeback = False
    if not is_reg(operands[0]):
        return 'Expected register'
    base = get_reg_num(operands[0])
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
            r = [x.strip() for x in op.split('-')]
            if len(r) > 2:
                return 'Invalid syntax'
            if not is_reg(r[0]) or not is_reg(r[1]):
                return 'Expected register'
            start = get_reg_num(r[0])
            end = get_reg_num(r[1])
            if start >= end:
                return 'Registers must be specified in ascending order'
            reglist += list(range(start, end+1))  # upy needs explicit conversion
        else:
            if not is_reg(op):
                return 'Expected register'
            reglist.append(get_reg_num(op))
    for i in range(0, len(reglist)-1):
        if reglist[i] >= reglist[i+1]:
            return 'Registers must be specified in ascending order'
    if sbit and writeback and (name == 'STM' or (name == 'LDM' and 15 not in reglist)):
        return 'Writeback may not be used combined with user bank transfer'
    if writeback and name == 'LDM' and base in reglist:
        return 'Attention: Writeback is useless here because the loaded value will overwrite it'
    return ''


def encode_blockdatatransop(name, flags, condcode, operands):
    """
    check_blockdatatransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    if operands[0][-1] == '!':
        writeback = True
        operands[0] = operands[0][:-1].strip()
    else:
        writeback = False
    base = get_reg_num(operands[0])
    if operands[-1][-1] == '^':
        sbit = True
        operands[-1] = operands[-1][:-1].strip()
    else:
        sbit = False
    operands[1] = operands[1][1:].strip()  # strip the curly brackets
    operands[-1] = operands[-1][:-1].strip()
    reglist = []
    for op in operands[1:]:
        if '-' in op:
            (start, end) = [get_reg_num(r.strip()) for r in op.split('-')]
            reglist += list(range(start, end+1))  # upy needs explicit conversion
        else:
            reglist.append(get_reg_num(op))
    regfield = 0
    for r in reglist:
        regfield |= (1 << r)
    lflag = (name == 'LDM')
    addrmodedict = {'ED': (lflag, lflag), 'IB': (1, 1), 'FD': (lflag, not lflag),
                    'IA': (1, 0), 'EA': (not lflag, lflag), 'DB': (0, 1),
                    'FA': (not lflag, not lflag), 'DA': (0, 0)}
    (uflag, pflag) = addrmodedict[flags]
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (25, 3, 0x4), (24, 1, pflag),
                                    (23, 1, uflag), (22, 1, sbit), (21, 1, writeback),
                                    (20, 1, lflag), (16, 4, base), (0, 16, regfield)])
    return bigendian_to_littleendian(encoded)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############




def get_size(name, operands, address):
    """
    name must be the name of a directive or instruction in uppercase, operands the operands, address the address where it is.
    Return the length of op (in bytes) (assuming passed address) and store included files using filedict,
    or return -1 on failure (invalid name)
    """
    if not is_opname(name):
        print('DEBUG: TODO remove. not is_opname. "%s"' % (name))
        return -1
    if is_directive(name):
        return get_directive_size(name, operands, address)
    elif is_opname(name):
        return get_instruction_size(name, operands, address)
    else:
        return -1


def get_directive_size(name, operands, address):
    """
    Do not check the syntax or the content, just return how many bytes it will be if it is valid, and store included files using 
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
            alignment = imval_to_int('#'+operands[0])
        if len(operands) > 1:
            offset = imval_to_int('#'+operands[1])
        return (alignment - ((address+alignment-offset) % alignment)) % alignment
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
    elif name == 'INCBIN':
        size = add_file(operands)
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
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############

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
        if not is_reg(operands):
            return 'Invalid Operand: Expected register'
        rn = get_reg_num(operands)
        if rn == 15:
            return 'PC not allowed here (causes undefined behaviour)'
        return ''
    else:
        operands = operands.strip()
        err = check_pcrelative_expression(operands, labeldict)
        if len(err) != 0:
            return 'Invalid Operand: Expected pc relative expression (%s)' % (err)
        offset = pcrelative_expression_to_int(operands, address, labeldict)
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
        rn = get_reg_num(operands)
        ccval = get_condcode_value(condcode)
        encoded = encode_32bit([(28, 4, ccval), (4, 24, 0x12FFF1), (0, 4, rn)])
        return bigendian_to_littleendian(encoded)
    else:
        offset = pcrelative_expression_to_int(operands, address, labeldict)
        offset >>= 2
        offset = offset + (offset < 0)*(1 << 24)  # correction for negative offsets
        ccval = get_condcode_value(condcode)
        lflag = (name == 'BL')
        encoded = encode_32bit([(28, 4, ccval), (25, 3, 0x5), (24, 1, lflag), (0, 24, offset)])
        return bigendian_to_littleendian(encoded)


def check_psrtransop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 2:
        return 'Invalid number of operands: expected 2, got %i' % (len(operands))
    if name == 'MRS':
        if not is_reg(operands[0]):
            return 'Invalid operand: expected register'
        rd = get_reg_num(operands[0])
        if rd == 15:
            return 'PC is not allowed here'
        if not operands[1].upper() in ['SPSR', 'SPSR_ALL', 'CPSR', 'CPSR_ALL']:
            return 'Invalid operand: expected psr'
        return ''
    else:
        if not is_psr(operands[0]):
            return 'Invalid operand: expected psr'
        if not operands[0].upper().endswith('FLG'):
            if not is_reg(operands[1]):  # immediate is only allowed for PSR_FLG
                return 'Invalid operand: expected register'
            if get_reg_num(operands[1]) == 15:
                return 'PC is not allowed here'
            return ''
        if is_reg(operands[1]):
            if get_reg_num(operands[1]) == 15:
                return 'PC is not allowed here'
            return ''
        if not is_valid_imval(operands[1]):
            return 'Invalid operand: expected register or immediate value'
        if not is_expressable_imval(operands[1]):
            return 'This immediate value cannot be encoded'
        return ''


def encode_psrtransop(name, condcode, operands):
    """
    check_psrtransop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    if name == 'MRS':
        rd = get_reg_num(operands[0])
        if operands[1].upper()[0] == 'C':  # CPSR
            spsrflag = False
        else:
            spsrflag = True
        ccval = get_condcode_value(condcode)
        encoded = encode_32bit([(28, 4, ccval), (23, 5, 0x2), (22, 1, spsrflag), (16, 6, 0xF), (12, 4, rd)])
        return bigendian_to_littleendian(encoded)
    else:
        if operands[0].upper()[0] == 'C':  # CPSR
            spsrflag = False
        else:
            spsrflag = True
        if operands[0].upper().endswith('FLG'):
            allflag = False
        else:
            allflag = True
        if is_reg(operands[1]):
            iflag = False
            rm = get_reg_num(operands[1])
            op2field = rm
        else:
            iflag = True
            op2field = encode_imval(operands[1])
        ccval = get_condcode_value(condcode)
        encoded = encode_32bit([(28, 4, ccval), (25, 1, iflag), (23, 2, 0x2),
                                        (22, 1, spsrflag), (17, 5, 0x14), (16, 1, allflag),
                                        (12, 4, 0xF), (0, 12, op2field)])
        return bigendian_to_littleendian(encoded)


def check_swiop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 1:
        return 'Invalid number of operands: expected 1, got %i' % (len(operands))
    operands = operands[0]
    if not is_valid_imval(operands):
        return 'Invalid operand: expected immediate value'
    com = imval_to_int(operands)
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
    ccval = get_condcode_value(condcode)
    com = imval_to_int(operands)
    encoded = encode_32bit([(28, 4, ccval), (24, 4, 0xF), (0, 24, com)])
    return bigendian_to_littleendian(encoded)


def check_miscarithmeticop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 2:
        return 'Invalid number of operands: expected 2, got %i' % (len(operands))
    if not is_reg(operands[0]):
        return 'Invalid operand: expected register'
    rd = get_reg_num(operands[0])
    if not is_reg(operands[1]):
        return 'Invalid operand: expected register'
    rm = get_reg_num(operands[1])
    if rd == 15 or rm == 15:
        return 'PC is not allowed here'
    return ''

def encode_miscarithmeticop(name, condcode, operands):
    """
    check_miscarithmeticop must be called before this.
    Encode the instruction and return it as a bytearray object.
    """
    operands = [x.strip() for x in operands.split(',')]
    rd = get_reg_num(operands[0])
    rm = get_reg_num(operands[1])
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (16, 12, 0x16F), (12, 4, rd), (4, 8, 0xF1), (0, 4, rm)])
    return bigendian_to_littleendian(encoded)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############



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
        if not is_reg(o):
            return 'Expected a register'
    operands = [get_reg_num(x) for x in operands]
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
    operands = [get_reg_num(x.strip()) for x in operands.split(',')]
    sflag = (flags == 'S')
    (rd, rm, rs) = operands[0:3]
    if name == 'MUL':
        rn = 0
        aflag = False
    else:
        rn = operands[3]
        aflag = True
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (21, 1, aflag), (20, 1, sflag), (16, 4, rd),
                                    (12, 4, rn), (8, 4, rs), (4, 4, 0x9), (0, 4, rm)])
    return bigendian_to_littleendian(encoded)


def check_longmulop(name, operands):
    """
    Assumes valid name, valid name+flags combination, valid condcode.
    Check the operands and return an error string if invalid, empty string otherwise.
    """
    operands = [x.strip() for x in operands.split(',')]
    if len(operands) != 4:
        return 'Expected 4 operands, got %i' % len(operands)
    for o in operands:
        if not is_reg(o):
            return 'Expected a register'
    operands = [get_reg_num(x) for x in operands]
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
    (rdlo, rdhi, rm, rs) = [get_reg_num(x.strip()) for x in operands.split(',')]
    sflag = (flags == 'S')
    signedflag = (name[0] == 'S')
    aflag = (name[3] == 'A')
    ccval = get_condcode_value(condcode)
    encoded = encode_32bit([(28, 4, ccval), (23, 5, 0x1), (22, 1, signedflag), (21, 1, aflag),
                                    (20, 1, sflag), (16, 4, rdhi), (12, 4, rdlo), (8, 4, rs), (4, 4, 0x9), (0, 4, rm)])
    return bigendian_to_littleendian(encoded)
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############




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
            if not is_valid_numeric_literal(op):
                return 'Invalid numeric literal'
            i = numeric_literal_to_int(op)
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
            if not is_valid_numeric_literal(op):
                return 'Invalid numeric literal'
            i = numeric_literal_to_int(op)
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
        if not is_valid_numeric_literal(operands[0]):
            return 'Invalid numeric literal'
        alignment = numeric_literal_to_int(operands[0])
        if alignment == 0 or (alignment & (alignment-1)) != 0:
            return 'Only powers of two are allowed as alignment boundaries'
        if len(operands) == 1:
            return ''
        if not is_valid_numeric_literal(operands[1]):
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
            elif is_valid_numeric_literal(op):
                i = numeric_literal_to_int(op)
                if i < -128:
                    return 'Numeric literal outside of 8bit range: lower than -2^7'
                if i > 255:
                    return 'Numeric literal outside of 8bit range: greater than 2^8-1'
            else:
                return 'Expected numeric or string literal'
        return ''
    if name == 'INCBIN':
        s = filecontents(operands)
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
            i = numeric_literal_to_int(op)
            encoded += bigendian_to_littleendian(encode_32bit([(0, 32, i)]))
        return encoded
    if name == 'DCW' or name == 'DCWU':
        operands = [x.strip() for x in operands.split(',')]
        encoded = b''
        if name == 'DCW':
            encoded += b'\x00'*(address % 2)  # align
        for op in operands:
            i = numeric_literal_to_int(op)
            encoded += bigendian_to_littleendian_16bit(encode_16bit([(0, 16, i)]))
        return encoded
    if name == 'ALIGN':
        operands = [x.strip() for x in operands.split(',')]
        if len(operands) == 0 or len(operands[0]) == 0:  # implicit alignment to 4 bytes
            alignment = 4
        else:
            alignment = numeric_literal_to_int(operands[0])
        if len(operands) < 2:
            offset = 0
        else:
            offset = numeric_literal_to_int(operands[1])
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
                i = numeric_literal_to_int(op)
                encoded += bytes([i])
        return encoded
    if name == 'INCBIN':
        return filecontents(operands)
    return b''  # should never be reached
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############
# functions return -1 on failure.
# member functions prefixed with an underline must not be called from outside the class.













class Sourceline:
    # line  # the full string
    # notcomment  # everything except comments
    # label
    # operation  # everything after the label
    # opname
    # flags
    # condcode
    # operands
    # address
    # hexcode
    # length
    # errmsg  # contains a string describing the error if a function
    #           fails and returns -1

    def __init__(self, inst):
        """Initialize all data members to their empty/unprocessed-value except self.line to inst."""
        self.line = inst
        self.notcomment = ''
        self.label = ''
        self.operation = ''
        self.opname = ''
        self.flags = ''
        self.condcode = ''
        self.operands = ''
        self.address = -1
        self.hexcode = b''
        self.length = -1
        self.errmsg = ''

    def _parse_s_suffix(self):
        """If self.opname is an an op with an (arithmetic) S-suffix, remove that suffix and set self.flags to S."""
        soplist = ['ADC', 'ADD', 'RSB', 'RSC', 'SBC', 'SUB', 'AND',
                   'BIC', 'EOR', 'ORR', 'MOV', 'MVN', 'MUL', 'MLA',
                   'UMULL', 'SMULL', 'UMLAL', 'SMLAL']
        for op in soplist:
            if self.opname.startswith(op):
                if (self.opname[:-3] == op and is_condcode(self.opname[-3:-1]) and self.opname[-1] == 'S')\
                   or (self.opname == op+'S'):
                    self.opname = self.opname[:-1]
                    self.flags = 'S'
                    break

    def _parse_tbhs_suffixes(self):
        """If self.opname is an op with T, B, H or S-suffixes, remove that (those) suffix(es) and set self.flags to those."""
        tbhsoplist = ['LDR', 'STR', 'SWP']
        for op in tbhsoplist:
            if self.opname.startswith(op):
                if self.opname[-1] == 'T':
                    self.opname = self.opname[:-1]
                    self.flags = 'T'
                if self.opname[-1] == 'B':
                    self.opname = self.opname[:-1]
                    self.flags = 'B' + self.flags
                if self.opname[-1] == 'H':
                    self.opname = self.opname[:-1]
                    self.flags = 'H' + self.flags
                if self.opname[-1] == 'S':
                    self.opname = self.opname[:-1]
                    self.flags = 'S' + self.flags
                break

    def _parse_addrmode_suffixes(self):
        """If self.opname is a multiple data processing instruction, remove the suffix and set self.flags to it."""
        addrsuffoplist = ['LDM', 'STM']
        addressingmodelist = ['FD', 'ED', 'FA', 'EA', 'IA', 'IB',
                              'DA', 'DB']
        for op in addrsuffoplist:
            if self.opname.startswith(op):
                if (self.opname[:-4] == op and is_condcode(self.opname[-4:-2]) and self.opname[-2:] in addressingmodelist)\
                   or (self.opname[:-2] == op and self.opname[-2:] in addressingmodelist):
                    self.flags = self.opname[-2:]
                    self.opname = self.opname[:-2]
                    break

    def _parse_condition_code(self):
        """If there is a condition code in self.opname, remove it there and set self.condcode to it."""
        if is_opname(self.opname+self.flags):
            return
        if is_condcode(self.opname[-2:]):
            self.condcode = self.opname[-2:]
            self.opname = self.opname[:-2]

    def _check_operation(self):
        """
        Check if self forms a valid operation, fill errmsg if not.
        Return 0 if valid, -1 if invalid.
        """
        if not is_opname(self.opname+self.flags):
            self.errmsg = 'This instruction (name:%s, flags:%s) is unknown' % (self.opname, self.flags)
            return -1
        if is_conditionable(self.opname+self.flags):
            if len(self.condcode) > 0 and not is_condcode(self.condcode):
                self.errmsg = 'Condition code is unknown (condition code: %s)' % (self.condcode)
                return -1
        elif len(self.condcode) > 0:
            self.errmsg = 'Condition codes are not allowed for this instruction (name:%s, flags:%s, cond:%s)' % (self.opname, self.flags, self.condcode)
            return -1
        return 0

    def _check_label(self):
        """
        Check if self.label is allowed (i.e. not private or containing illegal characters), fill errmsg if not.
        Return 0 if correct, -1 if not correct.
        """
        if not is_valid_label(self.label):
            self.errmsg = 'This label contains illegal characters (label:%s)' % (self.label)
            return -1
        if is_private_label(self.label):
            self.errmsg = 'This label name is reserved (label:%s)' % (self.label)
            return -1
        return 0

    def parse_comments(self):
        """
        self must be initialized and not yet parsed.
        Set self.notcomment to self.line stripped from comments.
        Return 0.
        """
        sci = self.line.find(';')
        dqi = self.line.find('"')
        if sci < dqi or dqi == -1:
            if sci == -1:
                self.notcomment = self.line
            else:
                self.notcomment = self.line[:sci]
        else:  # there is a ; and a " before it
            tmpline = self.line.replace('\\"', '""')  # TODO: test #replace c-style escaped " with "", which is the arm asm way of getting a single " inside a string. don't have to care about cases where it's outside a string, because that will be a syntax error later on anyway. sci is still correct.
            while tmpline.count('"', 0, sci) % 2 != 0:  # if the number of quotes before the semicolon is odd, the semicolon is inside a string
                sci = self.line.find(';', sci+1)
                if sci == -1:
                    break
            if sci == -1:
                self.notcomment = self.line
            else:
                self.notcomment = self.line[:sci]
        self.notcomment = self.notcomment.rstrip()  # whitespace in front is relevant!
        return 0

    def parse_labelpart(self):
        """
        self must be processed by parse_comments but nothing after that.
        Set self.label to the label, set self.operation to the rest of the line (stripped from whitespace).
        Return 0 on success, -1 on failure/error.
        """
        if self.notcomment[:1].isspace():
            self.operation = self.notcomment.strip()
            return 0
        splitr = self.notcomment.split(None, 1)
        if len(splitr) == 0:
            return 0
        elif len(splitr) == 1:
            self.label = splitr[0]
        else:  # len(splitr) == 2
            self.label = splitr[0]
            self.operation = splitr[1].strip()
        if self._check_label() == -1:
            return -1
        return 0

    def parse_namepart(self):
        """
        self must be processed by parse_labelpart but nothing after.
        Parse self.operation: the operation name with suffixes and stuff, set self.opname, self.flags, self.condcode (defaults to AL if conditionable) to the computed values. Store the rest in self.operands.
        Return 0 on success, -1 on failure/error.
        """
        splitr = self.operation.split(None, 1)
        if len(splitr) == 0:
            return 0
        elif len(splitr) == 1:
            oppart = splitr[0]
            operators = ''
        else:  # len(splitr) == 2
            (oppart, operators) = splitr
        self.opname = oppart.upper().strip()
        self.operands = operators.strip()
        self._parse_s_suffix()
        self._parse_tbhs_suffixes()
        self._parse_addrmode_suffixes()
        self._parse_condition_code()
        if len(self.condcode) == 0 and is_conditionable(self.opname+self.flags):
            self.condcode = 'AL'
        if self._check_operation() == -1:
            return -1
        return 0

    def set_length_and_address(self, address):
        """
        self must be processed by parse_namepart.
        Set self.address to address, calculate and set self.length, store included files in 
        Return 0 on success, -1 on failure.
        """
        self.address = address
        if len(self.opname+self.flags) == 0:
            self.length = 0
        else:
            self.length = get_size(self.opname+self.flags, self.operands, address)
        if self.length == -1:
            self.errmsg = 'Could not calculate instruction size'
            return -1
        return 0

    def get_length(self):
        """
        self must be processed by set_length_and_address.
        Return self.length.
        """
        return self.length

    def replace_pseudoinstructions(self, labeldict):
        """
        self must be processed by set_length_and_address.
        Replace self.opname, self.operands of pseudoinstructions.
        Return 0 on success, -1 on failure.
        """
        if is_pseudoinstruction(self.opname, self.operands):
            err = check_pseudoinstruction(self.opname, self.operands, self.address, labeldict)
            if len(err) != 0:
                self.errmsg = err
                return -1
            self.opname, self.operands = get_replacement(self.opname, self.operands, self.address, labeldict)
        return 0

    def _check_syntax(self, labeldict):
        """
        self must be processed by replace_pseudoinstructions.
        Return error message string, empty string if no error.
        """
        fullname = self.opname+self.flags
        if is_directive(fullname):
            return check_directive(self.opname, self.operands)
        elif is_dataprocop(fullname):
            return check_dataprocop(self.opname, self.operands)
        elif is_branchop(fullname):
            return check_branchop(self.opname, self.operands, self.address, labeldict)
        elif is_psrtransop(fullname):
            return check_psrtransop(self.opname, self.operands)
        elif is_swiop(fullname):
            return check_swiop(self.opname, self.operands)
        elif is_mulop(fullname):
            return check_mulop(self.opname, self.operands)
        elif is_longmulop(fullname):
            return check_longmulop(self.opname, self.operands)
        elif is_coprocregtransop(fullname):
            return check_coprocregtransop(self.opname, self.operands)
        elif is_singledatatransop(fullname):
            return check_singledatatransop(self.flags, self.operands, self.address, labeldict)
        elif is_halfsigneddatatransop(fullname):
            return check_halfsigneddatatransop(self.operands, self.address, labeldict)
        elif is_swapop(fullname):
            return check_swapop(self.operands)
        elif is_blockdatatransop(fullname):
            return check_blockdatatransop(self.opname, self.operands)
        elif is_miscarithmeticop(fullname):
            return check_miscarithmeticop(self.opname, self.operands)
        else:
            return 'Unknown or not implemented instruction (failed in _check_syntax)'

    def _encode_line(self, labeldict):
        """
        self must be processed by _check_syntax.
        Return encoded line as a bytearray object.
        """
        fullname = self.opname+self.flags
        if is_directive(fullname):
            return encode_directive(self.opname, self.operands, self.address)
        elif is_dataprocop(fullname):
            return encode_dataprocop(self.opname, self.flags, self.condcode, self.operands)
        elif is_branchop(fullname):
            return encode_branchop(self.opname, self.condcode, self.operands, self.address, labeldict)
        elif is_psrtransop(fullname):
            return encode_psrtransop(self.opname, self.condcode, self.operands)
        elif is_swiop(fullname):
            return encode_swiop(self.opname, self.condcode, self.operands)
        elif is_mulop(fullname):
            return encode_mulop(self.opname, self.flags, self.condcode, self.operands)
        elif is_longmulop(fullname):
            return encode_longmulop(self.opname, self.flags, self.condcode, self.operands)
        elif is_coprocregtransop(fullname):
            return encode_coprocregtransop(self.opname, self.condcode, self.operands)
        elif is_singledatatransop(fullname):
            return encode_singledatatransop(self.opname, self.flags, self.condcode, self.operands, self.address, labeldict)
        elif is_halfsigneddatatransop(fullname):
            return encode_halfsigneddatatransop(self.opname, self.flags, self.condcode, self.operands, self.address, labeldict)
        elif is_swapop(fullname):
            return encode_swapop(self.opname, self.flags, self.condcode, self.operands)
        elif is_blockdatatransop(fullname):
            return encode_blockdatatransop(self.opname, self.flags, self.condcode, self.operands)
        elif is_miscarithmeticop(fullname):
            return encode_miscarithmeticop(self.opname, self.condcode, self.operands)
        else:
            return b''

    def assemble(self, labeldict):
        """
        self must be processed by replace_pseudoinstructions.
        Set self.hexcode to the binary machine code corresponding to self.
        Return 0 on success, -1 on failure.
        """
        if len(self.opname) == 0:
            return 0
        err = self._check_syntax(labeldict)
        if len(err) > 0:
            self.errmsg = err
            return -1
        self.hexcode = self._encode_line(labeldict)
        if len(self.hexcode) != self.length:
            self.errmsg = 'Precalculated length (%i bytes) and real length (%i bytes) are not the same' % (self.length, len(self.hexcode))
            return -1
        return 0

    def get_hex(self):
        """
        self must be processed by assemble.
        Return self.hexcode.
        """
        return self.hexcode
##########IMPORT END############

##########IMPORT END############
##########IMPORT START############
# assembly language details:
# of the operations dealing with the coprocessor only MRC and MCR are supported (the others (LDC, STC, CDP) are useless on the nspire)
# labels may not have any whitespace before them, instructions have to have whitespace before them





def printerror(filename, linenum, line, msg):
    """Print an error message using the supplied information."""
    print('Error in file "%s" on line %i:%s' % (filename, linenum, line))
    print('\t%s' % (msg))


def printmsg(msg):
    """Print msg."""
    print(msg)


def gettext(filename):
    """Return a list of all lines in the file."""
    f = open(filename, 'r')
    text = f.read()
    f.close()
    return text.split('\n')


def assembler(infile, outfile):
    """
    Assemble infile and write the binary to outfile.
    Return -1 on failure, 0 on success.
    """
    print("DEBUG: ASSEMBLER CALLED")
    numerrs = 0
    curaddr = 0
    labeldict = {}
    set_sourcepath(infile)
    text = gettext(infile)
    code = []
    # create list of Sourceline objects containing the lines of code
    for l in text:
        code.append(Sourceline(l))

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
    if numerrs != 0:
        printmsg('Stopping assembler: %i Error(s)' % (numerrs))
        return -1

    # stage 2: calculate length and address of every instruction, read files included with INCBIN
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
##########IMPORT END############

##########IMPORT END############



def calc_assemble():
    """prompts the user for the arguments"""
    inf = input('in:')
    outf = input('out:')
    return assembler(inf, outf)


calc_assemble()

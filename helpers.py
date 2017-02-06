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
    directivelist = ['DCD', 'DCDU', 'DCW', 'DCWU', 'ALIGN', 'DCB']
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


def is_opname(s):
    """Return True if s is a valid operation or directive name (full name, i.e. with flags!), False otherwise."""
    return is_directive(s) or is_dataprocop(s) or is_branchop(s) or is_psrtransop(s) or is_mulop(s)\
        or is_longmulop(s) or is_swiop(s) or is_singledatatransop(s) or is_halfsigneddatatransop(s)\
        or is_swapop(s) or is_blockdatatransop(s) or is_coprocregtransop(s) or is_pseudoinstructionop(s)


def is_conditionable(s):
    """Check if s can be conditionally executed. Return True if yes, False if no."""
    return True


def is_pseudoinstruction(opname, operands):
    """Check if opname operands is a pseudoinstruction. Return True if yes, False if no."""
    return is_pseudoinstructionop(opname)

def is_shiftname(s):
    """returns True iff s is a shiftname (excluding RRX)"""
    shiftnamelist = ['ASL', 'LSL', 'LSR', 'ASR', 'ROR']
    return s in shiftnamelist

def is_valid_imval(s):
    """returns True iff s is a syntactically valid immediate value"""
    if len(s) < 2:
        return False
    if s[0] != '#':
        return False
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
    if s[1] != '0' and isdigit(s[1:]):
        return True
    return False

def imval_to_int(s):
    """returns value of the immediate value s
s must be a syntactically valid immediate value, or the result is meaningless"""
    if s.startswith('#'):
        if s == '#0':
            return 0
        if s.startswith('#\'') and s[-1] == '\'' and len(s) == 4:
            return ord(s[2])
        if s.startswith('#0x'):
            return int(s[3:], 16)
        if s.startswith('#0'):
            return int(s[2:], 8)
        if s.startswith('#0b'):
            return int(s[3:], 2)
        return int(s[1:])
    return 0

def is_valid_label(s):
    """returns True if s is a syntactically valid label, False otherwise
Rules: must start with an alphabetic character, must only contain alphanumeric characters or underscores"""
    if not s[0].isalpha():
        return False
    for c in s:
        if c.isalnum() or c == '_':
            continue
        return False
    return True

def is_private_label(s):
    """returns True if s is a reserved label name, False otherwise
Currently, only assembly "keywords" are reserved"""
    if is_directive(s) or is_opname(s) or is_reg(s) or is_otherkeyword(s):
        return True
    return False

def is_otherkeyword(s):
    """returns True iff s is another keyword than an opname, directive or reg, False otherwise"""
    if s.upper() in ['LSL', 'LSR', 'ASR', 'ROR', 'RRX']:
        return True
    if s.upper() in ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15']:
        return True
    if s.upper() in ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15']:
        return True
    if s.upper() in ['CPSR', 'SPSR', 'CPSR_ALL', 'SPSR_ALL', 'SPSR_FLG', 'CPSR_FLG']:
        return True
    return False

def get_reg_num(s):
    regdict = {'R0' : 0, 'R1' : 1, 'R2' : 2, 'R3': 3, 'R4' : 4, 'R5' : 5, 'R6' : 6, 'R7' : 7, 'R8' : 8, 'R9' : 9, 'R10' : 10, 'R11' : 11, 'R12' : 12, 'R13' : 13, 'SP' : 13, 'R14' : 14, 'LR': 14, 'R15' : 15, 'PC' : 15}
    s = s.upper()
    if s in regdict:
        return regdict[s]
    return -1

def is_reg(s):
    return get_reg_num(s) != -1

def get_condcode_value(s):
    """returns the number corresponding to s or -1 if s is not a valid condition code"""
    condcodedict = {'EQ' : 0, 'NE' : 1, 'HS' : 2, 'CS' : 2, 'LO' : 3, 'CC' : 3, 'MI' : 4, 'PL' : 5, 'VS' : 6, 'VC' : 7, 'HI' : 8, 'LS' : 9, 'GE' : 10, 'LT' : 11, 'GT' : 12, 'LE' : 13, 'AL' : 14}
    if s in condcodedict:
        return condcodedict[s]
    return -1

def is_condcode(s):
    """returns True iff s is a valid condcode, False otherwise"""
    return get_condcode_value(s) != -1

def is_directive(s):
    directivelist = ['DCD', 'DCDU', 'ALIGN', 'DCB']
    return s in directivelist

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
    dataprocopdict = {'ADC' : 5,  'ADD' : 4, 'RSB' : 3, 'RSC' : 7, 'SBC' : 6, 'SUB' : 2, 'AND' : 0, 'BIC' : 14, 'EOR' : 1, 'ORR' : 12, 'CMP' : 10, 'CMN' : 11, 'TEQ' : 9, 'TST' : 8, 'MOV' : 13, 'MVN' : 15}
    if s in dataprocopdict:
        return dataprocopdict[s]
    return -1

def is_dataprocop(s):
    dataprocoplist = ['ADC', 'ADD', 'RSB', 'RSC', 'SBC', 'SUB', 'AND', 'BIC', 'EOR', 'ORR', 'CMP', 'CMN', 'TEQ', 'TST', 'MOV', 'MVN',
                    'ADCS', 'ADDS', 'RSBS', 'RSCS', 'SBCS', 'SUBS', 'ANDS', 'BICS', 'EORS', 'ORRS', 'MOVS', 'MVNS']
    return s in dataprocoplist

def is_branchop(s):
    branchoplist = ['BX', 'B', 'BL']
    return s in branchoplist

def is_psrtransop(s):
    psrtransoplist = ['MSR', 'MRS']
    return s in psrtransoplist

def is_mulop(s):
    muloplist = ['MUL', 'MLA', 'MULS', 'MLAS']
    return s in muloplist

def is_longmulop(s):
    longmuloplist = ['UMULL', 'SMULL', 'UMLAL', 'SMLAL', 'UMULLS', 'SMULLS', 'UMLALS', 'SMLALS']
    return s in longmuloplist

def is_swiop(s):
    swioplist = ['SWI', 'SVC']
    return s in swioplist

def is_singledatatransop(s):
    singledatatransoplist = ['LDR', 'STR', 'LDRB', 'STRB', 'LDRT', 'STRT', 'LDRBT', 'STRBT']
    return s in singledatatransoplist

def is_halfsigneddatatransop(s):
    halfsigneddatatransoplist = ['LDRH', 'LDRSH', 'LDRSB', 'STRH']
    return s in halfsigneddatatransoplist

def is_swapop(s):
    swapoplist = ['SWP', 'SWPB']
    return s in swapoplist

def is_blockdatatransop(s):
    blockdatatransoplist = ['LDMFD', 'LDMED', 'LDMFA', 'LDMEA', 'LDMIA', 'LDMIB', 'LDMDA', 'LDMDB', 'STMFD', 'STMED', 'STMFA', 'STMEA', 'STMIA', 'STMIB', 'STMDA', 'STMDB']
    return s in blockdatatransoplist

def is_coprocregtransop(s):
    coprocregtransoplist = ['MRC', 'MCR']
    return s in coprocregtransoplist

def is_opname(s):
    """returns True iff s is a valid operation or directive name (full name, i.e. with flags!), False otherwise"""
    return is_directive(s) or is_dataprocop(s) or is_branchop(s) or is_psrtransop(s) or is_mulop(s) or is_longmulop(s) or is_swiop(s) or is_singledatatransop(s) or is_halfsigneddatatransop(s) or is_swapop(s) or is_blockdatatransop(s) or is_coprocregtransop(s)

def is_conditionable(s):
    """check if s can be conditionally executed. returns True if yes, False if no"""
    return True

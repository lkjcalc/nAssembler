# functions return -1 on failure.
# member functions prefixed with an underline must not be called from outside the class.

import helpers
import size
import asm_dataproc
import asm_directive
import asm_misc
import asm_mul
import asm_cpregtrans
import asm_datatrans
import asm_blockdatatrans
import asm_pseudoinstructions


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
                if (self.opname[:-3] == op and helpers.is_condcode(self.opname[-3:-1]) and self.opname[-1] == 'S')\
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
                if (self.opname[:-4] == op and helpers.is_condcode(self.opname[-4:-2]) and self.opname[-2:] in addressingmodelist)\
                   or (self.opname[:-2] == op and self.opname[-2:] in addressingmodelist):
                    self.flags = self.opname[-2:]
                    self.opname = self.opname[:-2]
                    break

    def _parse_condition_code(self):
        """If there is a condition code in self.opname, remove it there and set self.condcode to it."""
        if helpers.is_opname(self.opname+self.flags):
            return
        if helpers.is_condcode(self.opname[-2:]):
            self.condcode = self.opname[-2:]
            self.opname = self.opname[:-2]

    def _check_operation(self):
        """
        Check if self forms a valid operation, fill errmsg if not.
        Return 0 if valid, -1 if invalid.
        """
        if not helpers.is_opname(self.opname+self.flags):
            self.errmsg = 'This instruction (name:%s, flags:%s) is unknown' % (self.opname, self.flags)
            return -1
        if helpers.is_conditionable(self.opname+self.flags):
            if len(self.condcode) > 0 and not helpers.is_condcode(self.condcode):
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
        if not helpers.is_valid_label(self.label):
            self.errmsg = 'This label contains illegal characters (label:%s)' % (self.label)
            return -1
        if helpers.is_private_label(self.label):
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
        if len(self.condcode) == 0 and helpers.is_conditionable(self.opname+self.flags):
            self.condcode = 'AL'
        if self._check_operation() == -1:
            return -1
        return 0

    def set_length_and_address(self, address):
        """
        self must be processed by parse_namepart.
        Set self.address to address and calculate and set self.length.
        Return 0 on success, -1 on failure.
        """
        self.address = address
        if len(self.opname+self.flags) == 0:
            self.length = 0
        else:
            self.length = size.get_size(self.opname+self.flags, self.operands, address)
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
        if helpers.is_pseudoinstruction(self.opname, self.operands):
            err = asm_pseudoinstruction.check_pseudoinstruction(self.opname, self.operands, self.address, labeldict)
            if len(err) != 0:
                self.errmsg = err
                return -1
            self.opname, self.operands = asm_pseudoinstruction.get_replacement(self.opname, self.operands, self.address, labeldict)
        return 0

    def _check_syntax(self, labeldict):
        """
        self must be processed by replace_pseudoinstructions.
        Return error message string, empty string if no error.
        """
        fullname = self.opname+self.flags
        if helpers.is_directive(fullname):
            return asm_directive.check_directive(self.opname, self.operands)
        elif helpers.is_dataprocop(fullname):
            return asm_dataproc.check_dataprocop(self.opname, self.operands)
        elif helpers.is_branchop(fullname):
            return asm_misc.check_branchop(self.opname, self.operands, self.address, labeldict)
        elif helpers.is_psrtransop(fullname):
            return asm_misc.check_psrtransop(self.opname, self.operands)
        elif helpers.is_swiop(fullname):
            return asm_misc.check_swiop(self.opname, self.operands)
        elif helpers.is_mulop(fullname):
            return asm_mul.check_mulop(self.opname, self.operands)
        elif helpers.is_longmulop(fullname):
            return asm_mul.check_longmulop(self.opname, self.operands)
        elif helpers.is_coprocregtransop(fullname):
            return asm_cpregtrans.check_coprocregtransop(self.opname, self.operands)
        elif helpers.is_singledatatransop(fullname):
            return asm_datatrans.check_singledatatransop(self.flags, self.operands, self.address, labeldict)
        elif helpers.is_halfsigneddatatransop(fullname):
            return asm_datatrans.check_halfsigneddatatransop(self.operands, self.address, labeldict)
        elif helpers.is_swapop(fullname):
            return asm_datatrans.check_swapop(self.operands)
        elif helpers.is_blockdatatransop(fullname):
            return asm_blockdatatrans.check_blockdatatransop(self.opname, self.operands)
        else:
            return 'Unknown or not implemented instruction (failed in _check_syntax)'

    def _encode_line(self, labeldict):
        """
        self must be processed by _check_syntax.
        Return encoded line as a bytearray object.
        """
        fullname = self.opname+self.flags
        if helpers.is_directive(fullname):
            return asm_directive.encode_directive(self.opname, self.operands, self.address)
        elif helpers.is_dataprocop(fullname):
            return asm_dataproc.encode_dataprocop(self.opname, self.flags, self.condcode, self.operands)
        elif helpers.is_branchop(fullname):
            return asm_misc.encode_branchop(self.opname, self.condcode, self.operands, self.address, labeldict)
        elif helpers.is_psrtransop(fullname):
            return asm_misc.encode_psrtransop(self.opname, self.condcode, self.operands)
        elif helpers.is_swiop(fullname):
            return asm_misc.encode_swiop(self.opname, self.condcode, self.operands)
        elif helpers.is_mulop(fullname):
            return asm_mul.encode_mulop(self.opname, self.flags, self.condcode, self.operands)
        elif helpers.is_longmulop(fullname):
            return asm_mul.encode_longmulop(self.opname, self.flags, self.condcode, self.operands)
        elif helpers.is_coprocregtransop(fullname):
            return asm_cpregtrans.encode_coprocregtransop(self.opname, self.condcode, self.operands)
        elif helpers.is_singledatatransop(fullname):
            return asm_datatrans.encode_singledatatransop(self.opname, self.flags, self.condcode, self.operands, self.address, labeldict)
        elif helpers.is_halfsigneddatatransop(fullname):
            return asm_datatrans.encode_halfsigneddatatransop(self.opname, self.flags, self.condcode, self.operands, self.address, labeldict)
        elif helpers.is_swapop(fullname):
            return asm_datatrans.encode_swapop(self.opname, self.flags, self.condcode, self.operands)
        elif helpers.is_blockdatatransop(fullname):
            return asm_blockdatatrans.encode_blockdatatransop(self.opname, self.flags, self.condcode, self.operands)
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
            self.errmsg = 'Precalculated length (%i bytes) and real length (%i bytes) are not the same' % (self.length, len(enc))
            return -1
        return 0

    def get_hex(self):
        """
        self must be processed by assemble.
        Return self.hexcode.
        """
        return self.hexcode

import assembler


def calc_assemble():
    """prompts the user for the arguments"""
    inf = input('in:')
    outf = input('out:')
    return assembler.assembler(inf, outf)


calc_assemble()

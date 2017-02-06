import argparse
import assembler


def cmd_assemble():
    """gets the arguments from the command line parameters"""
    parser = argparse.ArgumentParser(description='Assemble ARM assembly code')
    parser.add_argument('infile', metavar='INFILE', help='file containing code to assemble')
    parser.add_argument('outfile', metavar='OUTFILE', help='file to write the binary output to')
    args = parser.parse_args()
    assembler.assembler(args.infile, args.outfile)


cmd_assemble()

#automatic tests for the bundled version
#checking assembled result against hashes of known-to-be-correct results

import hashlib
import subprocess
import os

srcdir = './testsrc/'
hashdir = './testhashes/'

class NoHashError(Exception):
    pass

def get_hash_filename(fname):
    return hashdir+fname+'.hash'

def calculate_md5_of_file(fname):
    with open(srcdir+fname, 'rb') as f:
        binin = f.read()
    return hashlib.md5(binin).hexdigest()

def get_known_md5_of_file(fname):
    try:
        f = open(get_hash_filename(fname))
    except FileNotFoundError:
        raise NoHashError
    md5 = f.read().strip()
    f.close()
    return md5

def set_known_md5_of_file(fname, md5):
    with open(get_hash_filename(fname), 'w') as f:
        f.write(md5)

def do_all_tests():
    subproc_stdin_fname = 'nassembler_autotest_stdin.in'
    subproc_stdout_fname = 'nassembler_autotest_stdout.out'
    for fname in os.listdir(srcdir):
        if not fname.endswith('.asm'):
            continue
        print("Testing '{}'...".format(fname))
        # check source hash
        srcmd5 = calculate_md5_of_file(fname)
        try:
            if srcmd5 != get_known_md5_of_file(fname):
                srchashchanged = True
                print("WARNING: source hash changed for '{}'.".format(fname))
                answer = input("Replace source md5 and calculate new binary md5? (Y/N)").upper()
                if answer == 'N':
                    setnewhashes = False
                else:
                    setnewhashes = True
            else:
                srchashchanged = False
                setnewhashes = False
        except NoHashError:
            print("No known source hash for '{}'. Calculating new source and binary hash.".format(fname))
            srchashchanged = True
            setnewhashes = True
        outfilename = srcdir + fname[:-4] + '.tns'
        # move old binary
        try:
            os.rename(outfilename, outfilename+'.old')
        except FileNotFoundError:
            pass
        # assemble file
        fin = open(subproc_stdin_fname, 'w')
        fin.write(srcdir + fname + '\n')
        fin.write(outfilename + '\n')
        fin.close()
        fin = open(subproc_stdin_fname)
        fout = open(subproc_stdout_fname, 'w')
        subprocess.call(['python3', 'bundledmain.py'], stdin=fin, stdout=fout)
        fin.close()
        fout.close()
        fout = open(subproc_stdout_fname, 'r')
        s = fout.read()
        fout.close()
        # check stdout
        if 'Error' in s:
            print("Failed test. Assembler failed:")
            print(s)
            exit(1)
        # check output
        try:
            binmd5 = calculate_md5_of_file(fname[:-4] + '.tns')
        except FileNotFoundError:
            print("Failed test. No output binary found for '{}'. Assembler stdout:".format(fname))
            print(s)
            exit(1)
        try:
            if binmd5 != get_known_md5_of_file(fname[:-4] + '.tns'):
                binhashchanged = True
                print("WARNING: binary hash changed for '{}'.".format(fname))
            else:
                binhashchanged = False
        except NoHashError:
            print("No known binary hash for '{}'. Calculating new binary hash.".format(fname))
            binhashchanged = True
            setnewhashes = True
        # change hashes if requested
        if setnewhashes:
            set_known_md5_of_file(fname, srcmd5)
            set_known_md5_of_file(fname[:-4] + '.tns', binmd5)
            print("Recalculated known hashes for '{}'.".format(fname))
        # exit with error if binary hash was incorrect
        if binhashchanged and not setnewhashes:
            print("Failed tests.")
            exit(1)


do_all_tests()

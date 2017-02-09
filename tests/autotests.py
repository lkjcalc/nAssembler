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
                answer = input("Replace source md5 and calculate new binary md5? (Y/N)").toupper()
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
        # assemble file
        fin = open(subproc_stdin_fname, 'w')
        fin.write(srcdir + fname + '\n')
        fin.write(srcdir + fname[:-4] + '.tns\n')
        fin.close()
        fin = open(subproc_stdin_fname)
        fout = open(subproc_stdout_fname, 'w')
        subprocess.call(['python3', 'bundledmain.py'], stdin=fin, stdout=fout)
        #TODO: should close files?
        # check output
        binmd5 = calculate_md5_of_file(fname[:-4] + '.tns')
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

src_hash_list = ['36d7985f55521ad32dafbf9623c7da93', 'e06649b7675ce1bfcc61fe13c8d56d6a', '66ea2d57abeec95f56bc6116d35a022b', 'd95f7cac333fbd1732f771cf9f07abb4', 'dd1b84ea2ac9b0be819b4c83cc5e75b3', '18ac487586890f8b32dff351e9fadedb']
tns_hash_list = ['7977c81268034a0b21daff8a8c913a5e', '16df3dba78cb45e37bb4981415ef74dc', '0977abdea7079e0ce1c4e7f255985f71', 'bf6ec9b5d164f46e0a981cd5e456b0eb', '8a4475ec9444f278de7470d0250c0503', '3187101e4fafaefc9c44915f430a61e5']
filename_list = ['armasm_test', 'armasmt2', 'boot1largetest', 'armasm_spacet', 'lowercase_test', 'casetest2']

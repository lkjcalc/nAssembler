_files = {}
_sourcefolder = None
_sourcefile = None

def set_sourcepath(path):
    """
    Set the path of the source file which is currently being assembled.
    """
    global _sourcefolder, _sourcefile
    _sourcefile = path
    bs = path.rfind('/')
    _sourcefolder = path[:bs+1]

def _abspath(curpath, path):
    """
    Assuming current directory is curpath, resolve path as far as possible.
    """
    if path.startswith('../'):
        parpath = curpath[:curpath.rfind('/', 0, -1)+1]
        if not parpath:
            return path
        npath = path[3:]
        return _abspath(parpath, npath)
    elif path.startswith('./'):
        npath = path[2:]
        return _abspath(parpath, npath)
    elif path.startswith('/'):
        return path
    else:
        return curpath + path

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
    Return the contents of file at path, or None if file is not in filedict.
    add_file needs to be called on the same file before using this.
    """
    abspath = _abspath(_sourcefolder, path)
    return _files.get(abspath)

def filesize(path):
    """
    Return the size of file at path, or None if file is not in filedict.
    add_file needs to be called on the same file before using this.
    """
    abspath = _abspath(_sourcefolder, path)
    try:
        return len(_files[abspath])
    except Exception as e:
        print(e)
    return None

def get_sourcecode():
    """
    Return the source code in the file last passed to set_sourcepath, or None if file cannot be read.
    """
    if _sourcefile:
        try:
            with open(_sourcefile, 'r') as f:
                s = f.read()
            return s
        except Exception as e:
            print(e)
    return None

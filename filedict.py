_files = {}
_sourcefolder = None

def set_sourcepath(path):
    """
    Set the path of the source file which is currently being assembled.
    """
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
    Return the contents of file at path, or None if file is not in filedict.
    add_file needs to be called on the same file before using this.
    """
    abspath = _abspath(_sourcefolder, path)
    return _files.get(abspath)

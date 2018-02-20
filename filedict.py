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

def get_sourcepath():
    """
    Return the path of the source file which is currently being assembled.
    """
    return _sourcefile

def change_sourcepath(path):
    """
    Change the path of the source file which is currently being assembled.
    path is taken relative to the current sourcepath.
    """
    global _sourcefolder, _sourcefile
    abspath = _abspath(_sourcefolder, path)
    _sourcefile = abspath
    bs = abspath.rfind('/')
    _sourcefolder = abspath[:bs+1]

def _abspath(curpath, path):
    """
    Assuming current directory is curpath, resolve path as far as possible.
    """
    if path.startswith('./'):
        npath = path[2:]
        return _abspath(curpath, npath)
    elif not curpath:
        return path
    elif path.startswith('../'):
        parpath = curpath[:curpath.rfind('/', 0, -1)+1]
        npath = path[3:]
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
            return s.split('\n')
        except Exception as e:
            print(e)
    return None

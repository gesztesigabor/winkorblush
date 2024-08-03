
import itertools
import os.path


def splitNames(name):
    for num in itertools.count(1):
        yield f'{name}.{num:03}'


def mergeFile(fileName):
    with open(fileName, 'wb') as of:
        for name in splitNames(fileName):
            if not os.path.isfile(name):
                break
            with open(name, 'rb') as f:
                of.write(f.read())


def splitFile(fileName, splitSize):
    with open(fileName, 'rb') as f:
        for name in splitNames(fileName):
            b = f.read(splitSize)
            if len(b) == 0:
                break
            with open(name, 'wb') as of:
                of.write(b)


def shallMerge(fileName):
    if not os.path.isfile(fileName):
        return True
    name = next(splitNames(fileName))
    if not os.path.isfile(name):
        return False
    return os.path.getmtime(fileName) < os.path.getmtime(name)


def checkedMerge(fileName):
    if shallMerge(fileName):
        mergeFile(fileName)


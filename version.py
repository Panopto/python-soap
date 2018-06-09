from __future__ import print_function
from subprocess import Popen, PIPE
from os.path import abspath, dirname


# Can use 'alpha', 'beta', 'release candidate', 'final'
VERSION = (0, 0, 1, 'final', 0)


def git_sha():
    loc = abspath(dirname(__file__))
    try:
        p = Popen(
            'cd "%s" && git log -1 --format=format:%%h' % loc,
            shell=True,
            stdout=PIPE,
            stderr=PIPE
        )
        return p.communicate()[0]
    except Exception as err:
        print('Error collecting git sha: [%s] %s' % (err, err.message))


def get_version(form='short'):
    """
    Return a version string for this package, based on `VERSION`.

    Takes a single argument, ``form``, which should be one of the following
    strings:

    * ``branch``: just the major + minor, e.g. '0.9', '1.0'.
    * ``short`` (default): compact, e.g. '0.9rc1', '0.9.0'. For package
      filenames or SCM tag identifiers.
    * ``normal``: human readable, e.g. '0.9', '0.9.1', '0.9 beta 1'. For e.g.
      documentation site headers.
    * ``verbose``: like ``normal`` but fully explicit, e.g. '0.9 final'. For
      tag commit messages, or anywhere that it's important to remove ambiguity
      between a branch and the first final release within that branch.
    * ``all``: Returns all of the above, as a dict.
    """
    # Setup
    versions = {}
    branch = '%s.%s' % (VERSION[0], VERSION[1])
    tertiary = VERSION[2]
    type_ = VERSION[3]
    final = (type_ == 'final')
    type_num = VERSION[4]
    firsts = ''.join([x[0] for x in type_.split()])
    sha = git_sha()
    local_version = ('%s' % sha) if sha else ''

    # Branch
    versions['branch'] = branch

    # Short
    v = branch
    if (tertiary or final):
        v += '.' + str(tertiary)
    if not final:
        v += firsts + str(type_num)
    v += '+' + local_version
    versions['short'] = v

    # Normal
    v = branch
    if tertiary:
        v += '.' + str(tertiary)
    if not final:
        v += ' ' + type_
        if type_num:
            v += ' ' + str(type_num)
    v += ' (%s)' % local_version
    versions['normal'] = v

    # Verbose
    v = branch
    if tertiary:
        v += '.' + str(tertiary)
    if not final:
        v += ' ' + type_
        if type_num:
            v += ' ' + str(type_num)
    else:
        v += ' final'
    v += ' (%s)' % local_version
    versions['verbose'] = v

    try:
        return versions[form]
    except KeyError:
        if form == 'all':
            return versions
        raise TypeError('"%s" is not a valid form specifier.' % form)


__version__ = get_version('short')

if __name__ == '__main__':
    print(get_version('all'))

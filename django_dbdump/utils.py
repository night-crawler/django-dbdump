import os
import pexpect

from django_dbdump.settings import DUMP_DIR, RSYNC_PATTERN, RSYNC_DESTINATION, RSYNC_PASSWORD, RSYNC_DELETE
from django_dbdump.exceptions import SubprocessError

# 'rsync -raz --progress --delete %(source)s %(destination)s'

SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\?'


def run_rsync(reversed=False, log=''):
    """
    :param reversed: If True, copy remote's dumps to the local host
    :param log: show log
    :return:
    """
    if reversed:
        # TODO: read manual about trailing slash, including subdirs, etc
        dst = os.path.abspath(os.path.join(DUMP_DIR, os.path.pardir))
        cmd = RSYNC_PATTERN % {'destination': dst, 'source': RSYNC_DESTINATION}
    else:
        cmd = RSYNC_PATTERN % {'source': DUMP_DIR.rstrip(os.path.sep), 'destination': RSYNC_DESTINATION}
        if RSYNC_DELETE:
            cmd += ' --delete'

    if log:
        cmd += ' --log-file=%s' % log

    child = pexpect.spawn(cmd, timeout=5)

    if RSYNC_PASSWORD:
        i = child.expect([pexpect.TIMEOUT, SSH_NEWKEY, r'.*password: '])
        if i == 0:  # Timeout
            raise SubprocessError('TIMEOUT cmd: %s' % cmd)
        if i == 1:
            child.sendline('yes')
            child.expect(r'.*password: ')

        child.sendline(RSYNC_PASSWORD)

        i = child.expect(['Permission denied', r'.*'])
        if i == 0:
            raise SubprocessError('Wrong password')

    child.wait()

    return child


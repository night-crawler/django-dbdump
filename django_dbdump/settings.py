import os
import multiprocessing

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

BUNDLED_BACKENDS = {
    'django.db.backends.postgresql_psycopg2': 'django_dbdump.backends.psycopg2:DumpConverter',
    'django.db.backends.postgresql': 'django_dbdump.backends.psycopg2:DumpConverter',
}

BACKENDS = {}
BACKENDS.update(BUNDLED_BACKENDS)
BACKENDS.update(getattr(settings, 'DBDUMP_BACKENDS', {}))

DUMP_DIR = getattr(settings, 'DBDUMP_DIR', None)
if not DUMP_DIR:
    basedir = getattr(settings, 'BASE_DIR', None)
    if not basedir:
        raise ImproperlyConfigured('Need BASE_DIR in django.settings or DBDUMP_DIR')
    DUMP_DIR = os.path.join(basedir, 'dbdump')

if not os.path.exists(DUMP_DIR):
    try:
        os.makedirs(DUMP_DIR, mode=0o755)
    except OSError:
        pass

DBDUMP = getattr(settings, 'DBDUMP', {})
STRFTIME_FORMAT = getattr(settings, 'DBDUMP_STRFTIME_FORMAT', '%Y-%m-%d-%H%M%S')
# STRFTIME_FORMAT = getattr(settings, 'DBDUMP_STRFTIME_FORMAT', '%Y-%m-%d')

COMPRESS_ENABLED = getattr(settings, 'DBDUMP_COMPRESS_ENABLED', True)
COMPRESS_COMMAND = getattr(settings, 'DBDUMP_COMPRESS_COMMAND', 'gzip -f -9 %s')
DECOMPRESS_COMMAND = getattr(settings, 'DBDUMP_DECOMPRESS_COMMAND', 'gzip -d %s')
COMPRESS_EXTENSION = getattr(settings, 'DBDUMP_COMPRESS_EXTENSION', '.gz')

MAX_DUMPS_PER_ALIAS = getattr(settings, 'DBDUMP_MAX_DUMPS_PER_ALIAS', 10)

RSYNC_ENABLED = getattr(settings, 'DBDUMP_RSYNC_ENABLED', False)
RSYNC_PATTERN = getattr(
    settings, 'DBDUMP_RSYNC_PATTERN',
    'rsync -raz --progress %(source)s %(destination)s'
)
RSYNC_DESTINATION = getattr(settings, 'DBDUMP_RSYNC_DESTINATION', 'backup@example.com:/backups/')
RSYNC_PASSWORD = getattr(settings, 'DBDUMP_RSYNC_PASSWORD', '')
RSYNC_DELETE = getattr(settings, 'DBDUMP_RSYNC_DELETE', True)

CONCURRENCY = getattr(settings, 'DBDUMP_CONCURRENCY', multiprocessing.cpu_count())

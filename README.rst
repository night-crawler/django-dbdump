# django\_dbdump
================

Yet another Django DB Backup tool. Tested with ``Django==1.9.1``

Features
--------

-  rsync
-  restore from rsync
-  database & user create scripts
-  gzip

Requirements
------------

-  pexpect

Installation
------------

::

    pip install pexpect
    pip install -e git+https://github.com/night-crawler/django-dbdump.git@#egg=django-dbdump

Default settings
----------------

-  ``DBDUMP_DIR``: use provided directory, or
   ``os.path.join(BASE_DIR, 'dbdump')``
-  ``DBDUMP_BACKENDS``: custom backends, i.e.
   ``{'django.db.backends.postgresql': 'django_dbdump.backends.psycopg2:DumpConverter'}``
-  ``DBDUMP_STRFTIME_FORMAT = '%Y-%m-%d-%H%M%S'``
-  ``DBDUMP_COMPRESS_ENABLED = True``
-  ``DBDUMP_COMPRESS_COMMAND = 'gzip -f -9 %s'``
-  ``DBDUMP_DECOMPRESS_COMMAND = 'gzip -d %s'``
-  ``DBDUMP_COMPRESS_EXTENSION = '.gz'``
-  ``DBDUMP_MAX_DUMPS_PER_ALIAS = 10`` store max N dumps
-  ``DBDUMP_RSYNC_ENABLED = False`` - ``rsync`` disabled by default
-  ``DBDUMP_RSYNC_PATTERN = 'rsync -raz --progress %(source)s %(destination)s'``
-  ``DBDUMP_RSYNC_DESTINATION = 'backup@example.com:/backups/'``
-  ``DBDUMP_RSYNC_PASSWORD = ''`` - rsync password, if empty suppose we're using key auth
-  ``DBDUMP_RSYNC_DELETE = True`` - remove destination files

Usage
-----

::

    ./manage.py dbdump
    --create              Show create statements
    --load                Load database from last dump
    --start-rsync         Start rsync and exit
    --rsync-restore       Restore dumps from rsync
    --max-dumps [MAX_DUMPS]
                          Max dumps per alias
    --rsync               Run rsync after dump
    --no-rsync            Do NOT run rsync after dump

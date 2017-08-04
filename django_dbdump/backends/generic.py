import os
import shlex

from subprocess import Popen
from time import sleep

from django.utils.functional import cached_property
from django.utils.timezone import now
from django_dbdump.settings import DUMP_DIR, DBDUMP, STRFTIME_FORMAT, COMPRESS_ENABLED, COMPRESS_COMMAND, \
    COMPRESS_EXTENSION, MAX_DUMPS_PER_ALIAS, CONCURRENCY


class GenericDumpConverter(object):
    cmd = None
    extension = '.sql'
    concurrency = CONCURRENCY

    def __init__(self, db_alias, db_attrs, extra_args=None):
        """
        :param db_attrs: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'sysblog',
            'USER': 'sysblog',
            'PASSWORD': '123',
            'HOST': 'localhost',
            'PORT': ''
        }
        :param db_alias: Django database key from DATABASES, i.e. 'default'
        """
        self.db_attrs = db_attrs
        self.db_alias = db_alias
        self.dbdump_options = DBDUMP.get(db_alias, {})
        self.extra_args = extra_args or []

    def dump_option(self, option_key, default=None):
        """
        Get option from django settings DBDUMP dict. {'default': {'connection_string': 'smth'}}
        :param option_key: i.e. connection_string, connection_string_pattern, etc.
        :param default: default value
        :return:
        """
        return self.dbdump_options.get(option_key, default)

    def db_option(self, option_key, default=None):
        """
        Get database connection option from Django DATABASES['<current_alias>'] dict
        :param option_key: i.e., 'NAME', 'HOST'
        :param default:  default value
        :return:
        """
        return self.db_attrs.get(option_key, default)

    @cached_property
    def now(self):
        """
        :return: formatted now() string with format specified in DBDUMP options variable or in
        `DBDUMP_STRFTIME_FORMAT`
        """
        return now().strftime(self.dump_option('strftime_format', STRFTIME_FORMAT))

    @cached_property
    def filename(self):
        """
        :return: filename like `default__2016_01_01-102030.sql`
        """
        name = '__'.join([self.db_alias, self.now])
        return '%s%s' % (name, self.extension)

    @cached_property
    def compressed_filename(self):
        """
        :return: `self.filename` + COMPRESS_SUFFIX, i.e. default__2016_01_01-102030.sql.gz
        """
        return self.filename + COMPRESS_SUFFIX

    @cached_property
    def dump_filepath(self):
        """
        :return: absolute path to dumped file
        """
        return os.path.join(DUMP_DIR, self.filename)

    @cached_property
    def compressed_dump_filepath(self):
        """
        :return: absolute path to dumped & compressed file
        """
        return os.path.join(DUMP_DIR, self.compressed_filename)

    def execute_dump_command(self):
        """
        Execute dump command, should be redefined in a subclass. Function must raise is something weng wrong.
        """
        raise NotImplementedError()

    def compress(self):
        """
        Compress current dump file, raise if something went wrong
        :return:
        """
        if not COMPRESS_ENABLED and COMPRESS_COMMAND:
            return self
        cmd = COMPRESS_COMMAND % self.dump_filepath
        args = shlex.split(cmd)
        child = Popen(args)
        streamdata = child.communicate()[0]
        if child.returncode != 0:
            raise ChildProcessError('Compress command\n%s\nFAILED' % cmd)

    def execute(self):
        self.execute_dump_command()
        self.compress()
        return True

    @property
    def all_alias_dumps(self):
        """
        Get all dumps for a current Django DB alias
        :return: ['default_<dt0>.sql.gz', 'default_<dt1>.sql.gz']
        """
        files = []
        for f in os.listdir(DUMP_DIR):
            if f.startswith(self.db_alias + '__'):
                files.append(os.path.join(DUMP_DIR, f))

        files.sort()
        return files

    def remove_redundant_dumps(self, max_dumps=None):
        """
        Removes oldest dumps, leaves at least `max_dumps` files. Disables if max_dumps == 0
        """
        if not max_dumps:
            max_dumps = self.dump_option('max_dumps', MAX_DUMPS_PER_ALIAS)
            if not max_dumps:
                return

        for f in self.all_alias_dumps[:-max_dumps]:
            os.remove(f)





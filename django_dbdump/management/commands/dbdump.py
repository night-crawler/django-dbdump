import os

from uuid import uuid4
from importlib import import_module

from django.core.management.base import BaseCommand
from django_dbdump.settings import BACKENDS, MAX_DUMPS_PER_ALIAS, RSYNC_ENABLED, DUMP_DIR, RSYNC_DESTINATION
from django_dbdump.utils import run_rsync
from django.utils import termcolors
from django.core.management import color


def color_style():
    style = color.color_style()
    style.SECTION = termcolors.make_style(fg='yellow', opts=('bold',))
    style.SUCCESS = termcolors.make_style(fg='green', opts=('bold',))
    style.ERROR = termcolors.make_style(fg='red', opts=('bold',))
    style.INFO = termcolors.make_style(fg='blue', opts=('bold',))
    return style


class Command(BaseCommand):
    help = ('Creates full database backup. Example:\n'
            'python manage.py dbdump')

    results = ''
    requires_model_validation = False
    can_import_settings = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = color_style()

    def log(self, msg, color='SECTION', ending=None):
        self.stdout.write(getattr(self.style, color)(msg), ending=ending)
        self.stdout.flush()

    def err(self, msg, color='ERROR', ending=None):
        self.stderr.write(getattr(self.style, color)(msg), ending=ending)
        self.stderr.flush()

    def add_arguments(self, parser):
        parser.add_argument('aliases', nargs='*', default=[], type=str, help='DB Aliases to dump')

        parser.add_argument('--show-dump-cmd', action='store_true', default=False, help='Show dump cmd')
        parser.add_argument('--create', action='store_true', default=False, help='Show create statements')
        parser.add_argument('--load', action='store_true', default=False, help='Load database from last dump')
        parser.add_argument('--start-rsync', action='store_true', default=False, help='Start rsync and exit')
        parser.add_argument('--rsync-restore', action='store_true', default=False, help='Restore dumps from rsync')

        parser.add_argument('--max-dumps', nargs='?', default=MAX_DUMPS_PER_ALIAS, type=int, help='Max dumps per alias')
        parser.add_argument('--rsync', action='store_true', dest='rsync', help='Run rsync after dump')
        parser.add_argument('--no-rsync', action='store_false', dest='rsync', help='Do NOT run rsync after dump')
        parser.set_defaults(rsync=RSYNC_ENABLED)

    def get_dump_converter_by_engine(self, django_engine_path):
        """

        :param django_engine_path: i.e. 'django.db.backends.postgresql_psycopg2'
        :return: i.e. django_dbdump.backends.dump.psycopg2.DumpHandler
        """
        backend_path = BACKENDS.get(django_engine_path, None)
        if backend_path is None:
            self.stdout.write('Unknown backend %s' % django_engine_path)
            exit()

        _mod, _class = backend_path.split(':')
        _mod = import_module(_mod)
        return getattr(_mod, _class)

    def run_rsync(self, reversed=False):
        if not RSYNC_DESTINATION:
            self.err('Set DBDUMP_RSYNC_DESTINATION in your Django settings file!')
            exit()

        self.log('Starting rsync -> ', ending='')

        rsync_log = os.path.join('/tmp/%s.log' % uuid4().hex)
        try:
            child = run_rsync(log=rsync_log, reversed=reversed)
            if int(child.exitstatus) == 0:
                self.log('[OK]', 'SUCCESS')
            else:
                self.log('[Return code: %s]' % child.exitstatus)
        except Exception as e:
            self.err('ERROR[%s]' % e)
        finally:
            self.stdout.write(open(rsync_log).read())
            self.stdout.flush()
            os.remove(rsync_log)

    def handle_create(self, db_alias, db_attrs):
        DumpConverter = self.get_dump_converter_by_engine(db_attrs['ENGINE'])
        dc = DumpConverter(db_alias, db_attrs)
        self.log(dc.db_create_sql, 'SUCCESS')

    def handle(self, *args, **options):
        from django.conf import settings
        self.log('Running Django db dump tool', 'INFO')

        load = options.get('load')
        aliases = options.get('aliases') or settings.DATABASES.keys()

        if options.get('show_dump_cmd'):
            for db_alias, db_attrs in settings.DATABASES.items():
                if db_alias not in aliases:
                    continue

                DumpConverter = self.get_dump_converter_by_engine(db_attrs['ENGINE'])
                dh = DumpConverter(db_alias, db_attrs)
                self.log(dh.build_command())
            exit()

        if options.get('create'):
            for db_alias, db_attrs in settings.DATABASES.items():
                if db_alias not in aliases:
                    continue
                self.log('Create script for `%s`' % db_alias)
                self.handle_create(db_alias, db_attrs)
            exit()

        if load:
            exit()

        if options.get('rsync_restore') is True:
            self.run_rsync(reversed=True)
            exit()

        if options.get('start_rsync') is True:
            self.run_rsync()
            exit()

        for db_alias, db_attrs in settings.DATABASES.items():
            if db_alias not in aliases:
                continue

            DumpConverter = self.get_dump_converter_by_engine(db_attrs['ENGINE'])

            self.log('Dumping `%s` -> ' % db_alias, ending='')
            dh = DumpConverter(db_alias, db_attrs)
            if dh.execute():
                self.log('[OK]', 'SUCCESS')
            else:
                self.err('[Failed]')
            dh.remove_redundant_dumps(options.get('max_dumps'))

        if options.get('rsync'):
            self.run_rsync()

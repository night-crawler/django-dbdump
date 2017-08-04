import shlex

from subprocess import Popen, PIPE, STDOUT

from django_dbdump.exceptions import SubprocessError
from django_dbdump.backends.generic import GenericDumpConverter


class DumpConverter(GenericDumpConverter):
    cmd = '/usr/bin/pg_dump'
    extension = '.tar'
    connection_string_pattern = 'postgresql://%(username)s:%(password)s@%(host)s:%(port)s/%(database)s'

    def build_command(self):
        return '%(cmd)s -C -c -b --dbname=%(opts)s -f %(out_file)s --format=t %(extra)s' % {
            'cmd': self.cmd,
            'opts': self.pg_dbname,
            'out_file': self.dump_filepath,
            'extra': self.dump_option('extra', ''),
            'concurrency': self.dump_option('concurrency') or self.concurrency,
        }

    @property
    def pg_dbname(self):
        """
        :return: formatted connection_string_pattern
        'postgresql://%(username)s:%(password)s@%(host)s:%(port)s/%(database)s'
        """
        connection_string = self.dump_option('connection_string')
        if not connection_string:
            connection_string_pattern = self.dump_option('connection_string_pattern') or self.connection_string_pattern
            connection_string = connection_string_pattern % {
                'username': self.db_option('USER', ''),
                'password': self.db_option('PASSWORD', ''),
                'host': self.db_option('HOST', ''),
                'port': self.db_option('PORT', '5432'),
                'database': self.db_option('NAME')
            }
        return connection_string

    def execute_dump_command(self):
        full_cmd = self.build_command()
        args = shlex.split(full_cmd)
        child = Popen(args)
        streamdata = child.communicate()[0]
        if child.returncode != 0:
            raise SubprocessError('Command\n%s\nFAILED' % full_cmd)

    @property
    def db_create_sql(self):
        return """CREATE USER %(username)s WITH PASSWORD '%(password)s';
CREATE DATABASE %(database)s ENCODING '%(encoding)s' OWNER %(username)s;
GRANT ALL PRIVILEGES ON DATABASE %(database)s TO %(username)s;""" % {
            'username': self.db_option('USER', ''),
            'password': self.db_option('PASSWORD', ''),
            'database': self.db_option('NAME'),
            'encoding': 'utf8'
        }


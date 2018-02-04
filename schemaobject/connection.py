import asyncio
import re

import aiomysql
import pymysql

REGEX_RFC1738 = re.compile(r'''
            (?P<protocol>\w+)://
            (?:
                (?P<username>[^:/]*)
                (?::(?P<password>[^/]*))?
            @)?
            (?:
                (?P<host>[^/:]*)
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<database>.*))?
            ''', re.X)


def parse_database_url(url):
    matches = REGEX_RFC1738.match(url)
    result = {}

    if matches:
        if matches.group('protocol'):
            result['protocol'] = matches.group('protocol')

        if matches.group('username'):
            result['user'] = matches.group('username')

        if matches.group('password'):
            result['passwd'] = matches.group('password')

        if matches.group('database'):
            result['db'] = matches.group('database')

        if matches.group('host'):
            result['host'] = matches.group('host')

        try:
            result['port'] = int(matches.group('port'))
        except (TypeError, ValueError):
            pass

    return result


def build_database_url(host, protocol='mysql', username='root', password='', port=3306, database=None):
    if password:
        password = ':' + password
    result = "%s://%s%s@%s:%i/" % (protocol, username, password, host, port,)
    if database:
        result = result + database
    return result


class DatabaseConnection(object):
    """A lightweight wrapper around MySQLdb DB-API"""

    def __init__(self):
        self._db = None
        self.db = None
        self.host = None
        self.port = None
        self.user = None

    @property
    async def version(self):
        result = await self.execute("SELECT VERSION() as version")
        return result[0]['version']

    async def execute(self, sql, values=None):
        cursor = await self._db.cursor()
        # if isinstance(values, (basestring, unicode)):
        if isinstance(values, str):
            values = (values,)
        await cursor.execute(sql, values)

        if not cursor.rowcount:
            return None

        fields = [field[0] for field in cursor.description]
        rows = await cursor.fetchall()

        cursor.close()
        a = [dict(zip(fields, row)) for row in rows]
        return a

    async def connect(self, connection_url, charset):
        """Connect to the database"""

        kwargs = parse_database_url(connection_url)
        if not (kwargs and kwargs['protocol'] == 'mysql'):
            raise TypeError("Connection protocol must be MySQL!")

        self.db = kwargs.get('db', None)
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 3306)
        self.user = kwargs.get('user', None)
        kwargs['charset'] = charset

        # can't pass protocol to MySQLdb
        del kwargs['protocol']
        # insert charset option
        kwargs['charset'] = charset
        # add by yangmeaw
        kwargs['password'] = kwargs['passwd']
        del kwargs['passwd']
        kwargs['loop'] = asyncio.get_event_loop()

        self._db = await aiomysql.connect(**kwargs)

    def close(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()

    def __del__(self):
        self.close()


# Alias MySQL exception
DatabaseError = pymysql.Error

from schemaobject.option import SchemaOption
from schemaobject.table import table_schema_builder
from schemaobject.procedure import procedure_schema_builder
from schemaobject.collections import OrderedDict
from schemaobject.trigger import trigger_schema_builder
from schemaobject.view import view_schema_builder
import asyncio


async def database_schema_builder(instance):
    """
    Returns a dictionary loaded with all of the databases availale on
    the MySQL instance. ``instance`` must be an instance SchemaObject.

    .. note::
      This function is automatically called for you and set to
      ``schema.databases`` when you create an instance of SchemaObject

    """
    conn = instance.connection
    d = OrderedDict()
    sql = """
        SELECT SCHEMA_NAME, DEFAULT_CHARACTER_SET_NAME,
               DEFAULT_COLLATION_NAME
               FROM information_schema.SCHEMATA
        """
    if conn.db:
        sql += " WHERE SCHEMA_NAME = %s"
        params = conn.db
    else:
        params = None

    databases = await conn.execute(sql, (params,))

    if not databases:
        return d

    tasks = []

    for db_info in databases:
        name = db_info['SCHEMA_NAME']

        db = DatabaseSchema(name=name, parent=instance)
        db.options['charset'] = SchemaOption("CHARACTER SET", db_info['DEFAULT_CHARACTER_SET_NAME'])
        db.options['collation'] = SchemaOption("COLLATE", db_info['DEFAULT_COLLATION_NAME'])

        d[name] = db

        co1 = db.build_tables()
        co2 = db.build_views()
        co3 = db.build_procedures()
        co4 = db.build_triggers()

        tasks.extend([asyncio.ensure_future(co1),
                      asyncio.ensure_future(co2),
                      asyncio.ensure_future(co3),
                      asyncio.ensure_future(co4)])

    await asyncio.wait(tasks)
    return d


class DatabaseSchema(object):
    """
    Object representation of a single database schema
    (as per `CREATE DATABASE Syntax <http://dev.mysql.com/doc/refman/5.0/en/create-database.html>`_).
    Supports equality and inequality comparison of DatabaseSchemas.

    ``name`` is the database name.
    ``parent`` is an instance of SchemaObject

        '>>> for db in schema.databases:
        ...     print schema.databases[db].name
        ...
        sakila
        '>>> schema.databases['sakila'].name
        'sakila'

    .. note::
        DatabaseSchema objects are automatically created for you
        by database_schema_builder and loaded under ``schema.databases``
    """

    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self._options = None
        self.tables = None
        self.views = None
        self.procedures = None
        self.triggers = None

    async def build_tables(self):
        """
        Lazily loaded dictionary of all the tables within this database. See TableSchema for usage
          '>>> len(schema.databases['sakila'].tables)
          16
        """
        if self.tables is None:
            self.tables = await table_schema_builder(database=self)

        return self.tables

    async def build_views(self):
        """
        Lazily loaded dictionnary of all the views within this database. See ViewSchema for usage
        """
        if self.views is None:
            self_views = await view_schema_builder(database=self)

        return self.views

    @property
    def options(self):
        """
        Dictionary of the supported MySQL database options. See OptionSchema for usage.

        * CHARACTER SET  == ``options['charset']``
        * COLLATE == ``options['collation']``
        """
        if self._options is None:
            self._options = OrderedDict()

        return self._options

    async def build_procedures(self):
        """
        Lazily loaded dictionnary of all the procedures within this database. See ProcedureSchema for usage.
        """
        if self.procedures is None:
            self.procedures = await procedure_schema_builder(database=self)

        return self.procedures

    async def build_triggers(self):
        """
        Lazily loaded dictionnary of all the triggers within this database. See TriggerSchema for usage.
        """
        if self.triggers is None:
            self.triggers = await trigger_schema_builder(database=self)

        return self.triggers

    def select(self):
        """
        Generate the SQL to select this database
          >>> schema.databases['sakila'].select()
          'USE `sakila`;'
        """
        return "USE `%s`;" % self.name

    def fk_checks(self, val=1):
        if val not in (0, 1):
            val = 1

        return "SET FOREIGN_KEY_CHECKS = %s;" % val

    def alter(self):
        """
        Generate the SQL to alter this database
          >>> schema.databases['sakila'].alter()
          'ALTER DATABASE `sakila`'
        """
        return "ALTER DATABASE `%s`" % self.name

    def create(self):
        """
        Generate the SQL to create this databse
          >>> schema.databases['sakila'].create()
          'CREATE DATABASE `sakila` CHARACTER SET=latin1 COLLATE=latin1_swedish_ci;'
        """
        return "CREATE DATABASE `%s` %s %s;" % (
            self.name, self.options['charset'].create(), self.options['collation'].create()
        )

    def drop(self):
        """
        Generate the SQL to drop this database
          >>> schema.databases['sakila'].drop()
          'DROP DATABASE `sakila`;'
        """
        return "DROP DATABASE `%s`;" % self.name

    def __eq__(self, other):
        if not isinstance(other, DatabaseSchema):
            return False
        return (
                (self.options['charset'] == other.options['charset'])
                and (self.options['collation'] == other.options['collation'])
                and (self.name == other.name)
                and (self.tables == other.tables)
        )

    def __ne__(self, other):
        return not self.__eq__(other)

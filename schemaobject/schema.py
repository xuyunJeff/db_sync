from schemaobject.connection import DatabaseConnection
from schemaobject.database import database_schema_builder


class SchemaObject(object):
    """
    Object representation of a single MySQL instance.
    If database name is not specified in ``connection_url``,
    all databases on the MySQL instance will be loaded.

    ``connection_url`` - the database url as per `RFC1738 <http://www.ietf.org/rfc/rfc1738.txt>`_

      >>> schema  = schemaobject.SchemaObject('mysql://username:password@localhost:3306/sakila', charset='utf8')
      >>> schema.host
      'localhost'
      >>> schema.port
      3306
      >>> schema.user
      'username'
      >>> schema.version
      '5.1.30'
      >>> schema.charset
      'utf8'
      >>> schema.selected.name
      'sakila'

    """

    def __init__(self):
        self.databases = None
        self.connection = None
        self.host = None
        self.port = None
        self.user = None
        self.table_names = None
        self.version = None

    async def build_database(self, connection_url, charset, table_names=None):
        self.connection = DatabaseConnection()
        await self.connection.connect(connection_url, charset)
        self.version = await self.connection.version()

        self.host = self.connection.host
        self.port = self.connection.port
        self.user = self.connection.user
        self.table_names = table_names

        self.databases = await database_schema_builder(instance=self)

    @property
    def selected(self):
        """
        Returns the DatabaseSchema object associated with the database name in the connection url

          >>> schema.selected.name
          'sakila'
        """
        if self.connection.db:
            return self.databases[self.connection.db]
        else:
            return None

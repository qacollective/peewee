from peewee import *

from .base import IS_MYSQL
from .base import ModelTestCase
from .base import TestModel
from .base import db_loader
from .base import skip_case_unless


mysql_ext_db = db_loader('mysqlconnector')


class Person(TestModel):
    first = CharField()
    last = CharField()
    dob = DateField()


class Note(TestModel):
    person = ForeignKeyField(Person, backref='notes')
    content = TextField()
    timestamp = TimestampField(resolution=1e6)


@skip_case_unless(IS_MYSQL)
class TestMySQLConnector(ModelTestCase):
    requires = [Person, Note]

    def test_basic_operations(self):
        with self.database.atomic():
            charlie, huey, zaizee = [Person.create(first=f, last='leifer')
                                     for f in ('charlie', 'huey', 'zaizee')]
            # Use nested-transaction.
            with self.database.atomic():
                data = (
                    (charlie, ('foo', 'bar', 'zai')),
                    (huey, ('meow', 'purr', 'hiss')),
                    (zaizee, ()))
                for person, notes in data:
                    for note in notes:
                        Note.create(person=person, content=note)

        people = Person.select().order_by(Person.first)
        self.assertEqual([person.first for person in people],
                         ['charlie', 'huey', 'zaizee'])

        with self.assertQueryCount(1):
            notes = (Note
                     .select(Note, Person)
                     .join(Person)
                     .order_by(Note.content))
            self.assertEqual([(n.person.first, n.content) for n in notes], [
                ('charlie', 'bar'),
                ('charlie', 'foo'),
                ('huey', 'hiss'),
                ('huey', 'meow'),
                ('huey', 'purr'),
                ('charlie', 'zai')])

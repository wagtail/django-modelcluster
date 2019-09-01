from __future__ import unicode_literals

from django.test import TestCase

from tests.models import Person


class TestLoadsParentalManyToManyToOrderedModel(TestCase):

    fixtures = ["parentalmanytomany-to-ordered-model.json"]

    def test_data_loads_from_fixture(self):
        """
        The main test here is that the fixture loads without errors. The code
        below code then confirms that the relationship was set correctly.
        """
        person = Person.objects.get(id=1)
        self.assertEqual(list(person.houses.values_list("id", flat=True)), [1, 2])

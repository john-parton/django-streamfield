"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

from streamblocks import models as streamblocks


class SimpleTest(TestCase):
    def test_basic_create(self):
        rich_text = streamblocks.RichText.objects.create()
        
        assert False, rich_text


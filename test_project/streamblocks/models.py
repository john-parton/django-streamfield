from django.db import models

from streamfield.fields import StreamField


class RichText(models.Model):
    text = models.TextField(blank=True, null=True)   

    options = {
        "gray_bgr": {
            "label": "Block on gray background",
            "type": "checkbox",
            "default": False
        }
    }

    class Meta:
        # This will use as name of block in admin
        verbose_name="Text"

# list of objects
class Column(models.Model):
    text = models.TextField(null=True, blank=True)
    
    # StreamField option for list of objects
    as_list = True

    class Meta:
        verbose_name="Column"
        verbose_name_plural="Columns"

# Register blocks for StreamField as list of models
STREAMBLOCKS_MODELS = [
    RichText,
    Column
]


class ContentWrapper(models.Model):
    stream = StreamField()
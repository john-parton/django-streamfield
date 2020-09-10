from django.conf import settings

# Consider removing this
BLOCK_OPTIONS = getattr(settings, "STREAMFIELD_BLOCK_OPTIONS", {})
SHOW_ADMIN_HELP_TEXT = getattr(settings, "STREAMFIELD_SHOW_ADMIN_HELP_TEXT", True)
# Consider flipping this one
DELETE_BLOCKS_FROM_DB = getattr(settings, "STREAMFIELD_DELETE_BLOCKS_FROM_DB", True)

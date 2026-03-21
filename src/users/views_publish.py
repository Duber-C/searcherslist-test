"""
DEPRECATED: publish views moved to `users.views.publish`.
This file is intentionally left as a tiny shim to avoid accidental imports of the old implementation.
"""

from warnings import warn
warn("users.views_publish is deprecated; use users.views.publish instead", DeprecationWarning)

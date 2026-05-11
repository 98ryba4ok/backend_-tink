import logging
import sentry_sdk
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def sentry_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        sentry_sdk.capture_exception(exc)
        logger.exception('Unhandled exception in view: %s', exc)
    elif response.status_code >= 500:
        sentry_sdk.capture_exception(exc)
        logger.error('Server error %s: %s', response.status_code, exc)
    return response

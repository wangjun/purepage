import requests
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CouchdbException(Exception):

    def __init__(self, resp):
        self.resp = resp
        self.status_code = resp.status_code
        self.json = None
        self.error = None
        self.reason = None
        try:
            self.json = resp.json()
            self.error = self.json.get('error')
            self.reason = self.json.get('reason')
        except Exception as ex:
            logger.debug("Can't parse error message: %s" % ex)

    def __repr__(self):
        return "<CouchdbException %s %s>: %s" %\
            (self.status_code, self.error or '', self.reason or '')

    def __str__(self):
        return "<%s %s>: %s" %\
            (self.status_code, self.error or '', self.reason or '')


class BadRequest(CouchdbException):
    """400"""


class Unauthorized(CouchdbException):
    """401"""


class Forbidden(CouchdbException):
    """403"""


class NotFound(CouchdbException):
    """404"""


class ResourceNotAllowed(CouchdbException):
    """405"""


class NotAcceptable(CouchdbException):
    """406"""


class Conflict(CouchdbException):
    """409"""


class PreconditionFailed(CouchdbException):
    """412"""


class BadContentType(CouchdbException):
    """415"""


class RequestedRangeNotSatisfiable(CouchdbException):
    """416"""


class ExpectationFailed(CouchdbException):
    """417"""


class InternalServerError(CouchdbException):
    """500"""

exceptions = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    405: ResourceNotAllowed,
    406: NotAcceptable,
    409: Conflict,
    412: PreconditionFailed,
    415: BadContentType,
    416: RequestedRangeNotSatisfiable,
    417: ExpectationFailed,
    500: InternalServerError
}


def get_exception(resp):
    """Get Exception class by response status code"""
    Ex = exceptions.get(resp.status_code)
    if Ex is None:
        Ex = CouchdbException
    return Ex(resp)


class HttpRequestsImpl:
    """A class implement request method using requests lib"""

    def request(self, method, url, **kwargs):
        """
        Send request and return json result

        :param  method: http method
        :param     url: taget url
        :param headers: http headers
        :type  headers: dict
        :param    data: request data
        :param  params: query params
        :param  stream: return raw response object or not
        :type   stream: bool
        :return: json or reponse object if response status code < 400
        :raises: CouchdbException if status code >= 400
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault('Accept', 'application/json')
        kwargs["headers"].setdefault('Content-Type', 'application/json')
        if "data" in kwargs and not isinstance(kwargs['data'], bytes):
            data = json.dumps(
                kwargs["data"], ensure_ascii=False).encode('utf-8')
            kwargs["data"] = data
        logger.debug('"%s %s"\n%s' % (method, url, kwargs))
        resp = requests.request(method, url, **kwargs)
        stream = kwargs.get('stream', False)
        if resp.status_code >= 200 and resp.status_code <= 299:
            if not stream:
                if resp.content:
                    return resp.json()
                else:
                    return None
            else:
                return resp
        else:
            ex = get_exception(resp)
            raise ex

import traceback


class Log500ErrorsMiddleware:
    """
    Django Middleware that logs 500 error stack traces to the server console.

    Useful for logging 500 errors when DEBUG=True.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        print('\n\n----intercepted 500 error stack trace----')
        print(exception)
        print(type(exception))
        tb = exception.__traceback__
        print(
            '\n'.join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    tb,
                ),
            )
        )
        print('-----------------------------------------\n\n')
        return None

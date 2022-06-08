#!/usr/bin/env python3

import json
import requests
import logging


class Router:

    class NoInternetConnection(Exception):
        def __init__(self):
            super().__init__()

    def __init__(self, url: str) -> None:
        """
        """
        self.url = url

    def route_online(self, data: dict) -> None:
        """
        """
        try:
            # route_results = requests.post(self.url, json=data, verify=True, cert=ssl)
            # route_results = requests.post(self.url, json=data, verify=False)
            route_results = requests.post(self.url, json=data)
            route_results.raise_for_status()

        except requests.ConnectionError as error:
            """In the event of a network problem (e.g. DNS failure, refused connection, etc).
            Requests will raise a ConnectionError exception.
            """
            FAILED_DNS = "[Errno -2]"
            NAME_RESOLUTION_ERRNO = "[Errno -3]"

            if NAME_RESOLUTION_ERRNO in error.args[0].reason.args[0]:
                """There be no internet... should retry
                """
                raise self.NoInternetConnection

            else:
                raise error

        except requests.Timeout as error:
            """If a request times out, a Timeout exception is raised.
            """
            raise error

        except requests.TooManyRedirects as error:
            """If a request exceeds the configured number of maximum redirections
            a TooManyRedirects exception is raised.
            """
            raise error

        except Exception as error:
            raise error

        else:
            return route_results

#!/usr/bin/env python3

import json
import requests
import logging


class Router:

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

        except ConnectionError as error:
            """In the event of a network problem (e.g. DNS failure, refused connection, etc).
            Requests will raise a ConnectionError exception.
            """
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

        else:
            return route_results

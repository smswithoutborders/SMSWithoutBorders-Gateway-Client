#!/usr/bin/env python3

import json
import requests
import logging


class Router:

    class NoInternetConnection(Exception):
        def __init__(self):
            super().__init__()

    def __init__(self, routing_urls: [], text: str, MSISDN: str) -> None:
        """
        """
        self.text = text

        self.MSISDN = MSISDN

        self.routing_urls = routing_urls

    def route(self) -> bool:
        """
        """
        try:
            my_fault_cannot_route = False # keep message if True
            for i in range(len(self.routing_urls)):
                url = self.routing_urls[i]
                logging.debug("routing to: %s", url)

                try:
                    json_body = {"text":self.text, "MSISDN":self.MSISDN}
                    self.route_online(url=url, data=json_body)

                except Router.NoInternetConnection as error:
                    logging.warn( 
                            "** no internet connection... returning message to queue")
                    my_fault_cannot_route = True
                    break

                except Exception as error:
                    logging.exception(error)

        except Exception as error:
            logging.exception(error)
            raise error

        else:
            if my_fault_cannot_route:
                return False

        return True


    def route_online(self, url: str, data: dict) -> None:
        """
        """
        try:
            # route_results = requests.post(self.url, json=data, verify=True, cert=ssl)
            # route_results = requests.post(self.url, json=data, verify=False)
            route_results = requests.post(url, json=data)
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

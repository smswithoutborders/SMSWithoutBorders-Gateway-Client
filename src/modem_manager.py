#!/usr/bin/env python3

import logging
import threading
import time
from deku import Deku

from common.mmcli_python.modem import Modem

class ModemManager:
    """Summary of ModemManager
    Attributes:
    """
    def __init__(self, daemon_sleep_time:int=3)->None:
        """Initialize a modem manager instance.
        """
        self.models = []
        self.daemon_sleep_time=daemon_sleep_time
        self.active_nodes = {}

    def add_model(self, model) -> None:
        """Add model to daemon.

        The `main()` would be called for each model included.

            Args:
                model: 
                    DataType (any class) which has a method called `main`
                    that will be called by the daemon thread
        """
        self.models.append(model)

    def daemon(self) -> None:
        """Binds modems to models

        Monitors I/O changes of modem. Once a modem is active, it gets 
        added to the list of active nodes. 
        For each active node, the requested model will be triggered for them.

            Args:
                model: 
                    Any class that extends model class 
                    daemon_sleep_time: How long the daemon should sleep thread
                    after listening

            Returns: None
        """

        logging.debug("initializing modem manager daemon")

        try:
            th_hardware_state_monitor = threading.Thread( 
                    target=self.__daemon_hardware_state__, 
                    daemon=True)
        except Exception as error:
            raise error
        else:
            try:
                th_hardware_state_monitor.start()

                # if state dies, no need for active
                th_hardware_state_monitor.join()
            except Exception as error:
                raise error

    def __refresh_nodes__(self, available_modems)->None:
        """Checks HW available modems against active running nodes
        """
        modems = [modem.imei for modem in available_modems]
        active_nodes = self.active_nodes.keys()
        not_active = list(set(active_nodes).difference(modems))
        logging.debug("inactive nodes: %s", not_active)

        for modem_imei in not_active:
            try:
                del self.active_nodes[modem_imei]
                logging.debug("removed modem %s", self.modem.imei)
            except Exception as error:
                logging.exception(error)
        logging.debug("refreshed nodes")


    def __daemon_hardware_state__(self) -> None:
        while True:
            try:
                available_modems, locked_modems,_ = Deku.get_available_modems()
                logging.debug("+ Available modems %s Locked modems %s", 
                        [modem.index for modem in available_modems], \
                        [modem.index for modem in locked_modems])

                if len(available_modems) < 1:
                    time.sleep(self.daemon_sleep_time)
                    continue

            except Exception as error:
                raise error

            else:
                try:
                    self.__refresh_nodes__(available_modems + locked_modems)
                    self.__add_active_nodes__(modems=available_modems)
                except Exception as error:
                    raise error

            finally:
                logging.debug("sleeping hardware monitor daemon")
                time.sleep(self.daemon_sleep_time)

    def __add_active_nodes__(self, modems:list()) -> None:
        logging.debug("# of models %d", len(self.models))
        for modem in modems:
            if modem.imei not in self.active_nodes:
                if not Deku.modem_ready(modem, index_only=True):
                    continue
                
                for _model in self.models:
                    logging.debug("initializing modem for %s %s", 
                            modem.imei, _model)
                    node_operator = Deku.get_modem_operator_name(modem)

                    model = _model.init(modem=modem, active_nodes=self.active_nodes)

                    modem_thread = threading.Thread(
                            target=model.main,
                            daemon=True)

                    # TODO won't work with multiple models
                    if not modem.imei in self.active_nodes or \
                        not model.__class__.__name__ in self.active_nodes[modem.imei]:
                            modem_thread.start()
                            logging.debug("started %s for %s", modem.imei, model)

                            self.active_nodes[modem.imei] = {
                                    model.__class__.__name__: modem_thread}
                            # self.active_nodes[modem.imei][model] = modem_thread
                            # self.active_nodes[modem.imei] = [modem_thread, model]
                            logging.debug("added %s to active nodes %s", 
                                    modem.imei, model.__class__.__name__)

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
            th_active_state_monitor = threading.Thread(
                target=self.__daemon_active_state_monitor__, 
                daemon=True)

        except Exception as error:
            raise error
        else:
            try:
                th_hardware_state_monitor.start()
                th_active_state_monitor.start()

                # if state dies, no need for active
                th_hardware_state_monitor.join()
            except Exception as error:
                raise error


    def __daemon_active_state_monitor__(self) -> None:
        logging.debug("monitoring active modems")
        while True:
            try:
                for modem_imei, thread_model in self.active_nodes.items():
                    model_thread = thread_model[0]
                    try:
                        if model_thread.native_id is None:
                            model_thread.start()
                            logging.debug("started thread: %s", modem_imei)

                        if not model_thread.is_alive():
                            del self.active_nodes[modem_imei]
                            logging.debug("removed thread: %s", modem_imei)

                    except Exception as error:
                        raise error

            except Exception as error:
                raise error

            finally:
                time.sleep(self.daemon_sleep_time)

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
                    self.__add_active_nodes__(modems=available_modems)
                except Exception as error:
                    raise error

            finally:
                logging.debug("sleeping hardware monitor daemon")
                time.sleep(self.daemon_sleep_time)

    def __add_active_nodes__(self, modems:list()) -> None:
        for modem in modems:
            if modem.index not in self.active_nodes:
                if not Deku.modem_ready(modem, index_only=True):
                    continue
                
                for _model in self.models:
                    node_operator = Deku.get_modem_operator(modem)

                    model = _model.init(modem=modem)

                    modem_thread = threading.Thread(
                            target=model.main,
                            daemon=True)

                    self.active_nodes[modem.imei] = [modem_thread, model]
                    logging.debug("added %s to active nodes", modem.imei)

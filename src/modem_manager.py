#!/usr/bin/env python3

import logging
import threading
import time
from deku import Deku

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
        self.models.append(model)

    def daemon(self) -> None:
        """Binds modems to models

        lengthy description

            Args:
            model: Any class that extends model class
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
        for modem_imei, thread_model in self.active_nodes.items():
            model_thread = thread_model[0]
            try:
                if model_thread.native_id is None:
                    thread.start()
                    logging.debug("started thread: %s", modem_imei)

            except Exception as error:
                raise error

    def __daemon_hardware_state__(self) -> None:
        while True:
            try:
                available_modems, locked_modems,_ = Deku.get_available_modems()
                logging.debug("available modems:%s\tlocked modems:%s",
                        available_modems, locked_modems)

                if len(available_modems) < 1:
                    time.sleep(self.daemon_sleep_time)
                    continue

            except Exception as error:
                raise error

            else:
                try:
                    self.__add_active_nodes__(indexes=available_modems)
                except Exception as error:
                    raise error

            finally:
                time.sleep(self.daemon_sleep_time)

    def __add_active_nodes__(self, indexes:list()) -> None:
        for modem_index in indexes:
            if modem_index not in self.active_nodes:
                if not Deku.modem_ready(modem_index, index_only=True):
                    continue
                
                for _model in self.models:
                    modem = Modem(modem_index)
                    node_operator = Deku.get_modem_operator(modem)

                    model = _model.init(modem=modem)

                    modem_thread = threading.Thread(
                            target=model.main,
                            args=(modem,),
                            daemon=True)

                    self.active_nodes[modem.imei] = [modem_thread, model]

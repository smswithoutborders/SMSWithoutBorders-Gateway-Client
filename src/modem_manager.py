#!/usr/bin/env python3

class ModemManager:
    def init_daemon(self, model:Model, daemon_sleep_time:int=3) -> None:
        logging.daemon("initializing modem manager daemon")

        self.daemon_sleep_time = daemon_sleep_time
        
        self.model = model

        self.active_nodes = []

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
                indexes, locked_indexes = Deku.modems_ready(remove_lock=True, index_only=True)
                logging.debug("available modems %d %s, locked modems %d %s", 
                        len(indexes), indexes, len(locked_indexes), locked_indexes)

                if len(indexes) < 1:
                    time.sleep(self.sleep_time)
                    continue

            except Exception as error:
                raise error

            else:
                try:
                    self.__add_active_nodes__(indexes=indexes)
                except Exception as error:
                    raise error

            finally:
                time.sleep(self.daemon_sleep_time)

    def __add_active_nodes__(self, indexes:list()) -> None:
        for modem_index in indexes:
            if modem_index not in self.active_nodes:
                if not self.deku.modem_ready(modem_index, index_only=True):
                    continue
                try:
                    modem = Modem(modem_index)
                    node_operator = Deku.get_modem_operator(modem)

                    model = self.model.init(modem=modem)

                    modem_thread = threading.Thread(
                            target=model.main, daemon=True)

                    self.active_nodes[modem.imei] = [modem_thread, model]

                except Exception as error:
                    raise error

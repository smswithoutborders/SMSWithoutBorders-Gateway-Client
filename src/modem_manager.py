#!/usr/bin/env python3

import threading
import logging
import time
import configparser

import dbus

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from modem import Modem

from enum import Enum

class ModemManager:
    """Manages the comings and goings of the modems.
    This model begins activities for connected or newly plugged in modems.
    """

    def __init__(self)->None:
        """Initialize a modem manager instance.
        """
        self.active_modems = {}
        self.modem_connected_handlers = []

        self.name = 'org.freedesktop.ModemManager1'
        self.path = '/org/freedesktop/ModemManager1'
        self.obj_mng_iface = 'org.freedesktop.DBus.ObjectManager'

        self.interface_added_str = "InterfacesAdded"
        self.interface_removed_str = "InterfacesRemoved"

        DBusGMainLoop(set_as_default=True)
        self.loop = GLib.MainLoop()

        self.bus = dbus.SystemBus()


    def __list_modems__(self) -> None:
        """
        """
        dbus_mm = self.bus.get_object(self.name, self.path, True)

        self.mm_iface_obj_mng = dbus.Interface(dbus_mm, dbus_interface=self.obj_mng_iface)

        managed_objects : dict = self.mm_iface_obj_mng.GetManagedObjects()

        for object_path, _ in managed_objects.items():
            self.modem_connected(object_path)

    def list_modems(self) -> {}:
        """
        """
        dbus_mm = self.bus.get_object(self.name, self.path, True)

        self.mm_iface_obj_mng = dbus.Interface(dbus_mm, dbus_interface=self.obj_mng_iface)

        managed_objects : dict = self.mm_iface_obj_mng.GetManagedObjects()

        for object_path, _ in managed_objects.items():
            self.__add_modem__(object_path)

        return self.active_modems
    
    def get_modem(self, modem_path: str) -> Modem:
        """
        """
        if modem_path in self.active_modems:
            return self.active_modems[modem_path]
        
        return None

    def __add_modem__(self, modem_path: str) -> Modem:
        """
        """

        try:
            modem = Modem(bus=self.bus, modem_path=modem_path)

        except Exception as error:
            raise error

        else:
            self.active_modems[modem_path] = modem
            logging.debug("Added modem at path: %s", modem_path)


            return modem


    def __remove_modem__(self, modem_path: str) -> None:
        """
        """
        try:
            """
            - All the models using this modem would stop functioning at this point.
            """
            self.active_modems[modem_path].remove()
        except Exception as error:
            logging.exception(error)
        else:

            del self.active_modems[modem_path]
            logging.warning("Deleted modem at path: %s", modem_path)


    def modem_connected(self, modem_path, *args):
        """
        """
        logging.info("New modem connected:\n\t%s", modem_path)

        try:
            modem = self.__add_modem__(modem_path)

            for modem_handler in self.modem_connected_handlers:
                connected_modem_thread = threading.Thread(target=modem_handler,
                        args=(modem,), daemon=True)
                connected_modem_thread.start()

            logging.debug("Exiting modem connected: %s", self)
        except Exception as error:
            logging.exception(error)


    def modem_disconnected(self, modem_path):
        """
        """
        self.__remove_modem__(modem_path)

        logging.warning("Modem removed: %s", modem_path)

        logging.debug("# Active modems: %d", len(self.active_modems))


    def handler_function_interfaces_changed(self, *args, **kwargs) -> None:
        """
        """
        modem_path = ""

        if kwargs['interface'] == self.obj_mng_iface:
            modem_path = args[0]

        # check if truly added
        if kwargs['member'] == self.interface_added_str:
            self.modem_connected(modem_path)

        elif kwargs['member'] == self.interface_removed_str:
            self.modem_disconnected(modem_path)


    def daemon(self) -> None:
        """
        """
        self.__list_modems__()

        """Signal modem has been removed"""
        self.mm_iface_obj_mng.connect_to_signal(
                self.interface_removed_str,
                handler_function=self.handler_function_interfaces_changed, 
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        """Signal modem has been added"""
        self.mm_iface_obj_mng.connect_to_signal(
                self.interface_added_str,
                handler_function=self.handler_function_interfaces_changed, 
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.loop.run()


    def add_modem_connected_handler(self, modem_connected_handler) -> None:
        """
        """
        self.modem_connected_handlers.append(modem_connected_handler)


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')

    def send_sms(modem):
        import inspect
        import sys

        print(inspect.signature(modem.messaging.messaging.Create))

        try:
            number=sys.argv[1]
            modem.messaging.send_sms(text="hello world", number=number)
        except dbus.exceptions.DBusException as error:
            logging.error("something went wrong with sending...")
            raise error

        except Exception as error:
            logging.exception(error)


    mm = ModemManager()

    mm.add_modem_connected_handler(send_sms)

    mm.daemon()

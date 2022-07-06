import threading
import dbus
from enum import Enum
import logging
import time

from sms import SMS

dbus_name = 'org.freedesktop.ModemManager1'
modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'


class Messaging:
    dbus_name = 'org.freedesktop.ModemManager1'
    modem_dbus_messaging_iface = 'org.freedesktop.ModemManager1.Modem.Messaging'

    class MMSmsStorage(Enum):
        MM_SMS_STORAGE_UNKNOWN = 0
        MM_SMS_STORAGE_SM      = 1
        MM_SMS_STORAGE_ME      = 2
        MM_SMS_STORAGE_MT      = 3
        MM_SMS_STORAGE_SR      = 4
        MM_SMS_STORAGE_BM      = 5
        MM_SMS_STORAGE_TA      = 6


    def __init__(self, modem, *args) -> None:
        """
        """
        self.modem = modem

        self.__new_received_message_handlers__ = []
        self.__sms__ = {}

        self.messaging = dbus.Interface(
                self.modem.dbus_modem, dbus_interface=self.modem_dbus_messaging_iface)

        self.messaging.connect_to_signal(
                "Added",
                handler_function=self.__message_property_changed_added__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.messaging.connect_to_signal(
                "Deleted",
                handler_function=self.__message_property_changed_deleted__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        logging.debug("new messaging instance created: %s", self)


    def __add_message__(self, message: SMS) -> None:
        """
        """
        if message.__is_received_message__():
            self.broadcast_new_message(message)

        elif message.__is_receiving_message__():
            self.__sms__[message.message_path] = message
            logging.debug("added new sms: %s", message.message_path)


    def __message_property_changed_added__(self, *args, **kwargs) -> None:
        """
        """
        logging.debug("Message property changed Added - %s", args)

        message_path = args[0]
        received_from_network = args[1]

        if received_from_network:
            sms = SMS(message_path, self)
            self.__add_message__(sms)


    def __message_property_changed_deleted__(self, *args, **kwargs) -> None:
        """
        """
        message_path = args[0]
        logging.debug("Message property changed Deleted - %s", args)

        if message_path in self.__sms__:
            del self.__sms__[message_path]


    def check_available_messages(self) -> None:
        """
        """
        logging.debug("checking for available messages")
        try:
            available_messages = self.messaging.List()

            logging.debug("# Available received messages - [%d]", 
                    len(available_messages))

            for message_path in available_messages:

                message = SMS(message_path, self)

                self.__add_message__(message)


        except Exception as error:
            raise error


    def broadcast_new_message(self, message: SMS) -> None:
        """
        """
        for message_handler in self.__new_received_message_handlers__:

            message_handler_thread = threading.Thread(target=message_handler,
                    args=(message,), daemon=True)

            message_handler_thread.start()


    def add_new_message_handler(self, new_received_message_handler) -> None:
        """
        """
        self.__new_received_message_handlers__.append(new_received_message_handler)


    def __create_sms__(self, 
            text: str, 
            number: str, 
            delivery_report_request: bool = False) -> str:
        """
        """

        data = {'text':text, 
                'number': number,
                'delivery-report-request': delivery_report_request}

        try:
            message_path = self.messaging.Create(data)
        except Exception as error:
            raise error

        return message_path


    def send_sms(self, 
            text: str, 
            number: str, 
            delivery_report_request: bool = False, **kwargs) -> None:
        """
        """
        try:
            message_path = self.__create_sms__(text, number)

            logging.debug("created new sms: %s", message_path)

        except dbus.exceptions.DBusException as error:
            raise error

        except Exception as error:
            raise error

        else:
            try:
                sms = SMS(message_path, self)
                sms.send(message_path)

            except dbus.exceptions.DBusException as error:
                raise error

            except Exception as error:
                raise error

            finally:
                # remove this if monitoring for DeliveryReport
                self.__delete_sms__(message_path)
                time.sleep(3)


    def __delete_sms__(self, message_path:str) -> None:
        """
        """
        try:
            self.messaging.Delete(message_path)
        except Exception as error:
            logging.exception(error)
        else:
            logging.warning("Deleted message: %s", message_path)

    def clear_stack(self) -> None:
        """
        """
        logging.debug("clearing message stack...")
        try:
            available_messages = self.messaging.List()
            logging.debug("# Available received messages - [%d]", 
                    len(available_messages))

            for message_path in available_messages:
                message = SMS(message_path, self)

                if (message.is_sent_message() or message.is_delivery_report_message()):
                    self.__delete_sms__(message_path)
        except Exception as error:
            raise error

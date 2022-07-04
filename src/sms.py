import threading
import dbus
from enum import Enum
import logging

dbus_name = 'org.freedesktop.ModemManager1'
modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'

class SMS:

    class MMSmsState(Enum):
        MM_SMS_STATE_UNKNOWN   = 0
        MM_SMS_STATE_STORED    = 1
        MM_SMS_STATE_RECEIVING = 2
        MM_SMS_STATE_RECEIVED  = 3
        MM_SMS_STATE_SENDING   = 4
        MM_SMS_STATE_SENT      = 5

    def __init__(self, message_path: str, messaging, *args) -> None:
        """
        """
        self.messaging = messaging 
        self.message_path = message_path

        self.dbus_message = messaging.modem.bus.get_object(dbus_name, self.message_path, True)

        self.props = dbus.Interface(
                self.dbus_message, dbus_interface=modem_dbus_props_iface)

        self.props.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__message_property_changed__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.modem_dbus_sms_iface = "org.freedesktop.ModemManager1.Sms"
        self.sms = dbus.Interface(
                self.dbus_message, dbus_interface=self.modem_dbus_sms_iface)

    def send(self) -> None:
        """
        """
        try:
            logging.debug("Sending new sms message")
            send_status = self.sms.Send()
            logging.debug("sent sms message: %s", send_status)
        except Exception as error:
            logging.exception(error)

    def __message_property_changed__(self, *args, **kwargs) -> None:
        """
        """
        member = args[0]
        change_props = args[1]

        logging.debug("Message property changed - %s, %s", member, args)

        if ('State' in change_props
                and 
                self.MMSmsState(change_props['State']) == self.MMSmsState.MM_SMS_STATE_RECEIVED):
            self.messaging.broadcast_new_message(self)

    def get_property(self, property_name: str) -> None:
        """
        """
        try:
            return self.props.Get(self.modem_dbus_sms_iface, property_name)
        except Exception as error:
            raise error

    def set_property(self, property_name: str, value: str) -> None:
        """
        """
        try:
            return self.props.Set(self.modem_dbus_sms_iface, property_name, value)
        except Exception as error:
            raise error

    def new_received_message(self) -> tuple:
        """
        """
        try:
            text = self.get_property("Text")
            number = self.get_property("Number")
            timestamp = self.get_property("Timestamp")


        except Exception as error:
            logging.exception(error)

        else:
            return text, number, timestamp


    def __is_receiving_message__(self) -> bool:
        """
        """
        return (
                self.MMSmsState(self.get_property("State"))
                == 
                self.MMSmsState.MM_SMS_STATE_RECEIVING )


    def __is_received_message__(self) -> bool:
        """
        """

        """
        state = self.get_property(message_path, "State") 
        logging.debug("message state: %s", state)
        """

        return (
                self.MMSmsState(self.get_property("State"))
                == 
                self.MMSmsState.MM_SMS_STATE_RECEIVED )


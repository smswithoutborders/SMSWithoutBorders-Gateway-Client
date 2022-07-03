
import threading
import dbus
from enum import Enum
import logging

class Messaging:
    dbus_name = 'org.freedesktop.ModemManager1'

    class MMSmsState(Enum):
        MM_SMS_STATE_UNKNOWN   = 0
        MM_SMS_STATE_STORED    = 1
        MM_SMS_STATE_RECEIVING = 2
        MM_SMS_STATE_RECEIVED  = 3
        MM_SMS_STATE_SENDING   = 4
        MM_SMS_STATE_SENT      = 5

    class MMSmsStorage(Enum):
        MM_SMS_STORAGE_UNKNOWN = 0
        MM_SMS_STORAGE_SM      = 1
        MM_SMS_STORAGE_ME      = 2
        MM_SMS_STORAGE_MT      = 3
        MM_SMS_STORAGE_SR      = 4
        MM_SMS_STORAGE_BM      = 5
        MM_SMS_STORAGE_TA      = 6


    def __init__(self, bus, message_path: str, modem, *args) -> None:
        """
        """
        self.message_path = message_path
        self.bus = bus
        self.modem = modem

        self.modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'
        self.modem_dbus_sms_iface = "org.freedesktop.ModemManager1.Sms"

        dbus_message = self.bus.get_object(self.dbus_name, self.message_path, True)


        self.props = dbus.Interface(
                dbus_message, dbus_interface=self.modem_dbus_props_iface)

        self.sms = dbus.Interface(
                dbus_message, dbus_interface=self.modem_dbus_sms_iface)

        self.props.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__message_property_changed_added__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')


    def __message_property_changed_added__(self, *args, **kwargs) -> None:
        """
        """
        member = args[0]
        change_props = args[1]

        logging.debug("Message property changed - %s, %s", member, args)

        if ('State' in change_props
                and 
                self.MMSmsState(change_props['State']) == self.MMSmsState.MM_SMS_STATE_RECEIVED):
            """
            """
            self.modem.__waited_completed__(self)


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


    def __store__(self) -> None:
        """
        """
        try:
            self.sms.Store(self.MMSmsStorage.MM_SMS_STORAGE_ME.value)
        except Exception as error:
            logging.exception(error)
        else:
            logging.debug("stored message: %s", self.message_path)



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



class Modem:
    """
    """
    dbus_name = 'org.freedesktop.ModemManager1'
    modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'
    modem_3gpp_interface = 'org.freedesktop.ModemManager1.Modem.Modem3gpp'
    modem_dbus_messaging_iface = 'org.freedesktop.ModemManager1.Modem.Messaging'

    class MMModem3gppRegistrationState(Enum):
        """
        """
        MM_MODEM_3GPP_REGISTRATION_STATE_IDLE                       = 0
        MM_MODEM_3GPP_REGISTRATION_STATE_HOME                       = 1
        MM_MODEM_3GPP_REGISTRATION_STATE_SEARCHING                  = 2
        MM_MODEM_3GPP_REGISTRATION_STATE_DENIED                     = 3
        MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN                    = 4
        MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING                    = 5
        MM_MODEM_3GPP_REGISTRATION_STATE_HOME_SMS_ONLY              = 6
        MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING_SMS_ONLY           = 7
        MM_MODEM_3GPP_REGISTRATION_STATE_EMERGENCY_ONLY             = 8
        MM_MODEM_3GPP_REGISTRATION_STATE_HOME_CSFB_NOT_PREFERRED    = 9
        MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING_CSFB_NOT_PREFERRED = 10
        MM_MODEM_3GPP_REGISTRATION_STATE_ATTACHED_RLOS              = 11


    def __init__(self, bus, modem_path, *args) -> None:
        """
        TODO: 
            - Check if modem is Disabled and Enable it
        """
        super().__init__()

        self.bus = bus
        self.modem_path = modem_path
        dbus_modem = bus.get_object(self.dbus_name, self.modem_path, True)

        self.connected = True

        self.props = dbus.Interface(dbus_modem, dbus_interface=self.modem_dbus_props_iface)
        self.props.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__modem_property_changed__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.messaging = dbus.Interface(
                dbus_modem, dbus_interface=self.modem_dbus_messaging_iface)

        self.messaging.connect_to_signal(
                "Added",
                handler_function=self.__message_property_changed_added__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.messaging.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__message_property_changed_added__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.__new_received_message_handlers__ = []
        self.__modem_is_ready_handlers__ = []
        self.__modem_is_not_ready_handlers__ = []

    def __modem_property_changed__(self, *args, **kwargs) -> None:
        """
        TODO:
            - State changes in the modem which controls most of the loops will be controlled
            from here.

            - Changes such as OperatorCode == '' means the modem cannot perform simcard related
            activites.

            - In
        """
        member = args[0]
        change_props = args[1]


        logging.debug("Modem property changed - %s", member)

        if 'OperatorCode' in change_props:
            operator_code = change_props['OperatorCode']

            logging.debug("%s: changed operator code: %s", 
                    member, operator_code)

            if self.is_ready():
                self.__broadcast_ready_modem__()

            else:
                self.__broadcast_not_ready_modem__()



    def get_3gpp_properties(self) -> dict:
        """
        """
        try:
            return self.props.GetAll(self.modem_3gpp_interface)
        except Exception as error:
            raise error


    def get_3gpp_property(self, property_name):
        """
        """
        try:
            return self.props.Get(self.modem_3gpp_interface, property_name)
        except Exception as error:
            raise error

    def remove(self):
        """
        TODO: kill all infinite loops from here by changing their threads to set()
        - https://docs.python.org/3/library/threading.html#threading.Condition.wait_for
        """

        try:
            self.connected = False
            self.__broadcast_not_ready_modem__()

        except Exception as error:
            logging.exception(error)


    def __broadcast_new_message__(self, message: Messaging) -> None:
        """
        """
        for message_handler in self.__new_received_message_handlers__:
            message_handler_thread = threading.Thread(target=message_handler,
                    args=(message, self), daemon=True)

            message_handler_thread.start()



    def __broadcast_ready_modem__(self) -> None:
        """
        """
        for modem_ready_handler in self.__modem_is_ready_handlers__:
            modem_ready_handler_thread = threading.Thread(target=modem_ready_handler,
                    args=(self,), daemon=True)

            modem_ready_handler_thread.start()


    def __broadcast_not_ready_modem__(self) -> None:
        """
        """
        for modem_not_ready_handler in self.__modem_is_not_ready_handlers__:
            modem_not_ready_handler_thread = threading.Thread(target=modem_not_ready_handler,
                    daemon=True)

            modem_not_ready_handler_thread.start()


    def check_available_messages(self) -> None:
        """
        """
        logging.debug("checking for available messages")
        try:
            available_messages = self.messaging.List()
            logging.debug("# Available received messages - [%d]", len(available_messages))

            for message_path in available_messages:
                message = Messaging(self.bus, message_path, self)

                if message.__is_received_message__():
                    self.__broadcast_new_message__(message)

                elif message.__is_receiving_message__():
                    logging.debug("\n\treceiving: %s", message.new_received_message())

        except Exception as error:
            raise error

    def check_modem_is_ready(self) -> None:
        """
        """
        logging.debug("checking if modem is ready")
        try:
            if self.is_ready():
                self.__broadcast_ready_modem__()
        except Exception as error:
            raise error


    def __waited_completed__(self, message: Messaging) -> None:
        """
        """
        self.__broadcast_new_message__(message)


    def __message_property_changed_added__(self, *args, **kwargs) -> None:
        """
        """
        message_path = args[0]
        logging.debug("message property changed: %s", message_path)

        message = Messaging(self.bus, message_path, self)

        if message.__is_received_message__():
            self.__broadcast_new_message__(message)

        elif message.__is_receiving_message__():
            logging.debug("\n\treceiving: %s", message.new_received_message())


    def is_ready(self) -> bool:
        """
        """

        """
        https://www.freedesktop.org/software/ModemManager/api/latest/ModemManager-Flags-and-Enumerations.html#MMModem3gppRegistrationState
        """

        print(self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState")))
        return (self.get_3gpp_property("OperatorCode") != ''
                and 
                (self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_HOME
                or
                self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING
                or
                self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_HOME_SMS_ONLY
                or
                self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING_SMS_ONLY
                or
                self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN
                or
                self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState"))
                == 
                self.MMModem3gppRegistrationState.MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING_SMS_ONLY))

    

    def add_new_message_handler(self, new_received_message_handler) -> None:
        """
        """
        self.__new_received_message_handlers__.append(new_received_message_handler)


    def add_modem_is_ready_handler(self, modem_connected_handler) -> None:
        """
        """
        self.__modem_is_ready_handlers__.append(modem_connected_handler)

    def add_modem_is_not_ready_handler(self, modem_connected_handler) -> None:
        """
        """
        self.__modem_is_not_ready_handlers__.append(modem_connected_handler)

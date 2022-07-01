
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


    def __init__(self, bus, message_path, *args) -> None:
        """
        """
        self.message_path = message_path
        self.bus = bus

        self.modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'
        self.modem_dbus_sms_iface = "org.freedesktop.ModemManager1.Sms"

        dbus_message = bus.get_object(self.dbus_name, self.message_path, True)


        self.props = dbus.Interface(
                dbus_message, dbus_interface=self.modem_dbus_props_iface)

        self.sms = dbus.Interface(
                dbus_message, dbus_interface=self.modem_dbus_sms_iface)


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


    def get_property(self, property_name):
        """
        """
        try:
            return self.props.Get(self.modem_dbus_sms_iface, property_name)
        except Exception as error:
            raise error



class Modem(threading.Event):
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

        self.__new_received_message_handlers__ = []

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

        if 'OperatorCode' in change_props and change_props['OperatorCode'] != '':
            operator_code = change_props['OperatorCode']

            logging.debug("%s: changed operator code: %s", 
                    member, operator_code)

            """
            !Important note:

            - For richer data quality could use RegistrationState signals.
            This could inform about the network state and delivery efficiency.

            - Changes to registration state can be referenced from here.
            https://www.freedesktop.org/software/ModemManager/api/latest/ModemManager-Flags-and-Enumerations.html#MMModem3gppRegistrationState
            """

            try:
                self.check_available_messages()
            except Exception as error:
                logging.exception(error)

        if 'RegistrationState' in change_props:
            registration_state = \
                    self.MMModem3gppRegistrationState(change_props['RegistrationState'])
            logging.info("%s changed registration state: %s", 
                    member, registration_state)



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


    def __broadcast_new_message__(self, message: Messaging) -> None:
        """
        """
        for message_handler in self.__new_received_message_handlers__:
            message_handler_thread = threading.Thread(target=message_handler,
                    args=(message,), daemon=True)

            message_handler_thread.start()


    def check_available_messages(self) -> None:
        """
        """
        logging.debug("checking for available messages")
        try:
            available_messages = self.messaging.List()
            logging.debug("# Available messages - [%d]", len(available_messages))

            for message_path in available_messages:
                message = Messaging(self.bus, message_path)
                if message.__is_received_message__():
                    self.__broadcast_new_message__(message)
                    # self.messaging.Delete(message_path)
                    # logging.warning("Deleted message: %s", message_path)
        except Exception as error:
            raise error


    def __message_property_changed_added__(self, *args, **kwargs) -> None:
        """
        """
        message_path = args[0]
        logging.debug("message property changed: %s", message_path)

        message = Messaging(self.bus, message_path)
        if message.__is_received_message__():
            self.__broadcast_new_message__(message)
            """
            self.messaging.Delete(message_path)
            logging.warning("Deleted message: %s", message_path)
            """

    def is_ready(self) -> bool:
        """
        """
        return self.get_3gpp_property("OperatorCode") != ""
    
    def add_new_message_handler(self, new_received_message_handler) -> None:
        """
        """
        self.__new_received_message_handlers__.append(new_received_message_handler)

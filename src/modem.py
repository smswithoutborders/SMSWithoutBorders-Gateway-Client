
import threading
import dbus
from enum import Enum
import logging

from messaging import Messaging

dbus_name = 'org.freedesktop.ModemManager1'
modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'

class Modem:
    """
    """
    modem_3gpp_interface = 'org.freedesktop.ModemManager1.Modem.Modem3gpp'
    modem_modem_interface = 'org.freedesktop.ModemManager1.Modem'

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
        logging.debug("initialized new modem instance: %s", self)

        self.bus = bus
        self.modem_path = modem_path
        self.dbus_modem = bus.get_object(dbus_name, self.modem_path, True)

        self.connected = True

        self.props = dbus.Interface(self.dbus_modem, dbus_interface=modem_dbus_props_iface)
        self.props.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__modem_property_changed__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')

        self.modem = dbus.Interface(self.dbus_modem, dbus_interface=self.modem_modem_interface)

        self.__new_received_message_handlers__ = []
        self.__modem_is_ready_handlers__ = []
        self.__modem_is_not_ready_handlers__ = []

        self.messaging = Messaging(modem=self)

    
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


        logging.debug("Modem property changed - %s", args)

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
            self.__broadcast_not_ready_modem__()
            self.connected = False

        except Exception as error:
            logging.exception(error)



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



    def check_modem_is_ready(self) -> None:
        """
        """
        logging.debug("checking if modem is ready")
        try:
            if self.is_ready():
                self.__broadcast_ready_modem__()
        except Exception as error:
            raise error


    def is_ready(self) -> bool:
        """
        """

        """
        https://www.freedesktop.org/software/ModemManager/api/latest/ModemManager-Flags-and-Enumerations.html#MMModem3gppRegistrationState
        """

        # print(self.MMModem3gppRegistrationState(self.get_3gpp_property("RegistrationState")))
        """
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
        """
        return self.get_3gpp_property("OperatorCode") != ''

    
    def add_modem_is_ready_handler(self, modem_connected_handler) -> None:
        """
        """
        self.__modem_is_ready_handlers__.append(modem_connected_handler)

    def add_modem_is_not_ready_handler(self, modem_connected_handler) -> None:
        """
        """
        self.__modem_is_not_ready_handlers__.append(modem_connected_handler)

    def enable(self) -> None:
        """
        """
        self.modem.Enable(True)


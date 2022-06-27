
import threading
import dbus
from enum import Enum
import logging

class Modem(threading.Event):
    """
    """
    dbus_name = 'org.freedesktop.ModemManager1'

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

        modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'

        self.modem_path = modem_path

        dbus_modem = bus.get_object(self.dbus_name, self.modem_path, True)

        self.props = dbus.Interface(dbus_modem, dbus_interface=modem_dbus_props_iface)

        self.props.connect_to_signal(
                "PropertiesChanged",
                handler_function=self.__modem_property_changed__,
                path_keyword='path', 
                member_keyword='member', 
                interface_keyword='interface', 
                destination_keyword='destination',
                sender_keyword='sender')


    def __modem_property_changed__(self, *args, **kwargs) -> None:
        """
        """
        member = args[0]
        change_props = args[1]


        logging.debug("Modem property changed - %s", member)

        if 'OperatorCode' in change_props:
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

            if 'RegistrationState' in change_props:
                registration_state = \
                        self.MMModem3gppRegistrationState(change_props['RegistrationState'])
                logging.info("%s changed registration state: %s", 
                        member, registration_state)


    def get_properties(self) -> dict:
        """
        """
        modem_interface = 'org.freedesktop.ModemManager1.Modem.Modem3gpp'
        return self.props.GetAll(modem_interface)



    def get_property(self, key: str):
        """
        """
        return self.props.Get(modem_interface, key)

    def remove(self):
        """
        TODO: kill all infinite loops from here by changing their threads to set()
        - https://docs.python.org/3/library/threading.html#threading.Condition.wait_for
        """

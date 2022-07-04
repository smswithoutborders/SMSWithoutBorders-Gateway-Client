import threading
import dbus
from enum import Enum
import logging

dbus_name = 'org.freedesktop.ModemManager1'
modem_dbus_props_iface = 'org.freedesktop.DBus.Properties'

class SMS:

    class MMSmsDeliveryState(Enum):
        MM_SMS_DELIVERY_STATE_COMPLETED_RECEIVED              = 0x00
        MM_SMS_DELIVERY_STATE_COMPLETED_FORWARDED_UNCONFIRMED = 0x01
        MM_SMS_DELIVERY_STATE_COMPLETED_REPLACED_BY_SC        = 0x02

        # Temporary failures */
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_CONGESTION           = 0x20
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_SME_BUSY             = 0x21
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_NO_RESPONSE_FROM_SME = 0x22
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_SERVICE_REJECTED     = 0x23
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_QOS_NOT_AVAILABLE    = 0x24
        MM_SMS_DELIVERY_STATE_TEMPORARY_ERROR_IN_SME               = 0x25

        # Permanent failures */
        MM_SMS_DELIVERY_STATE_ERROR_REMOTE_PROCEDURE             = 0x40
        MM_SMS_DELIVERY_STATE_ERROR_INCOMPATIBLE_DESTINATION     = 0x41
        MM_SMS_DELIVERY_STATE_ERROR_CONNECTION_REJECTED          = 0x42
        MM_SMS_DELIVERY_STATE_ERROR_NOT_OBTAINABLE               = 0x43
        MM_SMS_DELIVERY_STATE_ERROR_QOS_NOT_AVAILABLE            = 0x44
        MM_SMS_DELIVERY_STATE_ERROR_NO_INTERWORKING_AVAILABLE    = 0x45
        MM_SMS_DELIVERY_STATE_ERROR_VALIDITY_PERIOD_EXPIRED      = 0x46
        MM_SMS_DELIVERY_STATE_ERROR_DELETED_BY_ORIGINATING_SME   = 0x47
        MM_SMS_DELIVERY_STATE_ERROR_DELETED_BY_SC_ADMINISTRATION = 0x48
        MM_SMS_DELIVERY_STATE_ERROR_MESSAGE_DOES_NOT_EXIST       = 0x49

        # Temporary failures that became permanent */
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_CONGESTION           = 0x60
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_SME_BUSY             = 0x61
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_NO_RESPONSE_FROM_SME = 0x62
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_SERVICE_REJECTED     = 0x63
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_QOS_NOT_AVAILABLE    = 0x64
        MM_SMS_DELIVERY_STATE_TEMPORARY_FATAL_ERROR_IN_SME               = 0x65

        # Unknown out of any possible valid value [0x00-0xFF] */
        MM_SMS_DELIVERY_STATE_UNKNOWN = 0x100

        # --------------- 3GPP2 specific errors ---------------------- */

        # Network problems */
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_ADDRESS_VACANT              = 0x200
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_ADDRESS_TRANSLATION_FAILURE = 0x201
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_NETWORK_RESOURCE_OUTAGE     = 0x202
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_NETWORK_FAILURE             = 0x203
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_INVALID_TELESERVICE_ID      = 0x204
        MM_SMS_DELIVERY_STATE_NETWORK_PROBLEM_OTHER                       = 0x205

        # Terminal problems */
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_NO_PAGE_RESPONSE                      = 0x220
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_DESTINATION_BUSY                      = 0x221
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_NO_ACKNOWLEDGMENT                     = 0x222
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_DESTINATION_RESOURCE_SHORTAGE         = 0x223
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_SMS_DELIVERY_POSTPONED                = 0x224
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_DESTINATION_OUT_OF_SERVICE            = 0x225
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_DESTINATION_NO_LONGER_AT_THIS_ADDRESS = 0x226
        MM_SMS_DELIVERY_STATE_TERMINAL_PROBLEM_OTHER                                 = 0x227

        # Radio problems */
        MM_SMS_DELIVERY_STATE_RADIO_INTERFACE_PROBLEM_RESOURCE_SHORTAGE = 0x240
        MM_SMS_DELIVERY_STATE_RADIO_INTERFACE_PROBLEM_INCOMPATIBILITY   = 0x241
        MM_SMS_DELIVERY_STATE_RADIO_INTERFACE_PROBLEM_OTHER             = 0x242

        # General problems */
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_ENCODING                            = 0x260
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_SMS_ORIGINATION_DENIED              = 0x261
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_SMS_TERMINATION_DENIED              = 0x262
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_SUPPLEMENTARY_SERVICE_NOT_SUPPORTED = 0x263
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_SMS_NOT_SUPPORTED                   = 0x264
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_MISSING_EXPECTED_PARAMETER          = 0x266
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_MISSING_MANDATORY_PARAMETER         = 0x267
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_UNRECOGNIZED_PARAMETER_VALUE        = 0x268
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_UNEXPECTED_PARAMETER_VALUE          = 0x269
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_USER_DATA_SIZE_ERROR                = 0x26A
        MM_SMS_DELIVERY_STATE_GENERAL_PROBLEM_OTHER                               = 0x26B

        # Temporary network problems */
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_ADDRESS_VACANT              = 0x300
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_ADDRESS_TRANSLATION_FAILURE = 0x301
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_NETWORK_RESOURCE_OUTAGE     = 0x302
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_NETWORK_FAILURE             = 0x303
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_INVALID_TELESERVICE_ID      = 0x304
        MM_SMS_DELIVERY_STATE_TEMPORARY_NETWORK_PROBLEM_OTHER                       = 0x305

        # Temporary terminal problems */
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_NO_PAGE_RESPONSE                      = 0x320
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_DESTINATION_BUSY                      = 0x321
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_NO_ACKNOWLEDGMENT                     = 0x322
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_DESTINATION_RESOURCE_SHORTAGE         = 0x323
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_SMS_DELIVERY_POSTPONED                = 0x324
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_DESTINATION_OUT_OF_SERVICE            = 0x325
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_DESTINATION_NO_LONGER_AT_THIS_ADDRESS = 0x326
        MM_SMS_DELIVERY_STATE_TEMPORARY_TERMINAL_PROBLEM_OTHER                                 = 0x327

        # Temporary radio problems */
        MM_SMS_DELIVERY_STATE_TEMPORARY_RADIO_INTERFACE_PROBLEM_RESOURCE_SHORTAGE = 0x340
        MM_SMS_DELIVERY_STATE_TEMPORARY_RADIO_INTERFACE_PROBLEM_INCOMPATIBILITY   = 0x341
        MM_SMS_DELIVERY_STATE_TEMPORARY_RADIO_INTERFACE_PROBLEM_OTHER             = 0x342

        # Temporary general problems */
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_ENCODING                            = 0x360
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_SMS_ORIGINATION_DENIED              = 0x361
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_SMS_TERMINATION_DENIED              = 0x362
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_SUPPLEMENTARY_SERVICE_NOT_SUPPORTED = 0x363
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_SMS_NOT_SUPPORTED                   = 0x364
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_MISSING_EXPECTED_PARAMETER          = 0x366
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_MISSING_MANDATORY_PARAMETER         = 0x367
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_UNRECOGNIZED_PARAMETER_VALUE        = 0x368
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_UNEXPECTED_PARAMETER_VALUE          = 0x369
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_USER_DATA_SIZE_ERROR                = 0x36A
        MM_SMS_DELIVERY_STATE_TEMPORARY_GENERAL_PROBLEM_OTHER                               = 0x36B

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

        if ('State' in change_props
                and 
                self.MMSmsState(change_props['State']) == self.MMSmsState.MM_SMS_STATE_SENT):
            logging.debug("Delivery state: %s",
                    self.MMSmsDeliveryState(self.get_property("DeliveryState")))

        if 'DeliveryState' in change_props:
            logging.debug("Changed in delivery: %s", args)

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


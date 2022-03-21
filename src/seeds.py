#!/usr/bin/env python3

import base64
import json

from ledger import Ledger

class Seeds(Ledger):

    def __init__(self, IMSI: str, seeder: bool=False):
        super().__init__(IMSI=IMSI)
        self.IMSI = IMSI
        self.seeder = seeder

    def is_seed(self) -> bool:
        """Checks if current node can seed.
        In other to seed, an MSISDN and IMSI should be present in local db.
        """
        result = self.find(["MSISDN", "IMSI"])
        if len(result) > 0:
            return True

        return False
        

    def is_seeder_message(self, data: base64) -> bool:
        """Checks if message is in format required for seeder update.
        """
        try:
            data = base64.b64decode(data)
        except Exception as error:
            raise error
        else:
            try:
                data = json.loads(data)
            except Exception as error:
                raise error
            else:
                if not "MSISDN" in data:
                    return False
                else:
                    # TODO check if valid MSISDN
                    return True

    def is_seed_message(self):
        return False

    def process_seed_message(self):
        return False

    def is_seeder(self) -> bool:
        """Checks if the current node can act as seeder.
        In other to be a seeder, seeder needs to be True in config and needs to be seed.
        """
        try:
            return self.seeder and self.is_seed()
        except Exception as error:
            raise error

    def ping(self):
        return False

    def make_seed(self, MSISDN: str):
        """Updates the ledger record for current IMSI with MSISDN.
        """

    def remote_seed(self):
        """Deletes the seed record for node.
        """

    def is_ledger_request(self, data:dict) -> bool:
        """Validates incoming SMS is a valid ledger response.

        Checks the data for the following:
            1. Number:
                Checks if number is a valid Gateway Seeder number - seeder list
            2. Text:
                Checks the body of the text if:
                    1. Is base64 encoded.
                    2. Is JSON.
                    3. Contains MSISDN.
                    4. Is valid MSISDN.
                    5. MSISIDN country matches country of SIM Operator CODE (MCCMNC).
        This creates the ledger record and number acquisition is complete.
        """

        try:
            if not self.__is_seeder__(data['MSISDN']):
                logging.debug("Not a seeder MSISDN %s", data["MSISDN"])
                return False

            try:
                # 1. 
                text = base64.b64decode(data['text'])
            except Exception as error:
                # logging.exception(error)
                logging.debug("Not a valid base64 text %s", data['text'])
                # raise error
                return False

            else:
                try:
                    # 2.
                    text = json.loads(text)
                except Exception as error:
                    logging.exception(error)
                    logging.debug("Not a valid json object")
                    raise error

                else:
                    # 3.
                    if not 'MSISDN' in text:
                        logging.debug("does not contain MSISDN")
                        return False
                    else:
                        # 4.
                        try:
                            MSISDN_country, _ = Deku.validate_MSISDN(MSISDN=text['MSISDN'])
                        except Deku.InvalidNumber as error:
                            logging.debug("Is not a valid MSISDN")
                            raise error

                        except Deku.BadFormNumber as error:
                            """
                            TODO: 
                                This error comes with 2 types (src/deku.py)
                            """
                            raise error

                        except Exception as error:
                            raise error

                        else:
                            # 5.
                            MCCMNC_country = Deku.get_modem_operator_country(self.modem)

                            if not MSISDN_country == MCCMNC_country:
                                logging.debug("MSISDN country does not match MCCMNC country")
                                return False

                            else:
                                logging.info("Valid ledger request: %s", data)
                                return True

        except Exception as error:
            raise error

        return False



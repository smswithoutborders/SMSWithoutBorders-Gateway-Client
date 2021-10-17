#!/usr/bin/env python3


''' this comes in handy for managing many other forms of request '''

''' list of events which can happen for Deku '''
'''
status updaters---
- SMS Fails to send  - Failed++
- SMS sent successfully - Sent++

list of events---

'''

class Events:
    class Category(Enum):
        ''' perhaps could be read from a file '''
        BENCHMARK='BENCHMARK'

    class States(Enum):
        FAILED=0
        SUCCESS=1
        UNKNOWN=2

    def __init__(self):
        pass

    @classmethod
    def check_event(cls, node, category:Category, state:States):
        print("Event fired!")
        # DekuControlBot.send_message("Event fired!")
        """
        node_status=node.fetch_status()
        node_value=int(node_status[state][category])

        # rules['SUCCESS']['EQUALS']['BENCHMARK']
        # rules[state][operand][category]
        '''would iterate through all the states and fire all states that pass '''
        for operand in rules[state]:
            rules_value=rules[state][operand][category]
            if operand == 'EQUALS':
                if rules_value != -1 and rules_value == node_value:
                    print(f'\nFiring event - state={state}, operand={operand}, category={category}')
            """


#!/usr/bin/env python3

import configparser,os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

'''
post - /sms
[{
text: "",
number: "",
isp: "",
}...]
--- returns
* HTTP status code

# Get ISP for numbers based on their ISP
get - /isp
?number= # E.164 standard (country code required) https://en.wikipedia.org/wiki/E.164
--- returns
* HTTP status code
* {
isp: ""
}

post - /isp
[{
number: = # E.164 standard (country code required) https://en.wikipedia.org/wiki/E.164
}...]
--- returns
* HTTP status code
* [{
number: "", 
isp: ""
}]
'''

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), '../configs', 'config.ini'))
connection = pika.BlockingConnection( pika.ConnectionParameters(host=config['NODE']['connection_url']))
channel = connection.channel()

def rabbit_new_sms_request(auth_id, auth_key, data):


    # queue_name = config_queue_name + _ + isp
    for _data in data:
        # queue_name = config['NODE']['outgoing_queue_name'] + '_' + _data['isp']
        routing_key = auth_id + '_' + config['NODE']['outgoing_queue_name'] + '.' + _data['isp']
        
        ''' creates the exchange '''
        '''
        channel.exchange_declare( 
                exchange=config['NODE']['outgoing_exchange_name'], exchange_type=config['NODE']['outgoing_exchange_type'])
        '''

        text = _data['text']
        number = _data['number']
        data = json.dumps({"text":text, "number":number})

        channel.basic_publish(
            exchange=config['NODE']['outgoing_exchange_name'],
            # routing_key=queue_name.replace('_', '.'),
            routing_key=routing_key,
            body=data,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        # print(" [x] Sent %r" % message)
        print(f"[x] text; {text} ::\n\tsent to {number}")
        connection.close()


@app.route('/sms', methods=['POST'])
def send_sms():
    request_body=None
    try:
        request_body = request.json
    except Exception as error:
        ''' something is wrong with the json '''
        ''' should be logged '''
        return "invalid json", 400


    ''' auth_id and auth_key should be authenticated here '''
    ''' still unsure if to use tokens or actual keys (if used internally and not exposed, key doesn't matter '''
    if not "auth_id" in request:
        request_body["error_requests"] = 'auth ID missing'
        return jsonify(request_body), 400
    if not "auth_key" in request:
        request_body["error_requests"] = 'auth Key missing'
        return jsonify(request_body), 400


    for i in len(range(request_body)):
        request_body[i]["error_requests"]=[]
        if not "text" in request:
            request_body[i]["error_requests"].append('text missing')
        if not "number" in request:
            request_body[i]["error_requests"].append('number missing')
        if not "isp" in request:
            request_body[i]["error_requests"].append('isp missing')

        if len(request_body[i]["error_requests"]) < 1:
            rabbit_new_sms_request(auth_id=auth_id, auth_key=auth_key, data=request)

    return jsonify(request_body), 200


@app.route('/isp', methods=['POST', 'GET'])
def get_isp():
    def deduce_isp(number): # E.164 standard required
        import re
        ''' operator files
        configs/isp/default.ini
        -> this is server code, so host should handle fitting in what they need
        -> deduction based on default file, not all the file, it either knows it or it doesn't
        '''

        _config = _configparser.ConfigParser()
        _config.read(os.path.join(os.path.dirname(__file__), 'configs/isp', 'default.ini'))

        country=None
        country_code=None
        cc = _config['country_codes']
        for cntry, code in cc.items():
            if re.search(f'^\{code}', number):
                country = cntry
                country_code=code

        if country is None:
            return None

        # TODO put something here in case the country does not have operator ids in the config file
        operator_stds= _config[country]
        for isp, stds in operator_stds.items():
            stds = stds.split(',')

            for std in stds:
                #removing country code from number
                number = number.replace(country_code, '')
                if re.search(std, number):
                    return isp

        return None

    if request.method == 'POST':
        request_body = request.json
        for i in range(len(request_body)):
            _request = request_body[i]
            isp = deduce_isp(_request['number'])
            if isp is None:
                request_body[i]['isp'] = 'INVALID'
            else:
                request_body[i]['isp'] = isp
        return jsonify(request_body), 200
    
    request_body = request.args
    number = request_body.get('number')
    # print(number)
    if number is None:
        return 'missing number', 400

    if number[0] =='0' or number[0] != '+':
        # this is so fucked
        number = list(number)
        number[0] = '+'
        number=''.join(number)

    isp = deduce_isp(number)
    if isp is None:
        return 'INVALID', 200
    else:
        return isp, 200


if __name__ == "__main__":
    app.run(host='localhost', port='15673', debug=True, threaded=True )

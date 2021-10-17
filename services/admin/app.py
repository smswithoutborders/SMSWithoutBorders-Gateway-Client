#!/usr/bin/env python3

import pika
import configparser, os, json
import re
import requests
import traceback

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

'''
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(os.path.join(os.path.dirname(__file__), 'configs', 'config.ini'))
'''
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
cofing.read(os.path.join(os.path.dirname(__file__), '', 'config.ini'))


def authenticate(user_id, auth_id, auth_key, project_id, scope=['read']):
    # results = requests.post(url=config['AUTH']['url'], json={"auth_id":auth_id, "auth_key":auth_key})
    url=f'http://localhost:9000/auth/users/{user_id}'


    admin_auth_id=config['ADMIN']['auth_id']
    admin_auth_key=config['ADMIN']['auth_key']

    ''' should be user creds - wait for Promise's fix of the API ''' 
    results = requests.post(url=url, json={"auth_id":auth_id, "auth_key":auth_key})
    print(">> results.json()", results.json())

    if results.status_code == 200 and results.json() == True:
        url=f'http://localhost:9000/auth/users/{user_id}/projects/{project_id}'
        ''' auth details here belong to admin '''

        results = requests.post(url=url, json={"auth_id":admin_auth_id, "auth_key":admin_auth_key, "scope":scope})
        print(results.text)
        return results.status_code == 200 and results.json() == True
    else:
        return False
    return None

def rabbit_new_sms_request(auth_id, auth_key, data):
    ''' is this wasted and just computational heavy? '''
    connection = pika.BlockingConnection( pika.ConnectionParameters(host=config['RABBITMQ']['connection_url']))
    channel = connection.channel()

    ''' creates the exchange '''
    channel.exchange_declare( 
            exchange=config['RABBITMQ']['outgoing_exchange_name'], 
            exchange_type=config['RABBITMQ']['outgoing_exchange_type'], 
            durable=True)

    # queue_name = config_queue_name + _ + isp
    for _data in data:
        queue_name = auth_id + '_' + config['RABBITMQ']['outgoing_queue_name'] + '_' + _data['isp']
        routing_key = auth_id + '_' + config['RABBITMQ']['outgoing_queue_name'] + '.' + _data['isp']
        
        ''' creates the queue, due to not knowing the isp this compute is wasted'''
        # channel.queue_declare(queue_name, durable=True)

        text = _data['text']
        number = _data['number']
        _data = json.dumps({"text":text, "number":number})

        channel.basic_publish(
            exchange=config['RABBITMQ']['outgoing_exchange_name'],
            # routing_key=queue_name.replace('_', '.'),
            routing_key=routing_key,
            body=_data,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        # print(" [x] Sent %r" % message)
        print(f"[x] text; {text} ::\n\tsent to {number}")
        # connection.close()


@app.route('/sms', methods=['POST'])
def send_sms():
    ''' input keys - 
    auth_id
    auth_key
    project_id
    data
       isp
       text
       number
    '''
    request_body=None
    try:
        request_body = request.json
    except Exception as error:
        ''' something is wrong with the json '''
        ''' should be logged '''
        return "invalid json", 400


    ''' auth_id and auth_key should be authenticated here '''
    ''' still unsure if to use tokens or actual keys (if used internally and not exposed, key doesn't matter '''
    if not "auth_id" in request_body:
        # request_body["error_requests"] = 'auth ID missing'
        return 'auth ID missing', 400
    if not "auth_key" in request_body:
        # request_body["error_requests"] = 'auth Key missing'
        return 'auth Key missing', 400
    if not "project_id" in request_body:
        # request_body["error_requests"] = 'auth Key missing'
        return 'project ID missing', 400
    if not "data" in request_body:
        # request_body["error_requests"] = 'auth Key missing'
        return 'data missing', 400
    
    user_id=request_body['user_id']
    auth_id=request_body['auth_id']
    auth_key=request_body['auth_key']
    project_id=request_body['project_id']
    # TODO: authenticate(auth_id, auth_key)
    # TODO: authenticate(auth_id, auth_key, scope)
    results = authenticate(user_id, auth_id, auth_key, project_id)

    if not results or results is None:
        return jsonify({"results":results, "message":"failed to authenticate..."}), 403

    def valid_number(number):
        reg="\+[0-9]*"
        return re.search(reg, number)

    for i in range(len(request_body['data'])):
        ''' each request can have multiple errors involved, keep note of that '''
        request_body['data'][i]["error_requests"]=[]
        if not "text" in request_body['data'][i]:
            request_body['data'][i]["error_requests"].append('text missing')
        if not "number" in request_body['data'][i]:
            request_body['data'][i]["error_requests"].append('number missing')
        if not "isp" in request_body['data'][i]:
            request_body['data'][i]["error_requests"].append('isp missing')

        if len(request_body['data'][i]["error_requests"]) < 1:
            '''authenticate for valid phonenumber '''
            try:
                if not valid_number(request_body['data'][i]['number']):
                    request_body['data'][i]["error_requests"].append('invalid number')
                    continue
                rabbit_new_sms_request(auth_id=auth_id, auth_key=auth_key, data=request_body['data'])
            except Exception as error:
                print(traceback.format_exc())

    return jsonify(request_body), 200


@app.route('/isp', methods=['POST', 'GET'])
def get_isp():
    def deduce_isp(number): # E.164 standard required
        ''' operator files
        configs/isp/default.ini
        -> this is server code, so host should handle fitting in what they need
        -> deduction based on default file, not all the file, it either knows it or it doesn't
        '''

        _config = configparser.ConfigParser()
        _config.read(os.path.join(os.path.dirname(__file__), '../configs/isp', 'default.ini'))

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
    # app.run(host='localhost', port='15673', debug=True, threaded=True )
    app.run(host='localhost', port='15673', debug=True, threaded=True )
    # app.run(host='localhost', port='15673', debug=False)

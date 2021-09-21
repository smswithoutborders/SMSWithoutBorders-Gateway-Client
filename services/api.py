#!/usr/bin/env python3


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

def rabbit_new_request(auth_id, auth_key, data):
    pass


@app.route('/sms', methods=['POST'])
def send_sms():
    request_body=None
    try:
        request_body = request.json
    except Exception as error:
        ''' something is wrong with the json '''
        ''' should be logged '''
        return "invalid json", 400


    error_requests=[]
    for request in request_body:
        if not "text" in request:
            pass
        if not "number" in request:
            pass
        if not "isp" in request:
            pass

        rabbit_new_request(auth_id=auth_id, auth_key=auth_key, data=request)

    return jsonify({"error requests":error_requests}), 200


@app.route('/isp', methods=['POST', 'GET'])
def get_isp():
    '''
    if request.method == 'POST':
    '''
    pass


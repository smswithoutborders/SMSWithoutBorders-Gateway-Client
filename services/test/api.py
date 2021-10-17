#!/usr/bin/env python3


import requests


if __name__ == "__main__":
    url='http://localhost:15673'
    # testing ISP deduction - using Cameroon values
    data = [
            {"text":"Hello world - MTN", "number":"+2376521", "expected": "MTN"},
            {"text":"Hello world - ORANGE", "number":"+2376921", "expected": "ORANGE"},
            {"text":"Hello world - INVALID", "number":"+2370921", "expected": "INVALID"}
            ]
    print("* Running on url -", url)
    print("* Deducing ISP...")

    results = requests.post(url=url + '/isp', json=data)
    if results.status_code != 200:
        print("* [error] request failed...", results, results.status_code)
        return False

    # print(results)
    for _data in results:
        if not "text" or not "number" or not "isp" in _data:
            print("* [error] missing key...\n", _data)
            return False
        if _data['expected'] != _data['isp']:
            print("* [error] isp does not match...\n", _data)
        else:
            print("* [error] isp matches...\n", _data)

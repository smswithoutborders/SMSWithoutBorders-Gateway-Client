##### Begin by configuring databases
###### MySQL
- Copy the _example.config.ini_ file into _config.ini_ in the same dir
>> libs/example.config.ini
##### How to Run

###### Create venv
```bash
python3 -m virtualenv .venv
```

###### Activate venv
```bash
source . venv/bin/activate
```

###### Install requirements
```bash
pip install -r requirements.txt
```

###### Start the API
```bash
cd src/
python api.py
```

###### Run send SMS Messages 
```bash
cd src/
python daemon.py
```

###### Run read received Messages 
```bash
cd src/
python daemon_received.py
```

##### How to test

###### Send SMS
```bash
./test_script.sh --send <receiving phonenumber>
# example: ./test_script.sh --send 00000000
```
###### See all received SMS messages
```bash
./test_script.sh --received
```

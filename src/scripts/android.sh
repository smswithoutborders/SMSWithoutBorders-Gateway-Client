#!/bin/bash

# https://gist.github.com/Pulimet/5013acf2cd5b28e55036c82c91bd56d8

# Start a call
adb shell am start -a android.intent.action.CALL -d tel:+1-xxx-xxx-xxxx

# End a call
adb shell input keyevent 6

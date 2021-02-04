#!/bin/bash


# Start a call
adb shell am start -a android.intent.action.CALL -d tel:+1-xxx-xxx-xxxx

# End a call
adb shell input keyevent 6

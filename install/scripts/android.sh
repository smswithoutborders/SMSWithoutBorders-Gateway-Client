#!/bin/bash

# https://gist.github.com/Pulimet/5013acf2cd5b28e55036c82c91bd56d8

# Start a call
adb shell am start -a android.intent.action.CALL -d tel:+1-xxx-xxx-xxxx

# End a call
adb shell input keyevent 6

# Send SMS messages
adb shell service call isms 7 i32 0 s16 "com.android.mms.service" s16 "+1234567890" s16 "null" s16 "'Hey you !'" s16 "null" s16 "null"

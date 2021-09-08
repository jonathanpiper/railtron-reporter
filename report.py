import paho.mqtt.client as mqtt
import json
import socket
import qwiic_bme280
import time
import sys
import usb.core
import signal
from time import sleep
import myriad_class
from sty import fg, bg, ef, rs

hostname = socket.gethostname()
version = "0.1.1"
print(ef.b + "Railtron Reporter " + version + " running on " + hostname + rs.ef)


def signal_handler(signal, frame):
    print('Keyboard interrupt!')
    # usb.util.dispose_resources(dev)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

myriadAmp = myriad_class.MyriadAmpConnection()

# We need the hostname to make the code as portable as possible!


# Just in case this needs to change at some point.
topic_general = 'sensorio'
topic_requests = topic_general + "/requests"
topic_specific = topic_general + "/" + hostname

bme280 = qwiic_bme280.QwiicBme280()

if bme280.connected == False:
    print("The Qwiic BME280 device isn't connected to the system. Please check your connection",
          file=sys.stderr)

bme280.begin()

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected to Railtron MQTT broker with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic_requests)

# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    msgJSON = json.loads(msg.payload)
    if list(msgJSON)[0] == 'targetSensor' and (msgJSON['targetSensor'] == 'all' or msgJSON['targetSensor'] == hostname):
        print('Railtron is asking ' +
              ef.b + msgJSON['targetSensor'] + rs.ef + ' for ' + ef.b + msgJSON['requestData'] + rs.ef + ' with scope ' + ef.b + msgJSON['requestScope'] + rs.ef)
        payload = '{'
        if msgJSON['requestData'] == 'all':
            temperature = round(bme280.temperature_fahrenheit, 3)
            humidity = round(bme280.humidity, 3)
            try:
                myriadAmp.get_current_ambientDB()
            except:
                print("Unable to retrieve ambient dB from Myriad amplifier.")
            try:
                myriadAmp.get_current_myriad_settings()
            except:
                print("Unable to retrieve settings from Myriad amplifier.")
            print('Temperature: ' + fg.li_red + str(temperature) + fg.rs + ' | ' + 'Humidity: ' +
                  fg.li_blue + str(humidity) + fg.rs + ' | ' + 'Ambient dB: ' + fg.li_green + str(myriadAmp.myriad_settings.get('current_ambient_db', '0')) + fg.rs)
            payload += '"sensor":"' + hostname + '","temperature":' + str(temperature) + ',"humidity":' + str(
                humidity) + ',"ambientDB":' + str(myriadAmp.myriad_settings.get('current_ambient_db', '0')) + ',"volumeOffset":' + myriadAmp.myriad_settings.get('vol_offset', '0')
        elif msgJSON['requestData'] == 'myriadState':
            try:
                myriadAmp.get_current_myriad_settings()
            except:
                print("Unable to retrieve settings from Myriad amplifier.")
            payload += '"sensor":"'+hostname+'","volumeOffset":"' + \
                myriadAmp.myriad_settings.get('vol_offset', '0')+'"'
        elif msgJSON['requestData'] == 'adjustVolumeOffset':
            try:
                myriadAmp.update_myriad_volume_offset(msgJSON['parameter'])
            except:
                print("Unable to adjust Myriad amplifier volume.")
            payload += '"sensor":"'+hostname+'","volumeOffset":"' + \
                myriadAmp.myriad_settings.get('vol_offset', '0')+'"'
        payload += ',"requestScope":"'+msgJSON['requestScope']+'"}'
        print('Publishing message for Railtron:\n', payload)
        client.publish(topic_general, payload)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("railhub.local", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

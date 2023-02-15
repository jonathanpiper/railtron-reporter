#!/home/railreporter/railtronreport/bin/python

import paho.mqtt.client as mqtt
import json
import socket
import qwiic_bme280
import sys
import signal

hostname = socket.gethostname()
version = "0.1.1"
print("Railtron Reporter " + version + " running on " + hostname)


def signal_handler(signal, frame):
    print("Keyboard interrupt!")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Just in case this needs to change at some point.
topic_general = "sensorio"
topic_requests = topic_general + "/requests"
topic_specific = topic_general + "/" + hostname

bme280 = qwiic_bme280.QwiicBme280()

if bme280.connected == False:
    print(
        "The Qwiic BME280 device isn't connected to the system. Please check your connection",
        file=sys.stderr,
    )

bme280.begin()

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected to Railtron MQTT broker with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic_requests)


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    msgJSON = json.loads(msg.payload)
    if list(msgJSON)[0] == "targetSensor" and (
        msgJSON["targetSensor"] == "all" or msgJSON["targetSensor"] == hostname
    ):
        print(
            "Railtron is asking "
            + msgJSON["targetSensor"]
            + " for "
            + msgJSON["requestData"]
            + " with scope "
            + msgJSON["requestScope"]
        )
        payload = "{"
        if msgJSON["requestData"] == "all":
            temperature = round(bme280.temperature_fahrenheit, 3)
            humidity = round(bme280.humidity, 3)
            print(
                "Temperature: "
                + str(temperature)
                + " | "
                + "Humidity: "
                + str(humidity)
            )
            payload += (
                '"sensor":"'
                + hostname
                + '","temperature":'
                + str(temperature)
                + ',"humidity":'
                + str(humidity)
            )
        payload += ',"requestScope":"' + msgJSON["requestScope"] + '"}'
        print("Publishing message for Railtron:\n", payload)
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

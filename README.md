# railtron-reporter
Reporter component for Museum of Making Music "Railtron" climate and audio monitoring service.

This reporter subscribes to a local MQTT broker on the Railtron server then listens for Railtron's requests for data. Based on the contents of the MQTT JSON payload, the reporter queries a connected BME280 temperature/humidity sensor and a Brown Innovations Myriad DSP amplifier. The Myriad can report current ambient volume levels at the speaker, and can receive commands to adjust various amplifier settings.

The intent is to be reasonably agnostic with the reporter's structure such that specific sensors could be swapped without any significant modification.
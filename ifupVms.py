#!/usr/bin/python
import ConfigParser
import sys
import subprocess

def startInterfaces(portNames):
	for port in portNames:
		subprocess.call("ip link set {} up".format(port),shell=True)

if __name__ == '__main__':
	conf = ConfigParser.ConfigParser()
	conf.read(sys.argv[1])
	portNames = conf.get('configure-ovs', 'portNames').split(',')
	startInterfaces(portNames)

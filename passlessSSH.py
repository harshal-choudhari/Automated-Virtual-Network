#!/usr/bin/python

import subprocess
import ConfigParser
import sys
from netaddr import iter_iprange

conf = ConfigParser.ConfigParser()
conf.read(sys.argv[1])
user = conf.get('sshConfig', 'user')
sshFilePath = conf.get('sshConfig', 'sshFilePath')
ipStart = conf.get('sshConfig', 'remoteHostIpRangeStart')
ipEnd = conf.get('sshConfig', 'remoteHostIpRangeEnd')
generator = iter_iprange(ipStart, ipEnd, step=1)
for i in generator:
	subprocess.call("ssh-copy-id -i {} {}@{} >> /dev/null 2>&1".format(sshFilePath, user,i),shell=True)
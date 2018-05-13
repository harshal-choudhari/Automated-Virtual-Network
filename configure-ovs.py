##!/usr/bin/python

import subprocess
import ConfigParser
import sys
import logging
import commands

def getLoggingLevel(level):
    #{'logging.CRITICAL':50, 'logging.ERROR':40, 'logging.WARNING':30, 'logging.INFO':20, 'logging.DEBUG':10}
    #logging level works with int values which are specified above. this function converts user level to actual value of logging.
    return int(conf.get('common-config',level))

def configParserObj(fileName):
	try:
		conf = ConfigParser.ConfigParser()
		conf.read(fileName)
		return conf
	except IOError as exception:
		logging.error(exception)
		sys.exit(1)

def execute(cmd):
	try:
		subprocess.call(cmd,shell=True)
		logging.debug(cmd)
	except Exception  as e:
		logging.error(e)

def getSectionValue(section, option):
    try:
        result = conf.get(section, option)
        logging.debug('reading variable {} with value {} from {} file. status:SUCCESS'.format(option, result, sys.argv[1]))
        return result
    except ConfigParser.NoSectionError as exception:
        logging.debug('tried reading variable {} from {} file. status:FAIL dumping exception log below'.format(option, sys.argv[1]))
        logging.error(exception)
        #if error occurs process can read from default config file
        try:
            defaultConf = ConfigParser.ConfigParser()
            defaultConf.read('default.conf')
            result = defaultConf.get(section, option)
            logging.debug('Due to error reading from default configuration file {}. variable name {} with value {}'.format('default.conf', option, result))
            return result
        except IOError as exception:
            logging.error('Unable to read from default config file')
            sys.exit(1)

def shortdelay():
        subprocess.call("sleep 1s",shell=True)

def executeCmd(cmd):
	for i in cmd:
		try:
			subprocess.call(i,shell=True)
			logging.debug(i)
		except Exception  as e:
			logging.error(e)

def generateSSHKey():
	execute("echo '\n' | ssh-keygen -t rsa -P ''")

def allocateIP():
	offsetVal=(int(commands.getoutput("fdisk -l "+imgFile+" | grep \Linux | grep \* | awk '{print $3}'")))*512
	execute("mount -o loop,offset="+str(offsetVal)+" "+imgFile+" /mnt")
	tmp = "\n#static ip allocation\nauto eth0\niface eth0 inet static\naddress "+ipAddr+"\nnetmask "+netmask+"\n"
	execute("echo {} > {}".format(tmp,'/mnt/etc/network/interfaces'))
	execute("cat ~/.ssh/id_rsa.pub >> /mnt/root/.ssh/known_hosts")
	execute("umount /mnt")

def addBridge():
	execute("ovs-vsctl --may-exist add-br {}".format(bridgeName))
	execute("ifconfig bridge1 {} ".format(bridgeIp))
	execute("ip link set {} up".format(bridgeName))

def addPorts(port):
	execute("ovs-vsctl --may-exist add-port {} {}".format(bridgeName, port))

def configureOvs():
	cmd = []
	cmd.append("echo 'openvswitch' >> /etc/modules")
	#Need to load kernel module to run ovs in kernel. if ovs must run in userspace then use datapath_type=netdev
	cmd.append("modprobe openvswitch >> /dev/null 2>&1")
	#cmd.append("/etc/init.d/openvswitch-switch stop")
	cmd.append("mkdir -p /usr/local/etc/openvswitch")
	cmd.append("mkdir -p /usr/local/var/run/openvswitch")
	cmd.append("ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitch.ovsschema >> /dev/null 2>&1")
	cmd.append("/etc/init.d/openvswitch-switch start >> /dev/null 2>&1")
	cmd.append("sudo ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
     --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
     --private-key=db:Open_vSwitch,SSL,private_key \
     --certificate=Open_vSwitch,SSL,certificate \
     --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert --pidfile --detach >> /dev/null 2>&1")
	cmd.append("ovs-vsctl --no-wait init >> /dev/null 2>&1")
	cmd.append("ovs-vswitchd --pidfile --detach >> /dev/null 2>&1")
	cmd.append("sudo /usr/share/openvswitch/scripts/ovs-ctl start >> /dev/null 2>&1")
	executeCmd(cmd)

def runVms():
	#cmd.append("ovs-vsctl add-port br0 {} >> /dev/null 2>&1".format(portNames[i]))
	#cmd.append("qemu-system-x86_64 -m {} -name {} -net nic,macaddr={} -net tap,ifname={},script={},downscript={} -hda {} &".format(ramSize, hostname, macAddr, vmName, upScript, downScript, imgFile))
	subprocess.Popen("qemu-system-x86_64 -m {} -name {} -net nic,macaddr={} -net tap,ifname={},script=no,downscript=no -device e1000 -hda {} & >> /dev/null 2>&1".format(ramSize, vmName, macAddr, ifname, imgFile),shell=True)

def startInterfaces(portNames):
	for port in portNames:
		execute("ip link set {} up".format(port))

if __name__ == '__main__':
	conf = configParserObj(sys.argv[1])
	loggingLevel = conf.get('configure-ovs', 'logging-level')
	logFormat = '%(asctime)s %(levelname)s %(lineno)d %(process)d %(message)s'
	logging.basicConfig(filename='configure-ovs.log', level=getLoggingLevel(loggingLevel), format=logFormat)

	#Get configurations variables
	dbSock = getSectionValue('configure-ovs', 'dbSock')
	userPass = getSectionValue('configure-ovs', 'userPassword')
	numberOfVm = getSectionValue('configure-ovs', 'numberOfVm')
	bridgeIp = getSectionValue('configure-ovs', 'bridgeIp')
	bridgeName = getSectionValue('configure-ovs', 'bridgeName')
	portNames = getSectionValue('configure-ovs', 'portNames').split(',')
	configureOvs()
	addBridge()
	vmSections = [i.strip() for i in getSectionValue('configure-ovs', 'vmSections').split(',')]
	for i in vmSections:
		ramSize = getSectionValue(i, 'ramSize')
		vmName = getSectionValue(i, 'vmName')
		macAddr = getSectionValue(i, 'macAddr')
		ifname = getSectionValue(i, 'ifname')
		upScript = getSectionValue(i, 'upScript')
		downScript = getSectionValue(i, 'downScript')
		imgFile = getSectionValue(i, 'imgFile')
		ipAddr = getSectionValue(i, 'ipAddr')
		netmask = getSectionValue(i, 'netmask')

		addPorts(ifname)
		#generateSSHKey()
		#allocateIP()
		runVms()
	#startInterfaces(portNames)

# -*- coding: utf-8 -*-

"""
Config reader and manager for the core program

Class Configuration provides the functionalities for loading the `config.json`
and getting them parsed, and for generating the commands necessary for
initializing the proxy subprocesses(more details defined in module
`proxyconf`).
"""

from distutils.version import StrictVersion
from json import loads

VERSION_REQUIREMENT = "1.1" # required version of `config.json`

##############################################################################

class ConfigFileException(Exception):
    pass

##############################################################################

class Configuration:

    def __checkKeyExistence(self, parentDict, *keys):
        for each in keys:
            if not parentDict.has_key(each):
                return False
        return True

    def __loadCore(self, core):
        # parse json.core and save to class attributes
        
        # get key for cryptography
        self.key = str(core["key"])
        if type(self.key) != str:
            raise ConfigFileException("core.key is invalid.")

        # get IP for server and client
        if not core["server"].has_key("ip"):
            raise ConfigFileException("core.server.ip must be specified.")
        if not core["client"].has_key("ip"):
            raise ConfigFileException("core.client.ip must be specified.")
        self.serverIP = core["server"]["ip"]
        self.clientIP = core["client"]["ip"]

        # get UID/GID names
        if not core["user"].has_key('uidname'):
            raise ConfigFileException("core.user.uidname must be specified.")
        if not core["user"].has_key('gidname'):
            raise ConfigFileException("core.user.gidname must be specified.")
        self.user = (core["user"]["uidname"], core["user"]["gidname"])

    def __loadProxyAllocations(self, proxies):
        # get and validate proxy and ports allocations
        self.__proxies = {}

        for proxyName in proxies:
            proxyConfig = proxies[proxyName]
            self.__proxies[proxyName] = proxyConfig

    def listProxies(self):
        return self.__proxies.keys()

    def getProxyConfig(self, name):
        if not self.__proxies.has_key(name):
            raise ConfigFileException("No such proxy method defined.")

        proxyConfig = self.__proxies[name]
        proxyType = proxyConfig["type"]
        return {
            "user": self.user,
            "mode": self.mode,
            "name": name,
            "type": proxyType, 
            "config": proxyConfig,
            "key": self.key,
        }

    def getCoreConfig(self):
        """Generates a config profile for starting core process."""
        ret = {
            "netmask": "255.255.255.0",
            "key": self.key,
            "user": self.user,
        }
        if 'server' == self.mode:   # server mode
            ret["ip"] = self.serverIP
            ret["dstip"] = self.clientIP
        else:                       # client mode
            ret["ip"] = self.clientIP
            ret["dstip"] = self.serverIP
        return ret 

    def __init__(self, mode, config):
        # set mode for reading config file
        if 's' == mode:
            self.mode = 'server'
        elif 'c' == mode:
            self.mode = 'client'
        else:
            raise ConfigFileException("`mode` must be either 'c' or 's'")

        # try load the configuration file string, and parse into JSON.
        try:
            json = loads(config)
        except Exception,e:
            raise ConfigFileException("config.json parse error.")

        # read config file version declaration
        jsonVersion = "0.0.0"
        if json.has_key("version"):
            jsonVersion = json["version"]
        if StrictVersion(jsonVersion) < StrictVersion(VERSION_REQUIREMENT):
            raise ConfigFileException("config.json version too old.")

        # check existence of 'core' and 'proxies' entry
        if not self.__checkKeyExistence(json, 'core', 'proxies'):
            raise ConfigFileException("config.json incomplete.")

        # check entries of core
        jsonCore = json["core"]
        if not self.__checkKeyExistence(\
            jsonCore, 
            'server',
            'client',
            'user',
            'key',
        ):
            raise ConfigFileException("config.json incomplete.")
        self.__loadCore(jsonCore)

        # check for proxy allocations
        jsonProxies = json["proxies"]
        self.__loadProxyAllocations(jsonProxies)


##############################################################################

if __name__ == "__main__":
    j = open('../config.json', 'r').read()
    #print j
    config = Configuration(j)
    lst = config.listProxies()
    for n in lst:
        proxyConfig = config.getProxyConfig(n)
        print proxyConfig.getInitCommand('s')
        print proxyConfig.getInitCommand('c')
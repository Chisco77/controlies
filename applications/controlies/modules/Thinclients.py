##############################################################################
# -*- coding: utf-8 -*-
# Project:     ControlIES
# Module:    Thinclients.py
# Purpose:     Thinclients class
# Language:    Python 2.5
# Date:        4-Oct-2011.
# Ver:        4-Oct-2011.
# Author:   Manuel Mora Gordillo
# Copyright:    2011 - Manuel Mora Gordillo <manuito @no-spam@ gmail.com>
#
# ControlIES is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# ControlIES is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with ControlIES. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import ldap
import logging
import time
from math import floor
from operator import itemgetter
from Utils import ValidationUtils

class Thinclients(object):

    def __init__(self):
        pass
    
    def __init__(self,ldap,name,mac):
        self.ldap = ldap
        self.name = name
        self.mac = mac

    def validation(self,action):
        
        if self.name == "":
            return "name"

        if action == "add":
            if self.existsHostname():
                return "hostAlreadyExists"

        if self.mac == "":
            return "mac"

        if not ValidationUtils.validMAC(self.mac):
            return "mac"                        
        
        if action == "add":                            
            if self.existsMAC():
                return "macAlreadyExists"

        elif action == "modify":
            if not self.equalMAC():
				if self.existsMAC():
					return "macAlreadyExists"

        return "OK"

    def process(self,action):

        if action == "add":
            val = self.validation(action)
            
            if val != "OK":
                return val
            else:
                response = self.add()
                return response

        if action == "modify":
            val = self.validation(action)
            
            if val != "OK":
                return val
            else:
                response = self.modify()
                return response
                
        if action == "delete":
            response = self.delete()
            return response
        
        if action == "list":
            response = self.list();
            return response               
            
    def list(self,args):
                
        # grid parameters
        limit = int(args['rows'])
        page = int(args['page'])
        start = limit * page - limit
        finish = start + limit;             

        # sort by field
        sortBy = args['sidx']
        #if sortBy == "uid":
            #sortBy = "id"

        # reverse Sort
        reverseSort = False
        if args['sord'] == "asc":
            reverseSort = True
        
        search = self.ldap.search("cn=THINCLIENTS,cn=DHCP Config","cn=*",["cn","dhcpHWAddress"])
        filter="(|(dhcpOption=*subnet*)(dhcpOption=*log*))"

        rows = []

        try:
            host_search = args["cn"]
        except:
            host_search = ""
            
        try:
            mac_search = args["mac"]
        except:
            mac_search = ""

        # esto hay que cambiarlo: tenemos 4 groups en thinclientes
        for i in search[6:len(search)]:
            host = i[0][1]["cn"][0]
            mac = i[0][1]["dhcpHWAddress"][0].replace("ethernet ","")

            if ((host_search != "" and host.find(host_search)>=0) or (host_search=="")) and ((mac_search != "" and mac.find(mac_search)>=0) or (mac_search=="")):
				nodeinfo=i[0][0].replace ("cn=","").split(",")
				row = {
					"id":host, 
					"cell":[host, mac, nodeinfo[1]],
					"cn":host,
					"dhcpHWAddress":mac,
					"groupName":mac
				}             
				rows.append(row)
				
        if len(rows) > 0:
            totalPages = floor( len(rows) / int(limit) )
            module = len(rows) % int(limit)

            if module > 0:
				totalPages = totalPages+1
        else:
            totalPages = 0
            
        if page > totalPages:
            page = totalPages
			
        result = sorted(rows, key=itemgetter(sortBy), reverse=reverseSort)
        return { "page":page, "total":totalPages, "records":len(rows), "rows":result[start:finish] }                    
          

    def add(self):

		attr = [
		('objectclass', ['top','dhcpHost']),
		('cn', [self.name] ),
		('dhcpStatements', ['filename "/var/lib/tftpboot/ltsp/i386/pxelinux.0"'] ), 
		('dhcpHWAddress', ['ethernet ' + self.mac] )
		]		
		group = self.getFreeGroup()
		
		self.ldap.add("cn="+self.name +",cn="+group["freeGroup"]+",cn=THINCLIENTS,cn=DHCP Config", attr)
            
		return "OK"
        
    def modify(self):

        attr = [(ldap.MOD_REPLACE, 'dhcpHWAddress', ['ethernet ' + self.mac])]
        self.ldap.modify("cn="+self.name+",cn="+self.getGroup()+",cn=THINCLIENTS,cn=DHCP Config", attr)

        return "OK"

    def delete(self):
        group = self.getGroup()
        if group != "noGroup":
            self.ldap.delete('cn='+ self.name +',cn='+group+',cn=THINCLIENTS,cn=DHCP Config')

        return "OK"     


    def move(self,purpose):
        data = self.getHostData()
        self.delete()
		
        self.name= purpose
        self.mac= data['mac']		
        self.add()

        return "OK"
               
            
    def existsHostname(self):
        result = self.ldap.search("cn=THINCLIENTS,cn=DHCP Config","cn="+self.name,["cn"])
        
        if len(result) > 0:
            return True
        
        return False
        
    def existsMAC(self):
        result = self.ldap.search("cn=THINCLIENTS,cn=DHCP Config","dhcpHWAddress=*",["dhcpHWAddress"])
        for i in range (0, len(result) - 1):
            if result [i][0][1]['dhcpHWAddress'][0].replace ("ethernet ", "") == self.mac:
				return True
        
        return False

    def equalMAC(self):
        result = self.ldap.search("cn=THINCLIENTS,cn=DHCP Config","cn="+self.name,["dhcpHWAddress"])
        if result[0][0][1]['dhcpHWAddress'][0].replace ("ethernet ", "") == self.mac:
            return True
        
        return False

       
    def getName (self):
        return self.mac   

    def getHostData(self):
        g = self.getGroup()
        result = self.ldap.search("cn="+g+",cn=THINCLIENTS,cn=DHCP Config","cn="+self.name,["cn","dhcpHWAddress"])

        dataHost = {
            "cn":self.name,
            "mac":result[0][0][1]["dhcpHWAddress"][0].replace("ethernet ","")
        }
        return dataHost    

    def getGroup (self):
        groups = self.getThinclientGroups()        
        for g in groups['groups']:
            search = self.ldap.search("cn="+g+",cn=THINCLIENTS,cn=DHCP Config","cn="+self.name,["cn"])
            if len(search) == 1:
			    return g
            
        return "noGroup"


    def getThinclientGroups (self):
        groups = []
        search = self.ldap.search("cn=THINCLIENTS,cn=DHCP Config","cn=group*",["cn"])
        for g in search:
            groups.append (g[0][1]["cn"][0])
            
        return { "groups":groups }


    def groupOverflow(self,group,overflow):
        search = self.ldap.search("cn="+group+",cn=THINCLIENTS,cn=DHCP Config","cn=*",["cn"])       
        if len(search)-2 >= overflow:
            return True
                
        return False
    

    def getFreeGroup (self):
        freeGroup = []
        groups = self.getThinclientGroups()        
        for g in groups['groups']:
            if not self.groupOverflow(g,300):
				return { "freeGroup":g }

        return { "freeGroup" : 'noFreeGroup' }

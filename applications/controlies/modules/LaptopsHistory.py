##############################################################################
# -*- coding: utf-8 -*-
# Project:      ControlIES
# Module:       LaptopsHistory.py
# Purpose:      LaptopsHistory class
# Language:     Python 2.5
# Date:         6-Jun-2012.
# Ver:          6-Jun-2012.
# Author:       Manuel Mora Gordillo
# Copyright:    2012 - Manuel Mora Gordillo <manuito @no-spam@ gmail.com>
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

from math import floor
import datetime

class LaptopsHistory(object):

    def __init__(self):
        pass
    
    def __init__(self,DB,id_historical,id_laptop,id_state,id_user_type,nif,username,name,comment):
        self.DB = DB
        self.id_historical = str(id_historical)        
        self.id_laptop = str(id_laptop)
        self.id_state = str(id_state)

        try:
            self.id_user_type = int(id_user_type)
        except ValueError:
            self.id_user_type = 0

        #self.id_user_type = int(id_user_type)
        self.nif = str(nif)
        self.username = str(username)
        self.name = str(name)
        self.comment = str(comment)
        
    def validation(self,action):

        if self.id_state == "none":
            return "id_state"

        if self.id_state=="2" or self.id_state=="3":
            if self.username == "":
                return "username"

            if self.id_user_type == 0:
                return "id_user_type"
                
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
        
    def list(self,args):

        #sql = "SELECT id_historical, datetime, state, username, name, comment FROM laptops_historical lh INNER JOIN states s ON lh.id_state=s.id_state"
        #sql = sql + " WHERE lh.id_laptop='"+str(args["id_laptop"])+"'"
        #sql = sql + " ORDER BY "+args['sidx']+" "+args['sord']
        #result = self.DB.executesql(sql)

        id_laptop = str(args["id_laptop"])
        result=self.DB(self.DB.laptops_historical.id_laptop==id_laptop)(self.DB.laptops_historical.id_state==self.DB.states.id_state).select(self.DB.laptops_historical.ALL, self.DB.states.state, orderby=args['sidx']+" "+args['sord']+", id_historical desc")

        rows = []
        for reg in result:
            d = datetime.datetime.strptime(str(reg['laptops_historical']['datetime']), '%Y-%m-%d %H:%M:%S')
            new_dataformat = d.strftime('%d/%m/%Y %H:%M:%S')

            row = {
                "id":reg['laptops_historical']['id_historical'],
                "cell":[new_dataformat,reg['states']['state'],reg['laptops_historical']['username'],reg['laptops_historical']['name'],reg['laptops_historical']['comment']],
                "datetime":new_dataformat,
                "state":reg['states']['state'],
                "username":reg['laptops_historical']['username'],
                "name":reg['laptops_historical']['name'],
                "comment":reg['laptops_historical']['comment']
            }
            rows.append(row)

        # grid parameters
        limit = int(args['rows'])
        page = int(args['page'])
        start = limit * page - limit
        finish = start + limit;             
                    
        # grid parameters
        if len(rows) > 0:
            totalPages = floor( len(rows) / int(limit) )
            module = len(rows) % int(limit)

            if module > 0:
                totalPages = totalPages+1
        else:
            totalPages = 0

        if page > totalPages:
            page = totalPages

        return { "page":page, "total":totalPages, "records":len(rows), "rows":rows[start:finish] }


    def add(self): 
        now = datetime.datetime.now()
        sql = "INSERT INTO laptops_historical (id_historical,id_laptop,datetime,username,name,id_user_type,nif,comment,id_state) "
        sql = sql+" VALUES (null,"+ str(self.id_laptop) +",'"+ now.strftime('%Y-%m-%d %H:%M:%S')+"','"+self.username+"','"+self.name+"',"+ str(self.id_user_type)+",'"+ self.nif+"','"+self.comment+"','"+ str(self.id_state)+"')"
        result = self.DB.executesql(sql)

        #self.DB.laptops_historical.insert (id_laptop=self.id_laptop, datetime=now.strftime('%Y-%m-%d %H:%M:%S'), username=self.username, name = self.name, id_user_type=self.id_user_type,nif=self.nif,comment=self.comment, id_state=self.id_state)
        #self.DB.commit()
        
        return "OK"
            
            
    def modify(self):
        now = datetime.datetime.now()
        self.DB(self.DB.laptops_historical.id_historical==self.id_historical).update(username=self.username, name=self.name, id_user_type=self.id_user_type, nif=self.nif, comment = self.comment, id_state = self.id_state, datetime=now.strftime('%Y-%m-%d %H:%M:%S'))        
        self.DB.commit()
        return "OK"


    def delete(self):
        self.DB(self.DB.laptops_historical.id_historical==self.id_historical).delete()
        self.DB.commit()
        return "OK"

    def getAllStates(self):
        sql="SELECT * FROM states ORDER BY state"
        result = self.DB.executesql(sql)

        data=[]
        for r in result:
            dataType = {
                "id_state":str(r[0]),
                "state":r[1]
            }
            data.append(dataType)
        return data

    def getAllUserTypes(self):
        sql="SELECT * FROM users_types ORDER BY user_type"
        result = self.DB.executesql(sql)

        data=[]
        for r in result:
            dataType = {
                "id_user_type":str(r[0]),
                "user_type":r[1]
            }
            data.append(dataType)
        return data

    def getDataHistory(self):
        sql="SELECT * FROM laptops_historical WHERE id_historical='"+str(self.id_historical)+"'"
        result = self.DB.executesql(sql)

        data = {"id_historical":"","id_laptop":"","username":"","name":"","id_user_type":"","nif":"","comment":"","id_state":""}
        if len(result)>0:
            data = {
                "id_historical":str(result[0][0]),
                "id_laptop":str(result[0][1]),
                "username":str(result[0][3]),
                "name":str(result[0][4]),
                "id_user_type":str(result[0][5]),
                "nif":str(result[0][6]),
                "comment":str(result[0][7]),
                "id_state":str(result[0][8])
            }

        return data

    def getLastHistory(self):
        sql="SELECT username, id_state FROM laptops_historical WHERE id_laptop='"+str(self.id_laptop)+"' ORDER BY id_historical desc LIMIT 0,1"
        result = self.DB.executesql(sql)

        data={"username":"","id_state":""}
        if len(result)>0:
            data = {
                "username":str(result[0][0]),
                "id_state":str(result[0][1])
            }

        return data
    
    def userAssignment(self):
        sql="SELECT lh.id_laptop, lh.username FROM laptops l, laptops_historical lh"
        sql=sql+" WHERE l.id_laptop=lh.id_laptop"
        sql=sql+" GROUP BY l.id_laptop ORDER BY lh.datetime desc"
        result = self.DB.executesql(sql)

        for r in result:
            if str(r[1])==self.username:
                return str(r[0])
                    
        return False
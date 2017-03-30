#!/bin/python
# -*- coding: utf-8 -*-
from pymongo import MongoClient
import pymongo
import json
import datetime
from random import randint
from bson.objectid import ObjectId


class Repository(object):
    """
    Clase para operaciones con colecciones de datos.
    """
    
    def __init__(self,dbcoll,dbdb,mongostring):
        self.client = MongoClient(mongostring)
        self.db_name = dbdb
        self.data_coll_name = dbcoll
        self.client.server_info()
        
    def getDataCollection(self):
        return self.client[self.db_name][self.data_coll_name]
     
    def findData(self,criteria=""):
        """
        Devuelve todos como lista
        """
        return list(self.getDataCollection().find(criteria))
  
    def add(self, data):
        """
        Agrega uno si no existe
        """
        # try to find data
        try:
            origin = data['origin']
            origin_id = data["origin_id"]
            cursor = self.getDataCollection().find({ 'origin_id': origin_id, 'origin': origin}, limit=1)
            # do nothing if data exists already
            if cursor.count() > 0:
                cursor.close()
                return 0
            cursor.close()
        except Exception, e:
            print "Query failed finding data"
        # insert data
        try:
            self.getDataCollection().insert_one(data)
            return 1
        except Exception, e:
            print "Failed to insert data: ", e
            return 0
    

    def updateOne(self,id,field,value):
        """
        Actualiza field con value para el que tiene _id = id.
        """
        return self.getDataCollection().update_one({'_id': ObjectId(id) }, {'$set': {field: value}})
   
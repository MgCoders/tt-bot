#!/bin/python
# -*- coding: utf-8 -*-
from pymongo import MongoClient
import pymongo
import json
import datetime
from random import randint
from bson.objectid import ObjectId
import gridfs


class Repository(object):
    """
    Clase para operaciones con colecciones de datos.
    """

    def __init__(self,dbcoll,dbdb,mongostring=None):
        if not mongostring:
            keys = {}
            exec(open('key_all.py').read(), keys)
        self.client = MongoClient(keys['mongostring'])
        self.db_name = dbdb
        self.data_coll_name = dbcoll
        self.client.server_info()
        self.fs = gridfs.GridFS(self.client[self.db_name])

    def getCollection(self):
        return self.client[self.db_name][self.data_coll_name]

    def getFs(self):
        return self.fs

    def find(self,criteria=""):
        """
        Devuelve todos como lista
        """
        return list(self.getCollection().find(criteria))

    def update_one(self,id,field,value):
        """
        Actualiza field con value para el que tiene _id = id.
        """
        return self.getCollection().update_one({'_id': ObjectId(id) }, {'$set': {field: value}})

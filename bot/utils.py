#!/bin/python
# -*- coding: utf-8 -*-
import socket
import urlparse

def utf8(unicode_text):
    return unicode_text.encode('utf-8')

def checkAndFixUrl(raw_data):
    finalUrl = None
    url = urlparse.urlparse(raw_data)
    if not url.scheme or not url.scheme.startswith('http'):
        raw_data = 'http://'+raw_data
        url = urlparse.urlparse(raw_data)
    #Ver si resuelve o excepcion
    hostname = socket.gethostbyname(url.hostname)
    if url.path:
        finalUrl = url.scheme+'://'+url.netloc+url.path
    else:
        finalUrl = url.scheme+'://'+url.netloc
    return finalUrl

def escapeMarkdown(text):
    text = text.replace('_','\_')
    text = text.replace('*','\*')
    return text

def splitEmail(raw_data):
    username = email = None
    s = raw_data.split('@')
    if (len(s)>1):
        email = raw_data
        username = s[0]
    else:
        email = None
        username = raw_data
    return (username,email)

#This file just loads resource names
import os
from classes import *

dir = os.path.dirname(os.path.abspath(__file__))

def folder_list(folder):
    return dict([(os.path.splitext(os.path.basename(file))[0], os.path.join(dir, folder, file)) for file in os.listdir(os.path.join(dir, folder))])

def folder_read(folder):
    return dict([(os.path.splitext(os.path.basename(file))[0], open(os.path.join(dir, folder, file), "r").read()) for file in os.listdir(os.path.join(dir, folder))])

css = folder_list("css")
html = folder_list("html")
html = folder_list("js")
icons = folder_list("icons")
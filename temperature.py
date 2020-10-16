import os
import glob
import time
from elasticsearch import Elasticsearch
import uuid
import datetime
import sys
from probelist import probes

log = open("tempprobe.log", "a")
sys.stdout = log

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

es=Elasticsearch([{'host':'x.x.x.x','port':9200}])

base_dir = '/sys/bus/w1/devices/'
# device_folders = glob.glob(base_dir + '28*') #moved into the loop to incase the device gets unplugged
device_file = '/w1_slave'

def read_temp_raw(device_folder):
    f = open(device_folder + device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_folder):
    lines = read_temp_raw(device_folder)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        now = datetime.datetime.now().isoformat()
        probe_id = device_folder[-6:]
        if device_folder[-6:] in probes:
            probe_id = probes[device_folder[-6:]]
        return {'probe_id': probe_id, 'temperature': temp_f, 'datestamp': now}

while True:
    device_folders = glob.glob(base_dir + '28*')
    date = datetime.date.today()
    index_name = str(date) + '-temp-reading'
    for device_folder in device_folders:
        data = read_temp(device_folder)
        res = es.index(index=index_name, doc_type='temp-reading', id=uuid.uuid4(), body=data)
        print(data, res)
    time.sleep(30)


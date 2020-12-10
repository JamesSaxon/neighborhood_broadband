import sys
from influxdb import InfluxDBClient

class InfluxCred():

    def __init__(self, host, port, username, password, deployment, database):

        if not host:
	    print("Get Influx creds from Jamie or Guilherme. Exiting!!")
	    sys.exit()

        self.host       = host       
        self.port       = port       
        self.username   = username   
        self.password   = password   
        self.deployment = deployment 
        self.database   = database   

        self.client = InfluxDBClient(host = host, port = port, 
                                     username = username, password = password,
                                     database = database, ssl = True, verify_ssl = True)

uc_cred = InfluxCred(host = "", port = None,
                     username = "", password = "", 
                     deployment = "", database = "")


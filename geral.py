from email import header
import pandas as pd
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib3
urllib3.disable_warnings()

def main():
    print("""    ____  ___       _____   ___    _________   ____________  ______  __
   / __ \/   |     /  _/ | / / |  / / ____/ | / /_  __/ __ \/ __ \ \/ /
  / /_/ / /| |     / //  |/ /| | / / __/ /  |/ / / / / / / / /_/ /\  / 
 / ____/ ___ |   _/ // /|  / | |/ / /___/ /|  / / / / /_/ / _, _/ / /  
/_/   /_/  |_|  /___/_/ |_/  |___/_____/_/ |_/ /_/  \____/_/ |_| /_/   
""")
    dfs = []
    totaldf = pd.DataFrame()
    df = pd.read_excel("apis.xlsx")
    for i, element in df.iterrows():
        if serverup(element) == 1:
            if validateapi(element) == 1:
                dados = server(element)
                dfs.append(dados)
            else:
                print("Houve algum erro!")
        else:
            print("Houve algum erro!")
    totaldf = pd.concat(dfs)
    totaldf.columns = ["Data da Coleta","Cliente","hostname","ip-address","model","EOL Model","Last OS","serial","sw-version","EOL Software","resources","rules"]
    totaldf.to_excel("Coleta.xlsx",header=True, index=False)
    print("Coleta realizada!!")

def serverup(host):
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host[1], 443))
    if result == 0:
        return 1
    else:
        print (f"Host {host[1]} is not alive")
        return 0

def validateapi(host):
    dashboard = requests.request("GET", f"https://{host[1]}/api/?type=op&cmd=<show><system><info></info></system></show>&key={host[2]}", verify=False)
    if dashboard.status_code == 200:
        return 1
    else:
        print(f"[+] Houve um erro no ip: {host[1]}")
        return 0

def server(ip):
    host = f"https://{ip[1]}"
    apikey = ip[2]

    chavesdashboard = ["hostname", "ip-address", "sw-version", "model", "serial"]
    dashboard_list = []

    dashboard = requests.request("GET", f"{host}/api/?type=op&cmd=<show><system><info></info></system></show>&key={apikey}", verify=False)
    _resources = requests.request("GET", f"{host}/api/?type=config&action=get&xpath=/config/devices/entry[@name='localhost.localdomain']/network/tunnel&key={apikey}", verify=False)
    _decryption = requests.request("GET", f"{host}/api/?type=config&action=get&xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/decryption/rules&key={apikey}", verify=False)

    dashboardET = ET.fromstring(dashboard.text)
    _resourcesET = ET.fromstring(_resources.text)
    _decryptionET = ET.fromstring(_decryption.text)

    dashboard_list.append(datetime.now())
    dashboard_list.append((ip[0]))
    for child in dashboardET.iter("*"):  
        if child.tag in chavesdashboard:
            dashboard_list.append(child.text)
            if child.tag == "sw-version":
                temp = str(child.text).strip(".")
                version = (f"{temp[0]}.{temp[2]}")
                eol = paloaltoeolversion(version)
                try:  
                    dashboard_list.append(eol)
                except:
                    dashboard_list.append("N/A")

            if child.tag == "model":
                model = str(child.text)
                eolmodel = paloaltoeolmodel(model)
                try:
                    dashboard_list.append(eolmodel[0])
                    dashboard_list.append(eolmodel[1])
                except:
                    dashboard_list.append("N/A")
                    dashboard_list.append("N/A")
    policies = []
    for child in _resourcesET.findall("./result/tunnel/*"):  
        count = sum(1 for _ in child.iter("*"))
        if count > 1:
            policies.append(child.tag)
        #else:
            #dashboard_list.append("N/A")
    dashboard_list.append(', '.join(policies))
    rules = []
    for child in _decryptionET.findall("./result/"): 
        count = sum(1 for _ in child.iter("*"))
        if count > 1:
            rules.append(child.tag)
    dashboard_list.append(', '.join(rules))
           # dashboard_list.append("N/A")

    #dashboard_list.append((" "))

    df = pd.DataFrame(dashboard_list)
    transpose = pd.DataFrame.transpose(df)
    return transpose

def paloaltoeolversion(_random):
    version = pd.read_html("https://www.paloaltonetworks.com/services/support/end-of-life-announcements/end-of-life-summary")
    z = "N/A"
    for i in range(len(version[0])):
        if _random == version[0].loc[i,0]:
            z = version[0].loc[i,2]
    return z


def paloaltoeolmodel(_random):
    paloaltoeolmodel = pd.read_html("https://www.paloaltonetworks.com/services/support/end-of-life-announcements/hardware-end-of-life-dates")
    z = ("N/A", "N/A")
    for i,x in paloaltoeolmodel[0].iterrows():
        if _random in x[0]:
            z = (x[2], x[4])
    return z

if __name__ == "__main__":
    main()
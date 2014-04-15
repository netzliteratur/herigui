#!/usr/bin/env python
''' GUI for Heritrix 3.1.x'''

##################################################
# FILE:     HeriGUY.py                           #
# VERSION:  0.4 BETA                             #
# DATE:     12.08.2013                           #
# AUTHOR:   steffen fritz                        #
# CONTACT:  steffen.fritz@dla-marbach.de         #
#                                                #
# NOTES:                                         #
#           a cancelled job must be teardowned   #
#           returns 401 if such a job is started #
##################################################
# DESCRIPTION:                                   #
#           GUI for Heritrix 3.1.x               #
# REQUIREMENTS:                                  #
#           Python 2.6/2.7                       #
#           easyGUI                              #
#           requests                             #
##################################################

# IMPORT SECTION

import sys
import time
import ConfigParser
import webbrowser

try:
    import modules.easygui as easygui
    import requests
    from requests.auth import HTTPDigestAuth
    
except ImportError, error:
    print("Import Error: " + str(error))
    sys.exit(1)


def welcome():
    'Main Menu'
    title = "HeriGUY v0.4 BETA"
    image = "config/herilogo.gif"
    choices = ["Crawler-Beans", "Befehl an Heritrix senden", \
		    "HeriGUY konfigurieren", "Heritrix im Browser oeffnen", \
		    "Beenden", "Hilfe"]
    choice = easygui.buttonbox(title=title, image=image, choices=choices)
    
    return choice


def config_me():
    'Configurator For HeriGUY. Heritrix Credentials'
    msg = "HeriGUY Konfiguration"
    title = "HeriGUY v0.2"
    fieldNames = ["https://HOST[:PORT]", "Benutzername", "Passwort", "Kontakt-URL"]
    fieldValues = []
    fieldValues = easygui.multenterbox(msg, title, fieldNames)
    if fieldValues == None:
        easygui.msgbox("HeriGUY benoetigt eine Konfiguration. Breche ab.")
        sys.exit(0)
    else:
        config = ConfigParser.RawConfigParser()
        config.add_section('Heritrix')
        config.set('Heritrix', 'url', fieldValues[0])
        config.set('Heritrix', 'user', fieldValues[1])
        config.set('Heritrix', 'passwd', fieldValues[2])
        config.set('Heritrix', 'contact_url', fieldValues[3])
        with open('config/main.cfg', 'wb') as configfile:
            config.write(configfile)
        
        easygui.msgbox("Konfiguration erfolgreich gespeichert.")


def read_config():
    'Gets Configuration From main.cfg in config/'
    config = ConfigParser.RawConfigParser()
    config.read('config/main.cfg')
    
    url = config.get('Heritrix', 'url')
    user = config.get('Heritrix', 'user')
    passwd = config.get('Heritrix', 'passwd')
    contact_url = config.get('Heritrix', 'contact_url')

    return url, user, passwd, contact_url


def success_msg():
    'Success if return code heritrix is = 200'
    easygui.msgbox("Befehl erfolgreich ausgefuehrt")


def warning_msg(errmsg):
    'Generic Warning Message'
    msg = "Es gab einen Verarbeitungsfehler. " + str(errmsg)
    easygui.msgbox(msg)


def get_values(contact_url):
    'Get Values For New Job, Overwrites Placeholders With Input Data'
    values_dict = {}
    msg = "Einstellungen"
    title = "Dateneingabe"
    fieldNames  = ["Zu spiegelnde URL", "SURT"]
    fieldValues = []
    fieldValues = easygui.multenterbox(msg, title, fieldNames)
    
    if fieldValues == None:
        pass
    else:
        values_dict["http://example.example/example"] = fieldValues[0] + "\n" + fieldValues[1]
        values_dict['ENTER_AN_URL_WITH_YOUR_CONTACT_INFO_HERE_FOR_WEBMASTERS_AFFECTED_BY_YOUR_CRAWL'] = contact_url 

        return values_dict


def choice_beans():
    'Submenu for Beans'
    # "Vorhandene Bean bearbeiten" aus Menu entfernt
    msg = "Auswahl"
    choices = ["Neue Crawler-Bean erstellen", \
		    "Lokale Crawler-Bean auf Server laden", "Abbrechen"]
    choice = easygui.buttonbox(msg, choices=choices)

    return choice


def create_bean(values_dict):
    'Create New Bean And Save It To temp/'   
    fd = open("templates/crawler-beans-template.cxml", "r")
    data = fd.read()
    fd.close()
    
    for key, value in values_dict.items():     
        data = data.replace(key, value)
        
    fe = open("temp/crawler-beans.cxml", "w")
    fe.write(data)
    fe.close()
    
    return data
    
    
def upload_bean(baseurl, user, passwd):
    'Upload A Local Bean To Heritrix'
    filename = easygui.fileopenbox(title = "cxml-Datei waehlen", \
		    filetypes = "*.cxml")
    msg = "Fuer welchen Job ist die Bean bestimmt?"
    job_name = easygui.enterbox(msg)
    if job_name == None:
        pass
    else:
        fd = open(filename, "r")
        data = fd.read()
        fd.close()
    
        url = baseurl + '/engine/job/' + job_name + '/jobdir/crawler-beans.cxml'
        requests.put(url, auth=HTTPDigestAuth(user, passwd), \
			data=data, verify=False)


def open_heritrix_web(url):
    'Open Heritrix In A Browser'
    webbrowser.open(url)
    

def hilfe():
    'help message'
    msg = "Noch nicht implementiert."
    easygui.msgbox(msg)


def say_heritrix(baseurl, user, passwd, contact_url):
    'Access Heritrix Via API'
    msg = "Heritrix steuern"
    choices = ["Job anlegen", "Job starten", "Abbrechen"]
    choice = easygui.buttonbox(msg, choices=choices)
    
    if choice == 'Job anlegen':
        msg = "Name des neuen Jobs eingeben"
        job_name = easygui.enterbox(msg)
        if job_name != None:
            payload = {'action':'create', 'createpath':job_name}
            url = baseurl + '/engine'
            ret = requests.post(url, auth=HTTPDigestAuth(user, passwd), \
                 data=payload, verify=False)
            print(ret)
 
            # Job-Bean erstellen
            values_dict = get_values(contact_url)
            data = create_bean(values_dict)
            
            # Bean auf Server uebertragen
            msg = "Soll die Konfigurationsdatei auf den Server uebertragen werden?"
            choices = ["Ja", "Nein"]
            choice = easygui.buttonbox(msg, choices=choices)
            
            if choice == "Ja":
                url = baseurl + '/engine/job/' + job_name + '/jobdir/crawler-beans.cxml'
                ret = requests.put(url, auth=HTTPDigestAuth(user, passwd), \
                    data=data, verify=False)
                print(ret)
            else:
                pass
            
            msg = "Soll die Jobkonfiguration auf dem Server gebaut werden?"
            choices = ["Ja", "Nein"]
            choice = easygui.buttonbox(msg, choices=choices)
        
            if choice == "Ja":
                payload = {'action':'build'}
                url = baseurl + '/engine/job/' + job_name
                ret = requests.post(url, auth=HTTPDigestAuth(user, passwd), \
                    data=payload, verify=False)
                print(ret)
            else:
                pass
        else:
            pass
        
    elif choice == 'Job starten':
        msg = "Name des zu startenden Jobs angeben"
        job_name = easygui.enterbox(msg)
        if job_name == None:
            pass
        else:
            payload = {'action':'launch'}
            url = baseurl + '/engine/job/' + job_name
            requests.post(url, auth=HTTPDigestAuth(user, passwd),  \
                data=payload, verify=False)
            time.sleep(3)
            payload = {'action':'unpause'}
            requests.post(url, auth=HTTPDigestAuth(user, passwd), \
                data=payload, verify=False)
        
    else:
        pass
    

def main():
    'The Main Function'
    try:
        url, user, passwd, contact_url = read_config()
    except:
        easygui.msgbox("Bitte HeriGUY im folgenden Fenster konfigurieren")
        config_me()
        url, user, passwd, contact_url = read_config()
    
    keep_running = True
    while keep_running == True:
        
        choice = welcome()
        
        if choice == 'Crawler-Beans':
            beans_choice = choice_beans()
            if beans_choice == "Neue Crawler-Bean erstellen":
                try:
                    values_dict = get_values(contact_url)
                    if values_dict == None:
                        pass
                    else:
                        create_bean(values_dict)
                        easygui.msgbox("Bean befindet sich im Verzeichnis temp")
                
                except RuntimeError, err:
                    warning_msg(err)
                    sys.exit(1) 

            elif beans_choice == "Lokale Crawler-Bean auf Server laden": 
                try:
                    upload_bean(url, user, passwd)
                except RuntimeError, err:
                    warning_msg(err)
                    sys.exit(1)
            else:
                pass
        
        elif choice == 'Hilfe':
            hilfe()
        
        elif choice == 'Beenden':
            keep_running = False
            sys.exit(0)
        
        elif choice == 'Befehl an Heritrix senden':
            try:
                say_heritrix(url, user, passwd, contact_url)
            except RuntimeError, err:
                warning_msg(err)
                sys.exit(1)

        elif choice == 'HeriGUY konfigurieren':
            try:	
                config_me()
            except RuntimeError, err:
                warning_msg(err)
                sys.exit(1)

        elif choice == 'Heritrix im Browser oeffnen':
            try: 
                open_heritrix_web(url)
            except Warning:
                warning_msg("Konnte Browser nicht oeffnen")
                pass
        
        else:
            sys.exit(1)
            
if __name__ == '__main__':
    main()
            

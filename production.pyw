import threading
import time
import sys
import tkinter
import os
import glob
import requests
import ctypes
import re
import datetime
import serial
import webbrowser
import psutil
from PIL import ImageTk, Image

########################################################
##Change log
##v1   - v6 build phase
##History trace started
##v7   - Adding instructions
##     - Added instruction path to config
##     - Removed timer
##     - instructions should load up in default tool
##     - Added variable to config for enable or disable instructions
##     - Added technician indicator
##v7.5 - Changed module in updateProdData
##     - Added FPY/LRF graph in config
##     - Added LRF view
##     - Added Login option to config
##v8   - Added company logo
##     - Add show instruction button
##     - Fixed colours for light mode
##v8.2 - Deleted lock symbol
##     - Repaired display an fullscreen
##     - Minor bug fix in sending data from M957
##v8.3 - Fixed timer issue
##     - Fixed perf graph
##v9   - Error handling added
##     - Added timeout for rest
##     - Fixed the issue with exit
##     - Fixed parser issue which cause stop
##v10  - Fixed issue with topmost windows
##v10.5- Updated performance calculation
##     - Added disable of trainings
##     - Added function to move logs if they are not send to itac
########################################################
##Stable version
##v11  - Now runable from network drive
##v11a - Fixed the multipanel error with deleting files too soon
##     - Deleted sleep before if remove_file == True: 0.05
##v11b - Fixed issue with empy SN
##v11c - Fixed issue with ICT 11 with =<> in same line when parsing the log
##v11d - Fixed issue with ICT 11 with =<> in same line when parsing the log
##v11e - Fixed issue with Reader cancel
##v11f - Fixed locking withou reader
##v12  - Changed logic for login/logout
##v12a - Added autogeneration of config file if file doesnt exist
##     - Compiler changes to single file
##v13  - Added Rexxam support
##     - New log file variable for selection of the system
##v14  - Rexxam fixes
##v14b - Fixed NOK components mark
##v14c - Added general instruction to config
##v15  - New SESO for upload
##     - Rexxam fail fixed
##v16  - Added network config files
##     - Added minimize button
##     - iTAC warning 212 ignored
########################################################
tLock = threading.Lock()
tLock = threading.BoundedSemaphore(value=1)

##Content for restAPI and ITAC
########################################################
login = 'regLogin'
check0 = 'trGetSerialNumberInfo'
check1 = 'trCheckSerialNumberState'
upload = 'trUploadResultDataAndRecipe'
logout = 'regLogout'
headers = {'content-type': 'application/json'}

tmout = 5

########################################################

class support:
    def read_config():
        file = open('C:\\production\\tester.ini', 'r')
        temp = file.read(-1)
        file = open('//fs/gs/IndustrialEngineering/Public/04_Testing/01_APPs/production/Configuration/' + temp + '.ini', 'r')
        temp = file.read(-1)
        temp = temp.splitlines()
        for x in temp:
            if '##' in x:
                continue
            elif 'stationNumber' in x:
                stationNumber = x.split('=')[1]
            elif 'dbtype' in x:
                dbtype = x.split('=')[1]
            elif 'logPATH' in x:
                PATH = x.split('=')[1]
            elif 'thread_number' in x:
                thread_number = int(x.split('=')[1])
            elif 'restAPI' in x:
                restAPI = x.split('=')[1]
            elif 'remove_file' in x:
                remove_file = x.split('=')[1]
                if remove_file == 'False':
                    remove_file = ''
            elif 'dashboard' in x:
                dashboard = x.split('=')[1]
                if dashboard == 'False':
                    dashboard = ''
            elif 'sesoData' in x:
                sesoData = x.split('=')[1]
            elif 'sesoOperator' in x:
                sesoData1 = x.split('=')[1]
            elif 'SESO' in x:
                useSESO = x.split('=')[1]
                if useSESO == 'False':
                    useSESO = ''
            elif 'parse' in x:
                parselog = x.split('=')[1]
                if parselog == 'False':
                    parselog = ''
            elif 'useReader' in x:
                useReader = x.split('=')[1]
                if useReader == 'False':
                    useReader = ''
            elif 'COM' in x:
                COM = x.split('=')[1]
            elif 'Baud' in x:
                BAUD = x.split('=')[1]
            elif 'greenFPY' in x:
                greenFPY = x.split('=')[1]
            elif 'orangeFPY' in x:
                orangeFPY = x.split('=')[1]
            elif 'color_mode' in x:
                mode = x.split('=')[1]
            elif 'instrPATH' in x:
                serverInstr = x.split('=')[1]
            elif 'instrGEN' in x:
                serverInstrGen = x.split('=')[1]
            elif 'showInstr' in x:
                showIntr = x.split('=')[1]
                if showIntr == 'False':
                    showIntr = ''
            elif 'graphMode' in x:
                graphMode = x.split('=')[1]
            elif 'useLogin' in x:
                useLogin = x.split('=')[1]
                if useLogin == 'False':
                    useLogin = ''
            elif 'company_logo' in x:
                company_logo = x.split('=')[1]
            elif 'showInfo' in x:
                showInfo = x.split('=')[1]
                if showInfo == 'False':
                    showInfo = ''
            elif 'useTraining' in x:
                useTraining = x.split('=')[1]
                if useTraining == 'False':
                    useTraining = ''
            elif 'log_format' in x:
                log_format = x.split('=')[1]
            elif 'ZAPATH' in x:
                ZAPATH = x.split('=')[1]

        return stationNumber, dbtype, PATH, thread_number, restAPI, bool(remove_file), bool(dashboard), sesoData, bool(useSESO), bool(parselog), bool(useReader), COM, BAUD, int(greenFPY), int(orangeFPY), mode, serverInstr, bool(showIntr), graphMode, bool(useLogin), company_logo, bool(showInfo), sesoData1, bool(useTraining), log_format, serverInstrGen, ZAPATH

    def fpy_color(fpy, mode):
        if mode == 'light':
            if fpy >= greenFPY:
                fpy_color = '#539955'
            elif fpy >= orangeFPY:
                fpy_color = '#997753'
            else:
                fpy_color = '#995353'
        else:
            if fpy >= greenFPY:
                fpy_color = '#b3ff87'
            elif fpy >= orangeFPY:
                fpy_color = '#ffc187'
            else:
                fpy_color = '#ff8787'

        return fpy_color

    def lrf_color(lrf, curr_perf):
        lrf_perc = lrf/100 * curr_perf
        if mode == 'light':
            if lrf_perc < 80:
                lrf_color = '#995353'
            elif lrf_perc < 100:
                lrf_color = '#997753'
            else:
                lrf_color = '#539955'
        else:
            if lrf_perc < 80:
                lrf_color = '#ff8787'
            elif lrf_perc < 100:
                lrf_color = '#ffc187'
            else:
                lrf_color = '#b3ff87'

        return lrf_color

    def open_instr(instructionList, module, serverInstr):
        cesta = serverInstr + module.split('-')[0].replace('M','M ') + '/'
        for file in os.listdir(cesta):
            if file.endswith('.pdf'):
                try:
                    fileNr = file.split('-')[1].split('_')[0].replace(' ','')
                    if int(fileNr) in instructionList:
                        webbrowser.open_new('file:' + os.path.join(cesta, file))
                except ValueError:
                    continue
                except IndexError:
                    continue

    def app_running():
        n = 0
        for p in psutil.process_iter(attrs=['pid', 'name']):
            if p.info['name'] == 'production.exe':
                n = n + 1
                if n > 2:
                    ctypes.windll.user32.MessageBoxW(0, 'Error 0x204 App is already running' , 'Error', 0x1000)
                    exit(0)


class ITAC:
    def login():
        body = """{"sessionValidationStruct":
                    {"stationNumber":""" + stationNumber + """,
                    "stationPassword":"",
                    "user":"",
                    "password":"",
                    "client":"01",
                    "registrationType":"S",
                    "systemIdentifier":"Test"}}"""
        req = requests.post(restAPI + login, headers=headers, data=body, timeout=tmout)

        if req.status_code != 200:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x301 iTAC regLogin problem ' + str(req.status_code), 'iTAC Message', 0x1000)

        js = (req.text).replace(' ','').replace('\r\n','').replace('{"result":{"return_value":0','').split(',')
        sessionId = js[1].replace('sessionContext":{','').split(':')[1]

        persId = js[2].split(':')[1]

        locale = js[3].replace('}}}','').replace('"','').split(':')[1]

        return sessionId, persId, locale

    def check0(sn):
        body = """{"sessionContext":
                    {"sessionId":""" + sessionId + """,
                    "persId":""" + '"' + persId + '"' + """,
                    "locale":""" + '"' + locale + '"' + """},
                    "stationNumber":""" + stationNumber + """,
                    "serialNumber":""" + '"' + sn + '"' + """,
                    "serialNumberPos":"-1",
                    "serialNumberResultKeys": ["PART_NUMBER","PART_DESC","WORKORDER_NUMBER","SERIAL_NUMBER_POS"]}"""
        req = requests.post(restAPI + check0, headers=headers, data=body, timeout=tmout)
        if req.status_code != 200:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x302 iTAC trGetSerialNumberInfo problem ' + str(req.status_code), 'iTAC Message', 0x1000)

        data = req.text.replace(' ','').replace('\r\n','').replace('"','').split(',')
        ITAC_part_no = str(data[1]).split('[')[1]
        ITAC_part_desc = str(data[2])
        ITAC_WA = str(data[3])
        ITAC_sn_pos = str(data[4].split(']')[0])

        return ITAC_part_no, ITAC_part_desc, ITAC_WA, ITAC_sn_pos

    def check1(sn):
        body = """{"sessionContext":
                    {"sessionId":""" + sessionId + """,
                    "persId":""" + '"' + persId + '"' + """,
                    "locale":""" + '"' + locale + '"' + """},
                    "stationNumber":""" + stationNumber + """,
                    "processLayer":"-1",
                    "checkMultiBoard":"0",
                    "serialNumber":""" + '"' + sn + '"' + """,
                    "serialNumberPos":"-1",
                    "serialNumberStateResultKeys": ["ERROR_CODE"]}"""
        req = requests.post(restAPI + check1, headers=headers, data=body, timeout=tmout)
        if req.status_code != 200:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x303 iTAC trCheckSerialNumberState problem ' + str(req.status_code), 'iTAC Message', 0x1000)
        status = req.text.replace(' ','').replace('\r\n','').split(',')[1]
        status = status.replace('"','').replace('}','').replace('[','').replace(']','').split(':')[1]
        if status != '0' and status != '212':
            ctypes.windll.user32.MessageBoxW(0, 'iTAC AOI ' + status, 'iTAC Message', 0x1000)

        return status

    def upload(stationNumber, sn, itac_pos, testresult, cycle_time, uploadvalues):
        body = """{"sessionContext":
                    {"sessionId":""" + sessionId + """,
                    "persId":""" + '"' + persId + '"' + """,
                    "locale":""" + '"' + locale + '"' + """},
                    "stationNumber":""" + stationNumber + """,
                    "processLayer":0,
                    "recipeVersionId":-1,
                    "serialNumberRef":""" + '"' + sn + '"' + """,
                    "serialNumberRefPos":""" + '"' + itac_pos + '"' + """,
                    "serialNumberState":""" + testresult + """,
                    "duplicateSerialNumber":0,
                    "bookDate":-1,
                    "cycleTime":""" + cycle_time + """,
                    "recipeVersionMode":0,
                    "resultUploadKeys": ["MEASURE_TYPE","ERROR_CODE","MEASURE_FAIL_CODE","UNIT","MEASURE_NAME","MEASURE_VALUE","LOWER_LIMIT","UPPER_LIMIT","TEST_STEP_NUMBER"],
                    "resultUploadValues": [""" + uploadvalues + """]}"""
        req = requests.post(restAPI + upload, headers=headers, data=body, timeout=tmout)
        if req.status_code != 200:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x304 iTAC trUploadResultDataAndRecipe problem ' + str(req.status_code), 'iTAC Message', 0x1000)

    def logout():
        body = """{"sessionContext":
                    {"sessionId":""" + sessionId + """,
                    "persId":""" + '"' + persId + '"' + """,
                    "locale":""" + '"' + locale + '"' + """}}"""
        req = requests.post(restAPI + logout, headers=headers, data=body, timeout=tmout)
        if req.status_code != 200:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x305 iTAC regLogout problem ' + str(req.status_code), 'iTAC Message', 0x1000)


class file_handler:
    def rexxam_handle(threadn):
        while run:
            time.sleep(0.001)
            ##We dont want to crash if the production doesnt run
            ##This ll crash only till the production start
            try:
                date = str(datetime.date.today()).replace('-','') + '\\'
                if len(os.listdir(path=PATH + date)) > 0:
                    try:
                        start_time = time.time()
                        ########################################################
                        tLock.acquire()
                        ########################################################
                        ##Main function definition
                        ########################################################
                        count = 0
                        uploadvalues = ''
                        numberofrecords = 0
                        name_prev = ''
                        name_a = 0
                        name_b = 0
                        name_c = 0
                        name_d = 0
                        name_e = 0

                        newest = max(glob.iglob(PATH + date + '*.[Dd][Aa][Tt]'), key=os.path.getctime)

                        with open(newest, 'r') as fileopened:
                            data = fileopened.read(-1)
                            data = data.splitlines()
                            size = len(data)

                        if remove_file == True:
                            split_path = newest.rsplit('\\', 1)
                            os.replace(newest, split_path[0][:-8] + '\\PROBLEMS\\' + str(start_time) + split_path[1])

                        tLock.release()

                        result_data = data[0].split(',')
                        if 'OK' in result_data[8] and 'OK' in result_data[9]:
                            testresult = '0'
                            status = 'pass'
                        else:
                            testresult = '1'
                            status = 'fail'

                        sn = data[0].split(',')
                        sn = sn[5] + sn[4] + 'E9'

                        if dbtype == 'ITAC':
                            if ITAC.check1(sn) != '0' and ITAC.check1(sn) != '212':
                                continue

                            itac_data = ITAC.check0(sn)
                            itac_wa = itac_data[2]
                            itac_desc = itac_data[1]
                            itac_pos = itac_data[3]

                            for x in range(size):
                                raw_data = data[x].replace(' ','').split(',')
                                if 'CP=' not in raw_data[9]:
                                    name = raw_data[1].replace('MR','R').replace('MC','C')
                                    value = raw_data[13]
                                    unit = raw_data[14]

                                    if raw_data[15] == '*PASS*':
                                        measfailcode = '0'
                                    elif raw_data[15] == '':
                                        continue
                                    else:
                                        measfailcode = '1'

                                    if name == 'T1':
                                        name = name + '_' + str(name_a)
                                        name_a += 1

                                    if name == 'XT801M':
                                        name = name + '_' + str(name_b)
                                        name_b += 1

                                    if name == 'XT1M':
                                        name = name + '_' + str(name_c)
                                        name_c += 1

                                    if name == 'DB101':
                                        name = name + '_' + str(name_d)
                                        name_d += 1

                                    if 'IC' in name:
                                        name = name + '_' + str(name_e)
                                        name_e += 1

                                    if name == name_prev:
                                        name += '_1'

                                    if str(raw_data[13]) == '':
                                        value = '0'

                                    if '%' in raw_data[10]:
                                        hlimit = int(value.split('.')[0]) + (int(value.split('.')[0]) / 100 * int(raw_data[9].split('.')[0]))
                                    else:
                                        hlimit = raw_data[9]

                                    if '%' in raw_data[12]:
                                        llimit = int(value.split('.')[0]) + (int(value.split('.')[0]) / 100 * int(raw_data[11].split('.')[0]))
                                    else:
                                        llimit = raw_data[11]

                                    unit_format = str(unit[:1]).replace('M','E+6').replace('G','E+9').replace('K','E+3').replace('m','E-3').replace('u','E-6').replace('n','E-9').replace('p','E-12')

                                    if 'o' in unit[-1:]:
                                        unit = 'Ohm'
                                    elif 'F' in unit[-1:]:
                                        unit = 'F'
                                    elif 'V' in unit[-1:]:
                                        unit = 'V'
                                    elif 'A' in unit[-1:]:
                                        unit = 'A'
                                    else:
                                        unit = ''

                                    if len(unit_format) <= 1:
                                        unit_format = ''

                                    name_prev = name

                                    numberofrecords += 1

                                    uploadvalues += ',"T",0,"' + measfailcode + '","' + str(unit) + '","' + str(name) + '","' + str(value) + '","' + str(llimit) + '","' + str(hlimit) + '",' + str(numberofrecords)

                            uploadvalues = uploadvalues.replace(',', '', 1)

                            if dbtype == 'ITAC':
                                ITAC.upload(stationNumber, sn, itac_pos, testresult, '20', uploadvalues)
                            SESO.upload(itac_desc, stationNumber, itac_wa, status, sn)

                            if useSESO == False:
                                global pass_count
                                global fail_count

                                if status == 'pass':
                                    pass_count += 1
                                else:
                                    fail_count += 1

                        if remove_file == True:
                            os.remove(split_path[0][:-8] + '\\PROBLEMS\\' + str(start_time) + split_path[1])

                    except ValueError:
                        try:
                            if 'max' in str(sys.exc_info()):
                                tLock.release()
                                continue
                            else:
                                ctypes.windll.user32.MessageBoxW(0, 'Error 0x101 ' + str(sys.exc_info()), 'Error', 0x1000)
                                tLock.release()
                                continue
                        except ValueError:
                            continue

                    except PermissionError:
                        try:
                            tLock.release()
                            continue
                        except ValueError:
                            continue

                    except UnboundLocalError:
                        try:
                            ctypes.windll.user32.MessageBoxW(0, 'Error 0x103 ' + str(sys.exc_info()), 'Error', 0x1000)
                            tLock.release()
                            continue
                        except ValueError:
                            continue

                    except FileNotFoundError:
                        try:
                            tLock.release()
                            continue
                        except ValueError:
                            continue

                    except IndexError:
                        try:
                            ctypes.windll.user32.MessageBoxW(0, 'Error 0x105 ' + str(sys.exc_info()), 'Error', 0x1000)
                            tLock.release()
                            continue
                        except ValueError:
                            continue

                    except:
                        try:
                            ctypes.windll.user32.MessageBoxW(0, 'Error 0x100 ' + str(sys.exc_info()), 'Error', 0x1000)
                            tLock.release()
                            continue
                        except ValueError:
                            continue

                    finally:
                        if threadn == '0':
                            global tr0
                            tr0 = str(time.time() - start_time)[:5]
                        elif threadn == '1':
                            global tr1
                            tr1 = str(time.time() - start_time)[:5]
                        elif threadn == '2':
                            global tr2
                            tr2 = str(time.time() - start_time)[:5]
                        elif threadn == '3':
                            global tr3
                            tr3 = str(time.time() - start_time)[:5]
                        elif threadn == '4':
                            global tr4
                            tr4 = str(time.time() - start_time)[:5]
                        elif threadn == '5':
                            global tr5
                            tr5 = str(time.time() - start_time)[:5]
                        elif threadn == '6':
                            global tr6
                            tr6 = str(time.time() - start_time)[:5]
                        elif threadn == '7':
                            global tr7
                            tr7 = str(time.time() - start_time)[:5]
            except FileNotFoundError:
                continue
        exit(0)

    def stdf_handle(threadn):
        while run:
            time.sleep(0.001)
            if len(os.listdir(path=PATH)) > 1:
                try:
                    start_time = time.time()
                    ########################################################
                    tLock.acquire()
                    ########################################################
                    ##Main function definition
                    ########################################################
                    comp = 0
                    start_array = {}
                    times = {}
                    name_prev = ''
                    count = 0
                    time_count = 0

                    newest = max(glob.iglob(PATH + '*.[TtLl][XxOo][TtGg]'), key=os.path.getctime)

                    with open(newest, 'r') as fileopened:
                        data = fileopened.read(-1)
                        data = data.splitlines()
                        size = len(data)

                    if remove_file == True:
                        split_path = newest.rsplit('\\', 1)
                        os.replace(newest, split_path[0] + '\\PROBLEMS\\' + str(start_time) + split_path[1])
                    ########################################################
                    tLock.release()
                    ########################################################

                    for x in range(size):
                        if '@' in data[x]:
                            start_number = x
                            break

                    for x in range(size):
                        if any ( ['"' in data[x], '/' in data[x] and ('/P' not in data[x] and 'P/N' not in data[x] and '/S' not in data[x] and '/W' not in data[x])]):
                            start_array[count] = x + 1
                            count = count + 1

                    for i in range(count):
                        uploadvalues = ''
                        numberofrecords = 0
                        contact_c = 0
                        if start_number > start_array[i]:
                            start_array[i] = len(data)

                        for x in range(start_number, start_array[i]):
                            if any( ['<' in data[x], '>' in data[x]]):
                                testresult = '1'
                                status = 'fail'
                                break
                            else:
                                testresult = '0'
                                status = 'pass'

                        for x in range(start_number, start_array[i]):
                            if 'SN ' in data[x]:
                                sn = data[x].split(' ')
                                sn = sn[4]
                                if '_' not in sn:
                                    sn = sn + '_1'
                                    multipanel = False
                                else:
                                    multipanel = True
                                sn = sn.split('_')
                                pos = sn[1]
                                sn = sn[0]
                                break
                            elif 'SERIALNUMBER' in data[x]:
                                sn = data[x].split(' ')
                                sn = sn[1]
                                if '_' not in sn:
                                    sn = sn + '_1'
                                    multipanel = False
                                else:
                                    multipanel = True
                                sn = sn.split('_')
                                pos = sn[1]
                                sn = sn[0]
                                break
                            else:
                                sn = ''

                        if sn == '':
                            ctypes.windll.user32.MessageBoxW(0, 'Error 0x106 DMX read error', 'Error', 0x1000)
                            if remove_file == True:
                                os.remove(split_path[0] + '\\PROBLEMS\\' + str(start_time) + split_path[1])
                            continue

                        if dbtype == 'ITAC':
                            if ITAC.check1(sn) != '0' and ITAC.check1(sn) != '212':
                                continue

                            itac_data = ITAC.check0(sn)
                            itac_wa = itac_data[2]
                            itac_desc = itac_data[1]
                            itac_pos = itac_data[3]

                            if any( [itac_desc == 'M830', itac_desc == 'M830-001', itac_desc == 'M830-002', itac_desc == 'M830-003'] ):
                                if int(itac_pos) in range(0, 10):
                                    comp = 0
                                elif int(itac_pos) in range(10, 19):
                                    comp = 9
                                elif int(itac_pos) in range(19, 28):
                                    comp = 18
                                else:
                                    comp = 27

                            elif any( [itac_desc == 'M951', itac_desc == 'M951-001', itac_desc == 'M952', itac_desc == 'M952-001', itac_desc == 'M953', itac_desc == 'M953-001'] ):
                                if int(itac_pos) in range(0, 18):
                                    comp = 0
                                else:
                                    comp = 18

                            elif any( [itac_desc == 'M976-002-HAUPTPL.', itac_desc == 'M976-001-HAUPTPL.'] ):
                                if int(itac_pos) in range(0, 43):
                                    comp = 0
                                else:
                                    comp = 42

                            if len(sn) == 13:
                                sn = sn.strip('AP')
                                if multipanel == True:
                                    sn = int(sn) - int(itac_pos) + comp + int(pos)
                                sn = str(sn)
                                sn = 'AP' + sn.zfill(11)

                            elif len(sn) == 26:
                                snrest = sn[-10:]
                                snnum = sn[:16]
                                sn = int(snnum) - int(itac_pos) + comp + int(pos)
                                sn = str(sn) + str(snrest)

                        for x in range(start_number,start_array[i]):
                            if re.match('.*-.*-.*:.*:.*', data[x]):
                                times[time_count] = data[x]
                                times[time_count] = times[time_count].split(' ')[2]
                                time_count = time_count + 1
                            if any( ['<' in data[x], '=' in data[x], '>' in data[x], '**' in data[x], '~' in data[x]] ):
                                name = re.split('=|<|>', data[x])
                                if '<' in data[x]:
                                    measfailcode = '1'
                                elif '>' in data[x]:
                                    measfailcode = '2'
                                elif '=' in data[x]:
                                    measfailcode = '0'
                                if 'ON MEASURED VALUE' in data[x]:
                                    continue
                                if 'CONTINUITY' in data[x]:
                                    name[0] = 'CONTINUITY_' + str(contact_c) + '=' + data[x + 3].replace('TP','tp').split(' ')[2] + '( , )'
                                    name = name[0].split('=')
                                    contact_c += 1
                                    measfailcode = '1'
                                    testresult = '1'
                                    status = 'fail'
                                if 'OPEN PIN GROUPS' in data[x]:
                                    name[0] += '=' + data[x + 2]
                                    name[0] = name[0].replace('**','').replace('~','').replace('(','').replace('(','').replace(',',':').replace(')','').replace(' OPEN PIN GROUPS ','CONTACT_' + str(contact_c))
                                    name = name[0].split('=')
                                    name[1] = name[1].replace(' ',',',1).replace(' ','')
                                    name[1] = name[1] + '( , )'
                                    contact_c += 1
                                    measfailcode = '1'
                                    testresult = '1'
                                    status = 'fail'
                                if 'NAILS NOT MAKING CONTACT' in data[x]:
                                    name[0] += '=' + data[x + 3]
                                    name[0] = name[0].replace('**','').replace('(','').replace('(','').replace(',',':').replace(')','').replace(' NAILS NOT MAKING CONTACT ','CONTACT_' + str(contact_c)) + '( , )'
                                    name = name[0].split('=')
                                    contact_c += 1
                                    measfailcode = '1'
                                    testresult = '1'
                                    status = 'fail'
                                if 'Shorted Nails' in data[x]:
                                    name[0] += '=' + data[x + 1]
                                    name[0] = name[0].replace('**','').replace('~','').replace('(','').replace('(','').replace(',',':').replace(';','').replace(')','').replace(' Shorted Nails ','SHORT' + str(contact_c)) + '( , )'
                                    name = name[0].split('=')
                                    contact_c += 1
                                    measfailcode = '1'
                                    testresult = '1'
                                    status = 'fail'
                                if len(name) < 2:
                                    continue
                                if name[1] == '':
                                    name[1] = '  ( , )'
                                if name[0] == '':
                                    continue
                                if 'LIMITS' in name[0]:
                                    continue
                                if '(,)' in name[1]:
                                    continue
                                if multipanel == True:
                                    name[0] = name[0].replace('-','_').rsplit('_',1)
                                    name[0] = name[0][0]
                                if 'P/N' in name[0]:
                                    continue
                                if name[0] == name_prev:
                                    name[0] += '_1'
                                if ' ' in name[0]:
                                    continue
                                name_prev = name[0]
                                value = name[1].split('(')
                                value[0] = value[0].replace('MEG','E+6').replace('G','E+9').replace('K','E+3').replace('M','E-3').replace('U','E-6').replace('N','E-9').replace('P','E-12')
                                llimit = value[1].split(',')
                                llimit[0] = llimit[0].replace('MEG','E+6').replace('G','E+9').replace('K','E+3').replace('M','E-3').replace('U','E-6').replace('N','E-9').replace('P','E-12')
                                hlimit = llimit[1].split(')')
                                hlimit[0] = hlimit[0].replace('MEG','E+6').replace('G','E+9').replace('K','E+3').replace('M','E-3').replace('U','E-6').replace('N','E-9').replace('P','E-12')
                                if 'R' in hlimit[1]:
                                    unit = 'Ohm'
                                elif 'C' in hlimit[1]:
                                    unit = 'F'
                                elif 'V' in hlimit[1]:
                                    unit = 'V'
                                elif 'A' in hlimit[1]:
                                    unit = 'A'
                                else:
                                    unit = ''
                                numberofrecords += 1
                                uploadvalues += ',"T",0,"' + measfailcode + '","' + unit + '","' + name[0] + '","' + value[0] + '","' + llimit[0] + '","' + hlimit[0] + '",' + str(numberofrecords)

                        uploadvalues = uploadvalues.replace(',', '', 1)
                        start_number = start_array[i]
                        cycle_time = datetime.datetime.strptime(times[1], '%H:%M:%S') - datetime.datetime.strptime(times[0], '%H:%M:%S')
                        cycle_time = str(cycle_time.total_seconds())

                        if dbtype == 'ITAC':
                            ITAC.upload(stationNumber, sn, itac_pos, testresult, cycle_time, uploadvalues)
                        SESO.upload(itac_desc, stationNumber, itac_wa, status, sn)

                    ##End of main function definition
                    ########################################################
                        if useSESO == False:
                            global pass_count
                            global fail_count

                            if status == 'pass':
                                pass_count += 1
                            else:
                                fail_count += 1

                    if remove_file == True:
                        os.remove(split_path[0] + '\\PROBLEMS\\' + str(start_time) + split_path[1])

                except ValueError:
                    try:
                        if 'max' in str(sys.exc_info()):
                            tLock.release()
                            continue
                        else:
                            ctypes.windll.user32.MessageBoxW(0, 'Error 0x101 ' + str(sys.exc_info()), 'Error', 0x1000)
                            tLock.release()
                            continue
                    except ValueError:
                        continue

                except PermissionError:
                    try:
                        tLock.release()
                        continue
                    except ValueError:
                        continue

                except UnboundLocalError:
                    try:
                        ctypes.windll.user32.MessageBoxW(0, 'Error 0x103 ' + str(sys.exc_info()), 'Error', 0x1000)
                        tLock.release()
                        continue
                    except ValueError:
                        continue

                except FileNotFoundError:
                    try:
                        tLock.release()
                        continue
                    except ValueError:
                        continue

                except IndexError:
                    try:
                        ctypes.windll.user32.MessageBoxW(0, 'Error 0x105 ' + str(sys.exc_info()), 'Error', 0x1000)
                        tLock.release()
                        continue
                    except ValueError:
                        continue

                except:
                    try:
                        ctypes.windll.user32.MessageBoxW(0, 'Error 0x100 ' + str(sys.exc_info()), 'Error', 0x1000)
                        tLock.release()
                        continue
                    except ValueError:
                        continue

                finally:
                    if threadn == '0':
                        global tr0
                        tr0 = str(time.time() - start_time)[:5]
                    elif threadn == '1':
                        global tr1
                        tr1 = str(time.time() - start_time)[:5]
                    elif threadn == '2':
                        global tr2
                        tr2 = str(time.time() - start_time)[:5]
                    elif threadn == '3':
                        global tr3
                        tr3 = str(time.time() - start_time)[:5]
                    elif threadn == '4':
                        global tr4
                        tr4 = str(time.time() - start_time)[:5]
                    elif threadn == '5':
                        global tr5
                        tr5 = str(time.time() - start_time)[:5]
                    elif threadn == '6':
                        global tr6
                        tr6 = str(time.time() - start_time)[:5]
                    elif threadn == '7':
                        global tr7
                        tr7 = str(time.time() - start_time)[:5]
        exit(0)


class HW:
    def rfid_open(COM, BAUD, msg_show):
        try:
            global ser
            ser = serial.Serial(COM, BAUD, timeout=0.5)
            useReader = True
        except serial.serialutil.SerialException:
            if msg_show == 1:
                dec = ctypes.windll.user32.MessageBoxW(0, 'Error 0x203 Reader cannot be found.\rContinue withour reader?', 'HW Error', 0x1001)
                if dec == 1:
                    useReader = False
                else:
                    exit(0)
            else:
                useReader = True

        return useReader

    def rfid_read():
        try:
            ser.write(b'0500100\r')
            serialString = ser.readline()
            if len(serialString) == 21:
                serialString = str(int(serialString.decode('utf-8')[-9:], 16))
            else:
                serialString = '0'
            return serialString

        except serial.serialutil.SerialException:
            HW.rfid_close()
            msg_show = 0
            HW.rfid_open(COM, BAUD, msg_show)
            msg_show = 1

    def rfid_close():
        ser.close()


class SESO:
    def upload(desc, stationNumber, wa, status, sn):
        wa = wa.strip(' ')
        if wa != 'locale':
            if status == 'fail':
                status = '0'
            else:
                status = '1'
            payload = {'type': 'production', 'itac': '0', 'station': stationNumber, 'wa': wa, 'module': desc, 'ap': sn, 'result': status}
            req = requests.post(sesoData1, data=payload, timeout=tmout)

    def updateProdData(stationNumber, mode):
        payload = {'action': 'hourly', 'station': stationNumber}
        req = requests.post(sesoData, data=payload, timeout=tmout)

        data = (req.text).split(',')

        working = int(data[3].split(':')[1]) + int(data[4].split(':')[1])

        testerType = data[0].split(':')[1].replace('"','')

        if 'ICT' in testerType:
            instructionList = [*range(60,64,1)]
        else:
            instructionList = {*range(65,69,1)}

        if working == 0:
            pass_count = 0
            fail_count = 0
            fpy = 0
            fpy_color = '#ff8787'
            module = ''
            lrf = 0
            lrf_color = '#ff8787'
            curr_perf = 0
        else:
            pass_count = int(float(data[3].split(':')[1]))
            fail_count = int(float(data[4].split(':')[1]))
            if '[]' not in data[9]:
                try:
                    fpy = int(float(data[9].split(':')[1]))
                    lrf = int(float(data[10].split(':')[1].replace('"','')))
                except:
                    fpy = 0
                    lrf = 1
            else:
                fpy = 0
                lrf = 1
            fpy_color = support.fpy_color(fpy, mode)
            module = data[2].split(':')[1].replace('"','')
            if fpy > 0:
                curr_perf = int(float(data[14].split(':')[1].replace('"','').replace('}','').replace(']','')))
            else:
                curr_perf = 0
            lrf_color = support.lrf_color(lrf, curr_perf)

        return pass_count, fail_count, fpy, fpy_color, instructionList, module, lrf, lrf_color, curr_perf

    def operatorTraining(serialString, training):
        payload = {'type': 'card', 'id': serialString, 'station': stationNumber}
        req = requests.post(sesoData1, data=payload, timeout=tmout)

        data = (req.text).split(',')
        op_id = data[2].split(':')[1].replace('"','')
        op_name = data[1].split(':')[1].replace('"','') + ' ' + data[0].split(':')[2].replace('"','')
        data = (req.text).split('[')[1].replace('[','').replace(']','').replace('{','').replace('}','').replace('"','').split(',')

        if useTraining == True:
            if len(data) > 1:
                training = 'Training OK'
                unlock = True
            else:
                training = 'Training NOK'
                unlock = False
        else:
            training = 'Turned OFF'
            unlock = True

        return op_id, op_name, unlock, training

    def operatorWithoutReader(stationNumber):
        payload = {'type': 'station-info', 'station': stationNumber}
        req = requests.post(sesoData1, data=payload, timeout=tmout)

        op_id = req.text.split(',')[5].split(':')[1].split('-')[0].replace('"','')
        op_name = req.text.split(',')[4].split(':')[1].split('-')[0].replace('"','')

        if len(op_id) > 1:
            training = 'Secondary'
            unlock = True
        else:
            training = 'Secondary'
            unlock = False

        return op_id ,op_name, training, unlock

    def loginLogout(stationNumber, op_name, op_id, inout):
        payload = {'type': 'operator', 'station': stationNumber, 'perName': op_name, 'perNr': op_id, 'action': inout}
        req = requests.post(sesoData1, data=payload, timeout=tmout)

        if inout == 'IN':
            logged = True
        else:
            logged = False

        return logged


class GUI:
    def config_window():
        def config_exit(*args):
            global run
            global app_exit
            run = False
            app_exit = True

        def config_save(*args):
            global run
            global app_exit

            station_itac = tester_text_input.get(1.0, 'end-1c')

            try:
                config = open('C:\\production\\tester.ini', 'w')
            except FileNotFoundError:
                os.makedirs('C:\\production')
                config = open('C:\\production\\tester.ini', 'w')
            config.write(station_itac)
            config.close()

            try:
                config = open('//fs/gs/IndustrialEngineering/Public/04_Testing/01_APPs/production/Configuration/' + station_itac + '.ini', 'r')
                config.close()
            except FileNotFoundError:
                ctypes.windll.user32.MessageBoxW(0, 'Error 0x003 Config on server not found', 'Error', 0x1000)
                GUI.config_window1(station_itac)

            run = False
            app_exit = False

        config = tkinter.Tk()
        config.title('Dashboard Config')
        config.geometry('200x60')
        config.config(bg = 'white')
        config.anchor('center')
        config.wm_attributes('-toolwindow', 'True')

        exit_button = tkinter.Button(config, text = 'Generate and exit', command = config_save, width = 20, bd = 1, bg = 'white', font = ('Helvetica 9'))
        exit_button.place(x = 25, y = 30)

        tester_text = tkinter.Label(config, text = 'iTAC ID' , font = ('Helvetica 8'), bg = 'white')
        tester_text.place(x = 5, y = 5)
        tester_text_input = tkinter.Text(config, height = 1, width = 10, font = ('Helvetica 8'), bg = 'white')
        tester_text_input.place(x = 120, y = 5)

        config.protocol('WM_DELETE_WINDOW', config_exit)
        while run:
            config.update()
        config.quit()
        config.destroy()
        if app_exit == True:
            exit(0)

    def config_window1(station_itac):
        def config_exit(*args):
            global run
            global app_exit
            run = False
            app_exit = True

        def config_save(*args):
            if str(instruction_var.get()) == '0':
                ins_var = 'True'
            else:
                ins_var = 'False'
            if str(parse_var.get()) == '0':
                par_var = 'True'
            else:
                par_var = 'False'
            if str(reader_var.get()) == '0':
                read_var = 'True'
            else:
                read_var = 'False'
            input_var = iTAC_nr_text_input.get(1.0, 'end-1c')
            input_com = reader_com_text_input.get(1.0, 'end-1c')

            config = open('//fs/gs/IndustrialEngineering/Public/04_Testing/01_APPs/production/Configuration/' + station_itac + '.ini', 'w')
            config.write('############################## Read me ###########################\n'
                         '## Error list: 	0x000 Error in loading of program		##\n'
                         '##		0x001 Config not found				##\n'
                         '##		0x002 Config error				##\n'
                         '##		0x100 General Error in parsing thread		##\n'
                         '##		0x101 Value error in parsing thread		##\n'
                         '## Legacy	0x102 Permission error in parsing thread	##\n'
                         '##		0x103 Unbound error in parsing thread		##\n'
                         '## Legacy	0x104 File not found in parsing thread		##\n'
                         '##		0x105 Index error in parsing thread		##\n'
                         '##		0x106 DMX read error				##\n'
                         '##		0x200 General error in GUI thread		##\n'
                         '##		0x201 Instruction not found			##\n'
                         '##		0x202 Company logo not found			##\n'
                         '##		0x203 Reader not found				##\n'
                         '##		0x204 App is already running			##\n'
                         '##		0x205 SSL Error					##\n'
                         '############################# Main data ##########################\n'
                         'stationNumber=' + input_var + '\n'
                         'dbtype=ITAC\n'
                         'restAPI=http://DUMMY\n'
                         'instrPATH=//DUMMY\n'
                         'instrGEN=//DUMMY\n'
                         'ZAPATH=//DUMMY\n'
                         '\n'
                         '########################## APAG specific #########################\n'
                         'SESO=True\n'
                         'sesoData=https://DUMMY\n'
                         'sesoOperator=https://DUMMY\n'
                         '\n'
                         '######################### LOG folder path ########################\n'
                         '##inside the log folder should be folder PROBLEMS for debug     ##\n'
                         'logPATH=C:\\LOG\\\n'
                         '\n'
                         '############################### HW ###############################\n'
                         '##if hw not used do not delete, just replace COM and BAUD with -##\n'
                         'COM=' + input_com + '\n'
                         'Baud=9600\n'
                         'thread_number=4\n'
                         '\n'
                         '############################ Options #############################\n'
                         'remove_file=' + par_var + '\n'
                         'dashboard=True\n'
                         'parse=' + par_var + '\n'
                         'useReader=' + read_var + '\n'
                         'showInstr=' + ins_var + '\n'
                         'useLogin=' + read_var + '\n'
                         'showInfo=True\n'
                         'useTraining=' + ins_var + '\n'
                         'log_format=teradyne'
                         '\n'
                         '############################ Graphics ############################\n'
                         '##			color_mode=dark/light			##\n'
                         '##			graph=fpy/lrf				##\n'
                         'color_mode=light\n'
                         'greenFPY=98\n'
                         'orangeFPY=95\n'
                         'graphMode=lrf\n'
                         'company_logo=company_logo=\\DUMMY\company.bmp\n')

            config.close()
            global run
            global app_exit
            run = False
            app_exit = False

        config = tkinter.Tk()
        config.title('Dashboard Config')
        config.geometry('200x160')
        config.config(bg = 'white')
        config.anchor('center')
        config.wm_attributes('-toolwindow', 'True')

        instruction_var = tkinter.IntVar()
        parse_var = tkinter.IntVar()
        reader_var = tkinter.IntVar()

        exit_button = tkinter.Button(config, text = 'Generate and exit', command = config_save, width = 20, bd = 1, bg = 'white', font = ('Helvetica 9'))
        exit_button.place(x = 25, y = 125)

        iTAC_nr_text = tkinter.Label(config, text = 'iTAC station_number' , font = ('Helvetica 8'), bg = 'white')
        iTAC_nr_text.place(x = 5, y = 5)
        iTAC_nr_text_input = tkinter.Text(config, height = 1, width = 10, font = ('Helvetica 8'), bg = 'white')
        iTAC_nr_text_input.place(x = 120, y = 5)

        iTAC_nr_text_input.insert(1.0, station_itac)

        reader_com_text = tkinter.Label(config, text = 'Reader port' , font = ('Helvetica 8'), bg = 'white')
        reader_com_text.place(x = 5, y = 25)
        reader_com_text_input = tkinter.Text(config, height = 1, width = 10, font = ('Helvetica 8'), bg = 'white')
        reader_com_text_input.place(x = 120, y = 25)

        ##Control of parse and delete
        parse_text = tkinter.Label(config, text = 'Parse' , font = ('Helvetica 8'), bg = 'white')
        parse_text.place(x = 5, y = 45)
        parse_on = tkinter.Radiobutton(config, variable = parse_var, value = 0, bg = 'white')
        parse_on.place(x = 120, y = 45)
        parse_off = tkinter.Radiobutton(config, variable = parse_var, value = 1, bg = 'white')
        parse_off.place(x = 135, y = 45)

        ##Control of reader and login
        reader_text = tkinter.Label(config, text = 'Use reader/Login' , font = ('Helvetica 8'), bg = 'white')
        reader_text.place(x = 5, y = 65)
        reader_on = tkinter.Radiobutton(config, variable = reader_var, value = 0, bg = 'white')
        reader_on.place(x = 120, y = 65)
        reader_off = tkinter.Radiobutton(config, variable = reader_var, value = 1, bg = 'white')
        reader_off.place(x = 135, y = 65)

        ##Control of instruction and training
        instruction_text = tkinter.Label(config, text = 'Training/Instruction' , font = ('Helvetica 8'), bg = 'white')
        instruction_text.place(x = 5, y = 85)
        instruction_on = tkinter.Radiobutton(config, variable = instruction_var, value = 0, bg = 'white')
        instruction_on.place(x = 120, y = 85)
        instruction_off = tkinter.Radiobutton(config, variable = instruction_var, value = 1, bg = 'white')
        instruction_off.place(x = 135, y = 85)

        config.protocol('WM_DELETE_WINDOW', config_exit)
        while run:
            config.update()
        config.quit()
        config.destroy()
        if app_exit == True:
            exit(0)

    def main():
        ##GUI variables
        ########################################################
        if useSESO == False:
            global pass_count
            global fail_count

        op_id = '0'
        op_name = ''
        training = ''
        pass_count = 0
        fail_count = 0
        fpy = 0
        lrf = 0
        graph = 0
        locktimeout = 0
        fpy_color = '#ff8787'
        lrf_color = '#ff8787'
        unlock = False
        logged = False
        module_prev = ''
        curr_perf = 0
        primary = False

        global tr0
        global tr1
        global tr2
        global tr3
        global tr4
        global tr5
        global tr6
        global tr7

        global dsh_offset

        tr0 = ''
        tr1 = ''
        tr2 = ''
        tr3 = ''
        tr4 = ''
        tr5 = ''
        tr6 = ''
        tr7 = ''

        if mode == 'light':
            canvasBack = 'white'
            rectBack = '#bda5ca'
            textColor = '#684979'
        elif mode == 'dark':
            canvasBack = '#464359'
            rectBack = '#312C56'
            textColor = '#C2BAFC'
        ########################################################

        top = tkinter.Tk()

        if dashboard == False:
            dsh_offset = 320
        else:
            dsh_offset = 0
        window_width = 400 - dsh_offset
        window_height = 250

        screen_width = int(top.winfo_screenwidth() - window_width)
        screen_height = int(top.winfo_screenheight() - window_height - 40)

        top.title('Dashboard')
        top.geometry(f'{window_width}x{window_height}+{screen_width}+{screen_height}')
        top.config(bg = '#484179')
        top.attributes('-alpha', 0.8)
        top.overrideredirect(True)
        top.anchor('center')

        if useSESO == True:
            lock = tkinter.Tk()
            lock.geometry()
            lock.config(bg = 'white')
            lock.attributes('-alpha', 0.8)
            lock.overrideredirect(True)
            lock.anchor('center')

            lock_text = tkinter.Label(lock, text = training , font = ('Helvetica 40 bold'), bg = 'white')
            lock_text.place(x = screen_width / 2, y = screen_height / 2)

        c = tkinter.Canvas(width = 400, height = 250, bg = canvasBack, bd = -2)
        c.create_rectangle(0, 0, 80, 250, tags = 'ch', fill = rectBack, width = 0)
        c.pack()

        def main_exit(*args):
            if dbtype == 'ITAC':
                ITAC.logout()
            if useReader == True:
              HW.rfid_close()
            if useSESO == True and useLogin == True:
                SESO.loginLogout(stationNumber, '', '0', inout = 'OUT')
            global run
            run = False

        def show_instr():
            support.open_instr(instructionList, module, serverInstr)

        def show_general_instr():
            webbrowser.open_new(serverInstrGen)

        def minimize(*args):
            global dsh_offset
            if dsh_offset == 320:
                dsh_offset = 0
            else:
                dsh_offset = 320

            window_width = 400 - dsh_offset
            window_height = 250
            screen_width = int(top.winfo_screenwidth() - window_width)
            screen_height = int(top.winfo_screenheight() - window_height - 40)
            top.geometry(f'{window_width}x{window_height}+{screen_width}+{screen_height}')

            c.coords(APP_ALIVE, 390 - dsh_offset, 0, 400 - dsh_offset, 10)
            c.coords(APP_MINIMIZE, 380 - dsh_offset, 0, 390 - dsh_offset, 10)

            c.pack()

        ##Left side
        ########################################################
        if showInfo == True:
            TC = tkinter.Label(top, text = 'Thread no:', bg = rectBack, font = ('Helvetica 7'), fg = textColor)
            TC.place(x = 3, y = 0)

            TCN = tkinter.Label(top, text = thread_number, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
            TCN.place(x = 62, y = 15)

            TT = tkinter.Label(top, text = 'Thread time:', bg = rectBack, font = ('Helvetica 7'), fg = textColor)
            TT.place(x = 3, y = 30)

            DB = tkinter.Label(top, text = 'DB type:', bg = rectBack, font = ('Helvetica 7'), fg = textColor)
            DB.place(x = 3, y = 170)

            TCN = tkinter.Label(top, text = dbtype, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
            TCN.place(x = 52, y = 185)

        instr_button = tkinter.Button(top, text = 'Instruction', command = show_instr, width = 9, bd = 0, bg = textColor, font = ('Helvetica 9'), fg = rectBack)
        instr_button.place(x = 5, y = 224)

        gen_instr_button = tkinter.Button(top, text = 'General ins.', command = show_general_instr, width = 9, bd = 0, bg = textColor, font = ('Helvetica 9'), fg = rectBack)
        gen_instr_button.place(x = 5, y = 201)

        APP_ALIVE = c.create_rectangle(390 - dsh_offset, 0, 400 - dsh_offset, 10, tags = 'APP_ALIVE')
        c.tag_bind('APP_ALIVE', '<Button-1>', main_exit)

        APP_MINIMIZE = c.create_rectangle(380 - dsh_offset, 0, 390 - dsh_offset, 10, tags = 'APP_MINIMIZE')
        c.tag_bind('APP_MINIMIZE', '<Button-1>', minimize)
        c.itemconfig(APP_MINIMIZE, fill = '#C2BAFC', outline = 'black')

        ##Right side
        ########################################################
        if dashboard == True:
            APP_NAME = tkinter.Label(top, text = 'Production Dashboard', bg = canvasBack, font = ('Helvetica 10'), fg = textColor)
            APP_NAME.place(x = 240, y = 10, anchor = 'center')

            TOTAL_PCBS = tkinter.Label(top, text = 'Total: ' + str(pass_count + fail_count), bg = canvasBack, font = ('Helvetica 8'), fg = textColor)
            PASS_PCBS = tkinter.Label(top, text = 'Passed: ' + str(pass_count), bg = canvasBack, font = ('Helvetica 8'), fg = textColor)
            FAIL_PCBS = tkinter.Label(top, text = 'Failed: ' + str(fail_count), bg = canvasBack, font = ('Helvetica 8'), fg = textColor)

            if graphMode == 'fpy':
                PASS_BASE = c.create_oval(110, 55, 260, 205, fill = rectBack, outline = '')
                PASS_RATE = c.create_arc(110, 55, 260, 205, start = 0, extent = 360, fill = textColor, outline = '')
                middle_RATE = c.create_oval(140, 85, 230, 175, fill = canvasBack, outline = '')

                FPY = tkinter.Label(top, text = str(fpy) + '%', bg = canvasBack, font = ('Helvetica 14 bold'), fg = textColor)
                FPY.place(x = 187, y = 130, anchor = 'center')

                TOTAL_PCBS.place(x = 270, y = 105)
                PASS_PCBS.place(x = 270, y = 120)
                FAIL_PCBS.place(x = 270, y = 135)

            elif graphMode == 'lrf':
                lrf_back = c.create_rectangle(119, 59, 361, 101, tags = 'ch', fill = rectBack, width = 0)
                lrf_front = c.create_rectangle(120, 60, 270, 100, tags = 'ch', fill = textColor, width = 0)
                PASS_BASE = c.create_rectangle(119, 159, 361, 201, tags = 'ch', fill = rectBack, width = 0)
                PASS_RATE = c.create_rectangle(120, 160, 270, 200, tags = 'ch', fill = textColor, width = 0)

                LRF = tkinter.Label(top, text = 'LRF', bg = canvasBack, font = ('Helvetica 12 bold'), fg =  textColor)
                LRF.place(x = 100, y = 80, anchor = 'center')

                FPY = tkinter.Label(top, text = 'FPY', bg = canvasBack, font = ('Helvetica 12 bold'), fg =  textColor)
                FPY.place(x = 100, y = 180, anchor = 'center')

                if useSESO == True:
                    LRF_number = tkinter.Label(top, text = 'LRF: ' + str(lrf), bg = canvasBack, font = ('Helvetica 8'), fg =  textColor)
                    LRF_number.place(x = 150, y = 105)
                    perf_number = tkinter.Label(top, text = 'PERF: ' + str(curr_perf), bg = canvasBack, font = ('Helvetica 8'), fg =  textColor)
                    perf_number.place(x = 150, y = 120)

                FPY_number = tkinter.Label(top, text = 'FPY: ' + str(fpy) + '%', bg = canvasBack, font = ('Helvetica 8'), fg =  textColor)
                FPY_number.place(x = 150, y = 135)

                TOTAL_PCBS.place(x = 270, y = 105)
                PASS_PCBS.place(x = 270, y = 120)
                FAIL_PCBS.place(x = 270, y = 135)

            if useSESO == True:
                Operator = tkinter.Label(top, text = op_id, bg = canvasBack, font = ('Helvetica 14'), fg = textColor)
                Operator.place(x = 240, y = 30, anchor = 'center')
                Training = tkinter.Label(top, text = training, bg = canvasBack, font = ('Helvetica 6'), fg = textColor)
                Training.place(x = 240, y = 45, anchor = 'center')

            if company_logo != 'False':
                try:
                    img = Image.open(company_logo)
                    img = img.resize((75,45))
                    photoImg =  ImageTk.PhotoImage(img)
                    logo = tkinter.Label(top , image = photoImg , height = 45 , width = 75 , borderwidth = 0)
                    logo.place(x = 323 , y = 203)
                except FileNotFoundError:
                    ctypes.windll.user32.MessageBoxW(0, 'Error 0x202 Image not found. Please check image name.', 'Error', 0x1000)

        D0 = tkinter.Label(top, text = tr0, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D0.place(x = 48, y = 45)
        D1 = tkinter.Label(top, text = tr1, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D1.place(x = 48, y = 60)
        D2 = tkinter.Label(top, text = tr2, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D2.place(x = 48, y = 75)
        D3 = tkinter.Label(top, text = tr3, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D3.place(x = 48, y = 90)
        D4 = tkinter.Label(top, text = tr4, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D4.place(x = 48, y = 105)
        D5 = tkinter.Label(top, text = tr5, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D5.place(x = 48, y = 120)
        D6 = tkinter.Label(top, text = tr6, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D6.place(x = 48, y = 135)
        D7 = tkinter.Label(top, text = tr7, bg = rectBack, font = ('Helvetica 7'), fg = textColor)
        D7.place(x = 48, y = 150)

        def change_color():
            current_color = c.itemcget(APP_ALIVE, 'fill')

            if current_color == 'black':
                c.itemconfig(APP_ALIVE, fill = '#C2BAFC')
            else:
                c.itemconfig(APP_ALIVE, fill = 'black')

        def update_perf(mode):
            if useSESO == False:
                global pass_count
                global fail_count

            if useSESO == True:
                pass_count, fail_count, fpy, fpy_color, instructionList, module, lrf, lrf_color, curr_perf = SESO.updateProdData(stationNumber, mode)
            if pass_count + fail_count > 0:
                graph = ((pass_count + fail_count) - fail_count) / (pass_count + fail_count) * 100
                if useSESO == True:
                    if graphMode == 'fpy':
                        c.itemconfig(PASS_RATE, extent = 360 / 100 * fpy - 0.01)
                    elif graphMode == 'lrf':
                        if curr_perf > lrf:
                            c.coords(lrf_front, 120, 60, 360, 100)
                        else:
                            c.coords(lrf_front, 120, 60, 120 + (240/lrf * curr_perf), 100)
                        c.coords(PASS_RATE, 120, 160, 120 + (240/100 * fpy), 200)
                        c.itemconfig(lrf_front, fill = lrf_color)
                        c.itemconfig(PASS_RATE, fill = fpy_color)
                        c.pack()
                else:
                    if graphMode == 'fpy':
                        c.itemconfig(PASS_RATE, extent = 360 / 100 * graph - 0.01)
                    elif graphMode == 'lrf':
                        c.coords(lrf_front, 120, 60, 120, 100)
                        c.coords(PASS_RATE, 120, 160, 120 + (240/100 * fpy), 200)
                        c.itemconfig(PASS_RATE, fill = fpy_color)
            else:
                graph = 0
            if useSESO == False and graphMode == 'fpy':
                fpy = int(graph)
                fpy_color = support.fpy_color(fpy, mode)

            return pass_count, fail_count, fpy, graph, fpy_color, instructionList, module, lrf, lrf_color, curr_perf

        def operator_perf_graph():
            TOTAL_PCBS.config(text = 'Total: ' + str(pass_count + fail_count))
            PASS_PCBS.config(text = 'Passed: ' + str(pass_count))
            FAIL_PCBS.config(text = 'Failed: ' + str(fail_count))

            if graphMode == 'fpy':
                FPY.config(text = str(fpy) + '%', fg = fpy_color)
            elif graphMode == 'lrf':
                FPY_number.config(text = 'FPY: ' + str(fpy) + '%')
                LRF_number.config(text = 'LRF: ' + str(lrf))
                perf_number.config(text = 'PERF: ' + str(curr_perf))

            Operator.config(text = op_id)
            Training.config(text = training)
            lock_text.config(text = training)

        def system_perf_graph():
            D0.config(text = tr0)
            D1.config(text = tr1)
            D2.config(text = tr2)
            D3.config(text = tr3)
            D4.config(text = tr4)
            D5.config(text = tr5)
            D6.config(text = tr6)
            D7.config(text = tr7)

        def screenLock():
            top.attributes('-topmost', 0)
            lock.geometry(f'{int(top.winfo_screenwidth())}x{int(top.winfo_screenheight())}')
            lock.attributes('-topmost', 1)

        def screenUnlock():
            lock.geometry('0x0')
            lock.attributes('-topmost', 0)
            top.attributes('-topmost', 1)

        top.protocol('WM_DELETE_WINDOW', main_exit)
        while run:
            try:
                change_color()
                if dashboard == True:
                    pass_count, fail_count, fpy, graph, fpy_color, instructionList, module, lrf, lrf_color, curr_perf = update_perf(mode)
                    operator_perf_graph()
                    if useSESO == True:
                        if useReader == True:
                            try:
                                serialString = HW.rfid_read()
                                if len(serialString) >= 4:
                                    op_id, op_name, unlock, training = SESO.operatorTraining(serialString, training)
                                    if showInstr == True:
                                        if module != module_prev:
                                            show_instr()
                                        module_prev = module
                                    if unlock == True and useLogin == True:
                                        if logged == False:
                                            logged = SESO.loginLogout(stationNumber, op_name, op_id, inout = 'IN')
                                            screenUnlock()
                                            primary = True
                                        locktimeout = 10
                                else:
                                    training = 'Card disconnected'
                                    op_id = str(locktimeout)
                                    if locktimeout > 0:
                                        locktimeout -= 1
                                        screenUnlock()
                                    if locktimeout == 0:
                                        screenLock()
                                        if useLogin == True and logged == True:
                                            logged = SESO.loginLogout(stationNumber, op_name, '0', inout = 'OUT')
                                            primary = False
                                if primary == False:
                                    op_id, op_name, training, unlock = SESO.operatorWithoutReader(stationNumber)
                                    if showInstr == True:
                                        if module != module_prev:
                                            show_instr()
                                        module_prev = module
                                    if useLogin == True:
                                        if unlock == True:
                                            if logged == False:
                                                logged = SESO.loginLogout(stationNumber, op_name, op_id, inout = 'IN')
                                                screenUnlock()
                                            locktimeout = 10
                                        else:
                                            training = 'Not logged in'
                                            screenLock()
                                            if logged == True:
                                                logged = SESO.loginLogout(stationNumber, op_name, '0', inout = 'OUT')
                                    else:
                                        screenUnlock()
                            except TypeError:
                                time.sleep(1)
                                training = 'Card reader error'
                                screenLock()
                        else:
                            op_id, op_name, training, unlock = SESO.operatorWithoutReader(stationNumber)
                            if showInstr == True:
                                if module != module_prev:
                                    show_instr()
                                module_prev = module
                            if useLogin == True:
                                if unlock == True:
                                    if logged == False:
                                        logged = SESO.loginLogout(stationNumber, op_name, op_id, inout = 'IN')
                                        screenUnlock()
                                    locktimeout = 10
                                else:
                                    training = 'Not logged in'
                                    screenLock()
                                    if logged == True:
                                        logged = SESO.loginLogout(stationNumber, op_name, '0', inout = 'OUT')
                            else:
                                screenUnlock()
                else:
                    screenUnlock()
                system_perf_graph()
                top.update()
                if useReader == False or useSESO == False:
                    time.sleep(1)
            except FileNotFoundError:
                ctypes.windll.user32.MessageBoxW(0, 'Error 0x201 Instruction not found.', 'Error', 0x1000)
                continue
            except requests.exceptions.SSLError:
                ctypes.windll.user32.MessageBoxW(0, 'Error 0x205 SSL Error.', 'Error', 0x1000)
                continue
            except IOError:
                if useSESO == True:
                    if useLogin == True and logged == True:
                        logged = SESO.loginLogout(stationNumber, '', '0', inout = 'OUT')
                continue
            except tkinter.TclError:
                main_exit()
            except:
                ctypes.windll.user32.MessageBoxW(0, 'Error 0x200' + str(sys.exc_info()), 'Error', 0x1000)
                continue
        top.quit()
        top.destroy()
        exit(0)


def main():
    ##Global variables
    ########################################################
    global sessionId
    global persId
    global locale
    global stationNumber
    global dbtype
    global PATH
    global thread_number
    global restAPI
    global remove_file
    global dashboard
    global sesoData
    global sesoData1
    global useSESO
    global parse
    global useReader
    global greenFPY
    global orangeFPY
    global COM
    global BAUD
    global mode
    global serverInstr
    global showInstr
    global graphMode
    global useLogin
    global company_logo
    global showInfo
    global run
    global useTraining
    global serverInstrGen
    global ZAPATH

    run = True
    ########################################################

    try:
        support.app_running()

        msg_show = 1

        try:
            stationNumber, dbtype, PATH, thread_number, restAPI, remove_file, dashboard, sesoData, useSESO, parselog, useReader, COM, BAUD, greenFPY, orangeFPY, mode, serverInstr, showInstr, graphMode, useLogin, company_logo, showInfo, sesoData1, useTraining, log_format, serverInstrGen, ZAPATH = support.read_config()
        except FileNotFoundError:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x001 Config not found', 'Error', 0x1000)
            GUI.config_window()
            stationNumber, dbtype, PATH, thread_number, restAPI, remove_file, dashboard, sesoData, useSESO, parselog, useReader, COM, BAUD, greenFPY, orangeFPY, mode, serverInstr, showInstr, graphMode, useLogin, company_logo, showInfo, sesoData1, useTraining, log_format, serverInstrGen, ZAPATH = support.read_config()
            run = True
        except:
            ctypes.windll.user32.MessageBoxW(0, 'Error 0x002 Config error', 'Error', 0x1000)

        if useReader == True:
            useReader = HW.rfid_open(COM, BAUD, msg_show)

        if useSESO == False:
            useReader == False

        if useSESO == True:
            if useLogin == True:
                SESO.loginLogout(stationNumber, '', '0', inout = 'OUT')

        t0 = threading.Thread(target = GUI.main)
        t0.start()

        if dbtype == 'ITAC':
            sessionId, persId, locale = ITAC.login()

        if thread_number > 8:
            thread_number = 8

        elif thread_number <= 1:
            thread_number = 1

        if parselog == True:
            if thread_number == 1:
                if log_format == 'teradyne':
                    t0 = threading.Thread(target = file_handler.stdf_handle, args = '0')
                elif log_format == 'rexxam':
                    t0 = threading.Thread(target = file_handler.rexxam_handle, args = '0')
                else:
                    ctypes.windll.user32.MessageBoxW(0, 'Error 0x002 Config error', 'Error', 0x1000)
                t0.start()
            else:
                for i in range(1, thread_number):
                    if log_format == 'teradyne':
                        t = threading.Thread(target = file_handler.stdf_handle, args = str(i))
                    elif log_format == 'rexxam':
                        t = threading.Thread(target = file_handler.rexxam_handle, args = str(i))
                    else:
                        ctypes.windll.user32.MessageBoxW(0, 'Error 0x002 Config error', 'Error', 0x1000)
                    t.start()
    except:
        ctypes.windll.user32.MessageBoxW(0, 'Error 0x000 ' + str(sys.exc_info()), 'Error', 0x1000)


if __name__ == '__main__':
    main()

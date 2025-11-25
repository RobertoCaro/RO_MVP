from scapy.all import sniff, IP, TCP, raw
import time

def C4B2D(S):
    D=[0,0,0,0]
    for i in range(4):
        match(S[i]):
            case '0':D[i]=0
            case '1':D[i]=1
            case '2':D[i]=2
            case '3':D[i]=3
            case '4':D[i]=4
            case '5':D[i]=5
            case '6':D[i]=6
            case '7':D[i]=7
            case '8':D[i]=8
            case '9':D[i]=9
            case 'a':D[i]=10
            case 'b':D[i]=11
            case 'c':D[i]=12
            case 'd':D[i]=13
            case 'e':D[i]=14
            case 'f':D[i]=15
    #
    return (D[0]*16+D[1]+D[2]*4096+D[3]*256)


def networker(ShareDataPool, Value):

    #Load skill data
    str_file_skill="skill.txt"
    filelog_skill = open(str_file_skill, "r")
    datalog_skill=filelog_skill.read().split('\n')
    filelog_skill.close()
    skillID=[]
    skillName=[]
    lenskill=len(datalog_skill)

    

    print(lenskill)

    for iskill in range(lenskill):
        #print(datalog_skill[iskill])
        temp=datalog_skill[iskill].split(',')
        skillID.append(int(temp[0]))
        skillName.append(temp[1])
    #Load items data

    def handler(pkt):



        if IP in pkt and TCP in pkt:
            ip_src = pkt[IP].src
            payload = bytes(pkt[TCP].payload)#bytes
            raw = payload.hex()#hex
            raw_bin = ''.join(f'{byte:08b}' for byte in payload)#bin

            SEQ_raw=pkt[TCP].seq#integer
            
            #print(raw)
            #
            ShareDataPool[23] = int(time.time())
            
            if ip_src == "51.79.98.215":
                ShareDataPool[24] = int(time.time())
                
                print("download files")
                return
            else:
                
                if(raw[0:4]=="1a0b"):

                    if(raw[28:32]=="2201"):
                        #print("ocus")
                        if(len(raw)>174):
                            
                            skillID_found=C4B2D(raw[170:174])
                            findskill=0
                            idskillcheck=0
                            while(findskill==0)&(idskillcheck<lenskill):

                                if(skillID[idskillcheck]==skillID_found):
                                    print(skillName[idskillcheck])
                                    if(skillName[idskillcheck]=="SKID_SA_CLASSCHANGE"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=1
                                    elif(skillName[idskillcheck]=="SKID_SA_TAMINGMONSTER"):
                                        print(skillName[idskillcheck])
                                        #ShareDataPool[33]=1
                                    elif(skillName[idskillcheck]=="SKID_NV_TRICKDEAD"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=10#deslogear
                                    elif(skillName[idskillcheck]=="SKID_SA_SUMMONMONSTER"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=2#alarma
                                    elif(skillName[idskillcheck]=="SKID_SA_INSTANTDEATH"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=2#alarma
                                    elif(skillName[idskillcheck]=="SKID_SA_AUTOSPELL"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar
                                    elif(skillName[idskillcheck]=="SKID_MG_ENERGYCOAT"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar
                                    elif(skillName[idskillcheck]=="SKID_PR_MAGNIFICAT"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar
                                    elif(skillName[idskillcheck]=="SKID_KN_AUTOCOUNTER"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar     
                                    elif(skillName[idskillcheck]=="SKID_CR_GRANDCROSS"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar
                                    elif(skillName[idskillcheck]=="SKID_AL_TELEPORT"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=6#ventana cancelar
                                    elif(skillName[idskillcheck]=="SKID_MO_STEELBODY"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=3#cancelar
                                    elif(skillName[idskillcheck]=="SKID_AC_MAKINGARROW"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=4#ventana cancelar
                                    elif(skillName[idskillcheck]=="SKID_AM_PHARMACY"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=5#enter
                                    elif(skillName[idskillcheck]=="SKID_TF_HIDING"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=2#alarma
                                    elif(skillName[idskillcheck]=="SKID_SA_COMA"):
                                        print(skillName[idskillcheck])
                                        ShareDataPool[33]=2#alarma
                                    else:
                                        ShareDataPool[33]=100#alarma
                                    
                                    
                                    findskill=1
                                idskillcheck=idskillcheck+1
                        #SKID_TF_HIDING
                        #salir

                        #SKID_SA_COMA
                        #esperar y recuperarse

                        #SKID_NV_TRICKDEAD
                        #deslogear y logear

                        #SKID_SA_INSTANTDEATH
                        #helearse

                        #SKID_SA_AUTOSPELL
                        #SKID_MG_ENERGYCOAT
                        #SKID_CR_GRANDCROSS
                        #SKID_MO_STEELBODY
                        #SKID_PR_MAGNIFICAT
                        #SKID_SA_AUTOSPELL
                        #cast cancel
                        
                        #SKID_MC_IDENTIFY
                        #SKID_AL_TELEPORT
                        #SKID_AC_MAKINGARROW
                        #SKID_AM_PHARMACY
                        #cancelar de formas distintas




    # Filtrado BPF básico (solo TCP)
    sniff(
        iface="Wi-Fi",
        filter="tcp and (src host 54.39.131.6 or src host 51.79.98.215)",
        prn=handler,
        store=False
    )
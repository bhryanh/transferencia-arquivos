# -*- coding: utf-8 -*-
import struct
import socket
import sys
import threading
import time

def carry_around_add(a, b):
    c = a + b
    return(c &0xffff) + (c>>16)

def checksum(msg):
    s = 0
    for i in range(0,len(msg),2):
        w = ord(msg[i]) + (ord(msg[i+1])<<8)
        s = carry_around_add(s,w)
    return~s &0xffff

def add_syn(str):
    syn = struct.pack('>4B',0xdc,0xc0,0x23,0xc2)
    nova_string = syn + syn + str
    return nova_string

def open_arquivo(nome,modo): #Função para abrir arquivo e selecionar modo
    arq = open(nome,modo)
    if arq:
        return arq
    if not arq:
        return ('Error')

def calc_length(str):
    length = len(str)
    if length % 2 == 0:
        return length,struct.pack('!H',len(str)),str
    elif length % 2 == 1:
        return length,struct.pack('!H',len(str)),(str + struct.pack('>B',0))

def create_quadro(data):
    length,length_bytes,data = calc_length(data)
    chk = struct.pack("@H",0)
    rservd = struct.pack("@H",0)
    quadro = add_syn(chk + length_bytes + rservd + data)
    chk = checksum(quadro)
    return quadro[0:8] + struct.pack("@H",chk) + quadro[10:14+length]


def send_file(arq_name,sock):
    arq = open_arquivo(arq_name,'rb')
    while True:
        dados = arq.read(65000)
        if not dados:
            break
        quadro = create_quadro(dados)
        sock.send(quadro)
    arq.close()
    print("Send Finished!")


def recv_file(arq_name,sock):
    arq = open_arquivo(arq_name,'wb')
    while True:
        try:
            sock.settimeout(3)
            quadro = sock.recv(1)
            if not quadro:
                break
            if quadro == '\xdc':
                quadro = sock.recv(1)
                if not quadro:
                    break
                if quadro == '\xc0':
                    quadro = sock.recv(1)
                    if not quadro:
                        break
                    if quadro == '\x23':
                        quadro = sock.recv(1)
                        if not quadro:
                            break
                        if quadro == '\xc2':
                            quadro = sock.recv(1)
                            if not quadro:
                                break
                            if quadro == '\xdc':
                                quadro = sock.recv(1)
                                if not quadro:
                                    break
                                if quadro == '\xc0':
                                    quadro = sock.recv(1)
                                    if not quadro:
                                        break
                                    if quadro == '\x23':
                                        quadro = sock.recv(1)
                                        if not quadro:
                                            break
                                        if quadro == '\xc2':
                                            chksum = sock.recv(2)
                                            length = sock.recv(2)
                                            rsrvd = sock.recv(2)
                                            length_int = struct.unpack("!H",length)
                                            if(length_int[0] > 0):
                                                dados = sock.recv(length_int[0])
                                                if length_int[0] % 2 == 0:
                                                    quadro_send = '\xdc' + '\xc0' + '\x23' + '\xc2' + '\xdc' + '\xc0' + '\x23' + '\xc2' + chksum + length + rsrvd + dados
                                                else:
                                                    quadro_send = '\xdc' + '\xc0' + '\x23' + '\xc2' + '\xdc' + '\xc0' + '\x23' + '\xc2' + chksum + length + rsrvd + dados + '\x00'
#                                                chk = checksum(quadro_send)
#                                               if(chk == 0):
                                                arq.write(dados)
        except socket.timeout:
            break
    arq.close()
    print("File Received!")


entrada = sys.argv[1]
saida = sys.argv[2]
ip = sys.argv[3]
port = int(sys.argv[4])
mode = sys.argv[5]

if(mode == "passivo"):
    sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = ('',port)
    sock.bind(address)
    sock.listen(1)
    rec,ip = sock.accept()
    print("Conectado com: ")
    print(ip)
    t1 = threading.Thread(target=send_file,args=(entrada,rec,))
    t2 = threading.Thread(target=recv_file,args=(saida,rec,))
    t1.start()
    t2.start()
    rec.close

if(mode == "ativo"):
    sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (ip,port)
    if(sock.connect(address)):
        exit
    print("Conectado com: ")
    print(ip)
    t1 = threading.Thread(target=send_file,args=(entrada,sock,))
    t2 = threading.Thread(target=recv_file,args=(saida,sock,))
    t1.start()
    t2.start()
    sock.close

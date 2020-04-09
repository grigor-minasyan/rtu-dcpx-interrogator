import time, socket, struct, mysql.connector, config
from DCPx_functions import *
from RTU_data import *
recvtimeout = 1

RTU_list = []
# RTU_list = pickle.load(open('./master-server/stored_RTUs.pkl', 'rb'))
# RTU_list.append(RTU_data(id=2, ip='192.168.1.102', port=8888))
RTU_list.append(RTU_data(id=3, ip='192.168.1.103', port=8888))


db_cnx = mysql.connector.connect(user=config.username, password=config.password, database='project6db')
db_cursor = db_cnx.cursor()
db_cursor.execute("SELECT * FROM rtu_list")


for id, ip, port in db_cursor:
    print("%i %s %i" %(id, socket.inet_ntoa(struct.pack('!I', ip)), port))



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('192.168.1.100', 10000)
sock.bind(server_address)

def get_RTU_i(id):
    for i in range(len(RTU_list)):
        if RTU_list[i].id == id:
            return i
    return -1

def listening_thread():
    # function to continuously check for UDP
    timeout = time.time() + recvtimeout
    sock.settimeout(recvtimeout)
    while time.time() < timeout:
        print('\nwaiting to receive message')
        try:
            data, address = sock.recvfrom(1024)
        except:
            continue
        else:
            data_list = bytearray(data)
            print('received %s bytes from %s' % (len(data), address))
            # print(':'.join(x.encode('hex') for x in data))
            # if len(data_list) > 3:
            print(' '.join(hex(i)[2:] for i in bytearray(data_list)))
            if DCP_is_valid_response(data_list):
                if get_RTU_i(data_list[2])  == -1:
                    print("No RTU found with an id of %s" % data_list[2])
                else:
                    rtu = RTU_list[get_RTU_i(data_list[2])]
                    DCP_process_response(data_list,rtu)


# main driver function
if __name__ == '__main__':
    rtu = RTU_list[0]
    buff = bytearray(DCP_buildPoll(3, DCP_op_lookup(DCP_op_name.FUDR)))
    DCP_compress_AA_byte(buff)
    sent = sock.sendto(buff, (rtu.ip, rtu.port))
    print("sending data for RTU %s with array size of %i" %(3, len(buff)))
    listening_thread()

    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("exiting")
    #     exit(0)

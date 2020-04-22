from json import JSONEncoder
# import functools


"""
def compare_Dttimetemphum(item1, item2):
    if item1.year != item2.year:
        return item1.year - item2.year
    elif item1.month != item2.month:
        return item1.month - item2.month
    elif item1.day != item2.day:
        return item1.day - item2.day
    elif item1.hour != item2.hour:
        return item1.hour - item2.hour
    elif item1.minute != item2.minute:
        return item1.minute - item2.minute
    elif item1.second != item2.second:
        return item1.second - item2.second
    else:
        return 0
"""

def get_point_description(rtu_type, display, point):
    if rtu_type == "temp_def_g2":
        if display == 1:
            if (point >= 1 and point <= 8):
                return f"Discrete Alarms {point}"
            elif point <= 16:
                return "Undefined"
            elif point <= 19:
                return f"Controls {point-16}"
            elif point <= 32:
                return "Undefined"
            elif point == 33:
                return "Default configuration"
            elif point == 34:
                return "DIP Switch Config"
            elif point == 35:
                return "MAC Address Not Set"
            elif point == 36:
                return "IP Address Not Set"
            elif point == 37:
                return "LAN Hardware Error"
            elif point == 38:
                return "SNMP Processing Error"
            elif point == 39:
                return "SNMP community error"
            elif point == 40:
                return "LAN TX packet drop"
            elif point <= 48:
                return f"Notification {point-40} failed"
            elif point == 49:
                return "NTP failed"
            elif point == 50:
                return "Undefined"
            elif point == 51:
                return "Serial 1 RcvQ full"
            elif point == 52:
                return "Dynamic memory full"
            elif point == 53:
                return "Unit reset"
            elif point == 54:
                return "DCP poller inactive"
            elif point == 55:
                return "Reserved"
            elif point == 56:
                return "Modbus poller inactive"
            elif point == 57:
                return "DNP3 poller inactive"
            elif point <= 64:
                return "Reserved"
        if display == 2:
            if (point >= 1 and point <= 32):
                return f"Ping Alarms {point}"
            elif point <= 48:
                return f"Derived Alarms {point-32}"
            elif point <= 64:
                return "Undefined"
        if (display >= 3 and display <= 6):
            flag_names = {1:"Minor Under", 2:"Minor Over", 3:"Major Under", 4:"Major Over"}
            is_second_part = (1 if point > 32 else 0)
            if (point-32*is_second_part >= 1 and point-32*is_second_part <= 4):
                return f"Analog {display*2-5+is_second_part} {flag_names[point-32*is_second_part]}"
            elif (point-32*is_second_part >= 9 and point-32*is_second_part <= 16):
                return f"Analog {display*2-5+is_second_part} Control {point-32*is_second_part-8}"
            elif (point-32*is_second_part >= 17 and point-32*is_second_part <= 32):
                return f"Analog {display*2-5+is_second_part} Value {point-32*is_second_part-16}"


            


class Dttimetemphum:
    year = 0
    month = 0
    day = 0
    hour = 0
    minute = 0
    second = 0
    temp = 0
    hum = 0
    def __init__(self,year = 0, month = 0, day = 0, hour = 0, minute = 0, second = 0, temp = 0, hum = 0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.temp = temp
        self.hum = hum
    def __str__(self):
        ret = ""
        ret += str(self.year) + "/" +str(self.month) + "/" +str(self.day) + " "
        ret += str(self.hour) + ":" +str(self.minute) + ":" +str(self.second) + " "
        ret += str(self.temp) + 'C ' + str(self.hum) + '%'
        return ret
    def __eq__(self, other):
        if isinstance(other, Dttimetemphum):
            return (self.year == other.year and self.month == other.month and self.day == other.day and self.hour == other.hour and self.minute == other.minute and self.second == other.second and self.temp == other.temp and self.hum == other.hum)
        return False
    def __hash__(self):
        return hash(tuple([self.year, self.month, self.day, self.hour, self.minute, self.second, self.temp, self.hum]))


class RTU_data:
    def __init__(self, id, ip, port, rtu_type, display_count):
        self.id = id
        self.thresholds = [0,0,0,0]
        self.alarms_binary = 0
        self.prev_alarm_state = 0
        self.current_data = Dttimetemphum()
        self.history = set()
        self.ip = ip
        self.port = port
        self.rtu_type = rtu_type
        self.display_count = display_count
        self.display_data = []


    def set_id(self, id):
        self.id = id

    def set_display_list(self, c):
        self.display_count = c
        for i in range(self.display_count):
            self.display_data.append([])
            for j in range(64):
                self.display_data[i].append(0)
    
    def set_thresholds(self, list):
        for i in range(4):
                self.thresholds[i] = list[i]
    def set_alarms_binary(self, a):
        self.alarms_binary = a
    def add_hist(self, new_data):
        self.history.add(new_data)
        # sorted(self.history, key=functools.cmp_to_key(compare_Dttimetemphum))
    def set_current_data(self, dttimetemphum):
        self.current_data = dttimetemphum
    def set_prev_alarm_state(self, a):
        self.prev_alarm_state = a
    def __str__(self):
        ret = ""
        ret += 'ID: '+str(self.id) + '\n'
        ret += 'Ip: '+str(self.ip) + '\n'
        ret += 'Type: '+str(self.rtu_type) + '\n'
        return ret

from json import JSONEncoder
# import functools


"""
This file contains class declaration for date_time_temperature_humidity as a single class
This also contains class declaration for RTU_data, where it contaions all of the information from RTU.
"""


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

# gets the descriptions for specific types of RTUs, currently it supports only temp_def_g2
def get_point_description(rtu_type, display, point):
    if rtu_type == "temp_def_g2":
        if display == 1:
            if (point >= 1 and point <= 8):
                return f"Discrete Alarm {point}"
            elif point <= 16:
                return "Undefined"
            elif point <= 19:
                return f"Control {point-16}"
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
                return f"Ping Alarm {point}"
            elif point <= 48:
                return f"Derived Alarm {point-32}"
            elif point <= 64:
                return "Undefined"
        if (display >= 3 and display <= 6):
            flag_names = {1:"minor under", 2:"minor over", 3:"major under", 4:"major over"}
            is_second_part = (1 if point > 32 else 0)
            pt = point-32*is_second_part
            if (pt >= 1 and pt <= 4):
                return f"Analog {display*2-5+is_second_part} {flag_names[pt]}"
            elif (pt >= 9 and pt <= 16):
                return f"Analog {display*2-5+is_second_part} Control"
            elif (pt >= 17 and pt <= 32):
                return f"Analog {display*2-5+is_second_part} Value"
        if (display >= 7 and display <= 22):
            flag_names = {1:"minor under", 2:"minor over", 3:"major under", 4:"major over",
                            5:"sensor not detected", 6:"hvac fail", 7:"air flow below normal", 8:"sensor mate not detected"}
            is_second_part = (1 if point > 32 else 0)
            pt = point-32*is_second_part
            if (pt >= 1 and pt <= 8):
                return f"Digital sensor {display*2-5-8+is_second_part} {flag_names[pt]}"
            elif (pt >= 9 and pt <= 16):
                return f"Digital sensor {display*2-5-8+is_second_part} Control"
            elif (pt >= 17 and pt <= 32):
                return f"Digital sensor {display*2-5-8+is_second_part} Value"


            


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
        self.analog_start = 0
        self.analog_end = 0
        self.display_count = display_count
        self.display_data = []
        self.set_display_list(display_count)


    def set_id(self, id):
        self.id = id

    def set_display_list(self, c):
        self.display_data = []
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

    # processes analog values, displayed passed as 1 indexed, works only with temp_def_g2
    def process_analogs(self, display_start, display_end):
        # RTU sends the float values as an int divided by those numbers, so we receive the INT and multiply by those numbers to get the float value.
        ranges = {0:0.001522821, 1:0.003863678, 2:0.008098398, 3:0.018197650, 4:0.023067190, 5:0.034655988, 6:1.000000000, 7:1.000000000}
        display_start -= 1
        display_end -= 1
        for i in range(display_start, display_end + 1):
            for j in range(0, 33, 32):
                self.display_data[i][9+j] = ((self.display_data[i][16+j] << 8) | self.display_data[i][24+j])
                is_enabled = ((1<<7)& self.display_data[i][8+j]) >> 7
                is_negative = (0b01000000 & self.display_data[i][8+j])
                cur_range = (0b00000111 & self.display_data[i][8+j])
                self.display_data[i][9+j] *= (-1 if is_negative else 1) * ranges[cur_range]
                self.display_data[i][9+j] = round(self.display_data[i][9+j], 3)
                self.display_data[i][8+j] = is_enabled

            # for j in range(0, 33, 32):
            #     del self.display_data[i][42-j:64-j]

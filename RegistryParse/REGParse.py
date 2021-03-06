import sys, os
import time
from RegistryParse import decode
import sqlite3
import struct
from RegistryParse.Registry import Registry

# 하이브 파일과 경로를 입력받아 값을 반환하는 함수
# name이 "ALL"이라면 해당 키의 모든 값을 이중리스트로 반환
def get_reg_value(reg, path, name):
    registry = Registry.Registry(reg)
    key = registry.open(path)

    if name == "ALL":
        result = []
        for v in key.values():
            result.append([v.name(), v.value()])
        return result
    else:
        for v in key.values():
            if v.name() == name:
                return v.value()


# 사용중인 ControlSet을 반환합니다. ex) ControlSet001
def get_controlset00n():
    registry = Registry.Registry(sys_reg)
    key = registry.open("Select")
    for v in key.values():
        if v.name() == "Current":
            return "ControlSet00" + str(v.value())


# sid 값을 받아 user명을 반환하는 함수
def sid_to_user(sid):
    registry = Registry.Registry(soft_reg)
    path = "Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\" + sid
    key = registry.open(path)
    user_name = None

    for v in key.values():
        if v.name() == "ProfileImagePath":
            user_name = v.value().rpartition('\\')[2]

    return user_name


# 시스템의 정보를 이중 리스트로 반환하는 함수
def os_info():
    registry = Registry.Registry(soft_reg)
    key = registry.open("Microsoft\\Windows NT\\CurrentVersion")

    product_name = None # 운영체제 이름
    product_ID = None   # 운영체제 식별자
    system_root = None  # 운영체제 설치 루트 폴더
    owner = None    # 사용자 이름
    organization = None # 조직 이름
    install_date = None # 운영체제 설치 날짜(유닉스 시간 형식)
    build_lab = None    # 운영체제 세부 버전

    for v in key.values():
        if v.name() == "ProductName":
            product_name = v.value()
        if v.name() == "ProductId":
            product_ID = v.value()
        if v.name() == "PathName":
            system_root = v.value()
        if v.name() == "RegisteredOwner":
            owner = v.value()
        if v.name() == "RegisteredOrganization":
            organization = v.value()
        if v.name() == "InstallDate":
            install_date = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(v.value()))
        if v.name() == "BuildLab":
            build_lab = v.value()

    result = [product_name, product_ID, system_root, owner, install_date, organization, build_lab]
    return result


# 타임존 정보를 이중 리스트로 반환하는 함수
def timezone():
    registry = Registry.Registry(sys_reg)
    path = ControlSet00n + "\\Control\\TimeZoneInformation"
    key = registry.open(path)

    active_time_bias = None
    timezone_name = None
    UTC = None

    for v in key.values():
        if v.name() == "ActiveTimeBias":
            active_time_bias = v.value()
        if v.name() == "TimeZoneKeyName":
            timezone_name = v.value()

    if active_time_bias is not None:
        # Active Time Bias로 UTC를 구합니다.
        tmp = (active_time_bias - 1) ^ 4294967295   # 4294967295 == FFFF FFFF
        UTC = int(tmp / 60)
    result = [timezone_name, active_time_bias, UTC]
    return result


# 컴퓨터 이름, 기본 사용자, 마지막 로그인한 사용자, 마지막 종료 시간
def others():
    computer_name = None
    default_user_name = None
    last_used_user_name = None
    shutdown_time = None

    registry = Registry.Registry(sys_reg)
    path = ControlSet00n + "\\Control\\ComputerName\\ComputerName"
    key = registry.open(path)
    for v in key.values():
        if v.name() == "ComputerName":
            computer_name = v.value()

    registry = Registry.Registry(soft_reg)
    path = "Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
    key = registry.open(path)
    for v in key.values():
        if v.name() == "DefaultUserName":
            default_user_name = v.value()
        if v.name() == "LastUsedUsername":
            last_used_user_name = v.value()

    registry = Registry.Registry(sys_reg)
    path = ControlSet00n + "\\Control\\Windows"
    key = registry.open(path)
    for v in key.values():
        if v.name() == "ShutdownTime":
            shutdown_time = decode.convert_time(v.value())

    result = [computer_name, default_user_name, last_used_user_name, shutdown_time]
    return result


# Uninstall의 하위 키를 통해
# 설치된 프로그램 정보를 이중 리스트로 반환하는 파싱 함수
def Uninstall():
    registry = Registry.Registry(soft_reg)

    # 서브키를 탐색하여 설치된 프로그램의 리스트 생성합니다
    # 64비트
    path_64 = "Microsoft\\Windows\\CurrentVersion\\Uninstall"  # 64비트 프로그램 경로
    key = registry.open(path_64)
    programs_64 = []
    for v in key.subkeys():
        programs_64.append(v.name())

    # 32비트
    path_32 = "WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"  # 32비트 프로그램 경로
    key = registry.open(path_32)
    programs_32 = []
    for v in key.subkeys():
        programs_32.append(v.name())

    # 설치된 프로그램의 정보를 담은 이중 리스트 생성를 생성합니다
    programs_info = []
    # 64비트
    for l in programs_64:
        program_path = path_64 + "\\" + l
        key = registry.open(program_path)

        display_name = None
        display_version = None
        install_location = None
        publisher = None
        type = "64 bit"
        install_date = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

        for v in key.values():
            if v.name() == "DisplayName":
                display_name = v.value()
            if v.name() == "DisplayVersion":
                display_version = v.value()
            if v.name() == "InstallLocation":
                install_location = v.value()
            if v.name() == "Publisher":
                publisher = v.value()
        if display_name is None:
            display_name = l

        programs_info.append([l, display_name, display_version, install_location, publisher, install_date, type])

    # 32비트
    for l in programs_32:
        program_path = path_32 + "\\" + l
        key = registry.open(program_path)

        display_name = None
        display_version = None
        install_location = None
        publisher = None
        type = "32 bit"
        install_date = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

        for v in key.values():
            if v.name() == "DisplayName":
                display_name = v.value()
            if v.name() == "DisplayVersion":
                display_version = v.value()
            if v.name() == "InstallLocation":
                install_location = v.value()
            if v.name == "Publisher":
                publisher = v.value()
        if display_name is None:
            display_name = l

        programs_info.append([l, display_name, display_version, install_location, publisher, install_date, type])

    return programs_info


# Multilingual User Interface
# 다중 언어를 지원하기 위해 프로그램 이름을 캐쉬하는 폴더
# 프로그램을 제거해도 MuiCache는 삭제되지 않는다.
def MuiCache(usrclass_reg):
    registry = Registry.Registry(usrclass_reg)
    key = registry.open("Local Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache")

    MuiCache = []
    for v in key.values():
        if v.name() != "LangID":
            MuiCache.append([v.value(), v.name()])

    return MuiCache


# UserAssist\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA} 실행파일 실행 기록
def UserAssist_CEB(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\\Count"
    key = registry.open(path)

    result = []
    for v in key.values():
        program_name = decode.ROT13(v.name())
        program_name = decode.GUID_to_display_name(program_name)
        run_count = int.from_bytes(v.value()[4:8], byteorder="little", signed=False)
        if v.value()[60:68] == b'\x00\x00\x00\x00\x00\x00\x00\x00' or program_name == "UEME_CTLSESSION":
            last_executed_time = None
        else:
            last_executed_time = decode.convert_time(v.value()[60:68])

        result.append([program_name, run_count, last_executed_time])

    return result


# UserAssist\{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F} 바로가기 실행 기록
def UserAssist_F4E(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist\\{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}\\Count"
    key = registry.open(path)

    result = []
    for v in key.values():
        program_name = decode.ROT13(v.name())
        program_name = decode.GUID_to_display_name(program_name)
        run_count = int.from_bytes(v.value()[4:8], byteorder="little", signed=False)
        if v.value()[60:68] == b'\x00\x00\x00\x00\x00\x00\x00\x00' or program_name == "UEME_CTLSESSION":
            last_executed_time = None
        else:
            last_executed_time = decode.convert_time(v.value()[60:68])

        result.append([program_name, run_count, last_executed_time])

    return result


# Background Activity Moderator
def BAM():
    registry = Registry.Registry(sys_reg)
    path = ControlSet00n + "\\Services\\bam\\State\\UserSettings"
    key = registry.open(path)
    sid = []
    for v in key.subkeys():
        sid.append(v.name())

    result = []
    for s in sid:
        sub_path = path + "\\" + s
        sub_key = registry.open(sub_path)
        for v in sub_key.values():
            if v.name() != "Version" and v.name() != "SequenceNumber":
                last_executed = decode.convert_time(v.value()[0:8])
                result.append([s, v.name(), last_executed])

    return result


# ComDlg32의 CIDSizeMRU 키
# 사용자가 가장 최근에 사용한 응용 프로그램
def CIDSizeMRU(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\CIDSizeMRU"
    key = registry.open(path)
    last_opened = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

    order = []
    for v in key.values():
        if v.name() == "MRUListEx":
            for i in range(0, 10000):
                if v.value()[i * 4] == 255:
                    break
                order.append(str(v.value()[i * 4]))

    result = []
    mru_position = 0
    for o in order:
        for v in key.values():
            if v.name() == o:
                program = ""
                var = struct.unpack("H"*296, v.value()) # CIDSizeMRU 키의 데이터들을 592 바이트입니다.
                for i in range(0, 296):                 # v.value()를 unsigned short(2 바이트)로 읽으므로 592 / 2 = 296
                    if var[i] == 0:                     # 2 바이트씩 묶은 후, utf-16 디코딩합니다.
                        break                           # 00 00이 나온다면 디코딩을 중단합니다.
                    else:
                        program = program + (struct.pack("<H", var[i]).decode("utf-16"))
                if mru_position == 0:
                    result.append([program, mru_position, last_opened])
                else:
                    result.append([program, mru_position, None])
        mru_position = mru_position + 1

    return result


# ComDlg32의 FirstFolder 키
# 사용자가 가장 최근에 사용한 앱과 사용자가 저장한 파일 목록
def FirstFolder(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\FirstFolder"
    key = registry.open(path)
    last_opened = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

    order = []
    for v in key.values():
        if v.name() == "MRUListEx":
            for i in range(0, 10000):
                if v.value()[i * 4] == 255:
                    break
                order.append(str(v.value()[i * 4]))

    result = []
    mru_position = 0
    for o in order:
        for v in key.values():
            if v.name() == o:
                program = ""
                folder = ""
                length = int(len(v.value())/2)
                var = struct.unpack("H"*length, v.value()) # 데이터의 길이의 1/2번 unsigned short(2 바이트)로 읽습니다.
                for i in range(0, length):
                    if var[i] == 0:                     # 2 바이트씩 묶은 후, utf-16 디코딩합니다.
                        for j in range(i + 1, length):
                            if var[j] == 0:
                                break
                            folder = folder + (struct.pack("<H", var[j]).decode("utf-16"))
                        break                           # 00 00이 나온다면 디코딩을 중단합니다.
                    else:
                        program = program + (struct.pack("<H", var[i]).decode("utf-16"))

                if mru_position == 0:
                    result.append([program, folder, mru_position, last_opened])
                else:
                    result.append([program, folder, mru_position, None])
        mru_position = mru_position + 1

    return result


# 연결했던 usb 정보를 이중 리스트로 반환하는 함수
def connected_usb(ntuser_reg):
    sys_registry = Registry.Registry(sys_reg)
    soft_registry = Registry.Registry(soft_reg)
    ntuser_registry = Registry.Registry(ntuser_reg)

    usb = []
    # DCID와 UIID를 구합니다.
    path = ControlSet00n + "\\Enum\\USBSTOR"
    key = sys_registry.open(path)
    for v in key.subkeys():
        DCID = v.name() # Device Class ID
        for w in v.subkeys():
            UIID = w.name() # Unique Instance ID
            usb.append([DCID, UIID])

    # UIID를 이용하여 볼륨 GUID를 매핑합니다.
    GUIDmap = []
    path = "MountedDevices"
    key = sys_registry.open(path)
    for v in key.values():
        if "\\??\\" in v.name():
            guid = v.name().split("\\??\\Volume")[1]
            uiid = v.value().decode("utf-16").split("#")[2]
            GUIDmap.append([guid, uiid])
    for u in usb:
        tmp = None
        for g in GUIDmap:
            if u[1] == g[1]:
                tmp = g[0]
                u.append(tmp)

    # UIID를 이용하여 볼륨 레이블/드라이브 문자와 최초 연결 시각을 매핑합니다.
    path = "Microsoft\Windows Portable Devices\Devices"
    key = soft_registry.open(path)
    for u in usb:
        label = None
        first_connected = None
        for v in key.subkeys():
            if u[1] in v.name():    # UIID가 subkey 이름에 있다면
                first_connected = v.timestamp().strftime("%Y-%m-%d %H:%M:%S")
                for w in v.values():
                    if w.name() == "FriendlyName":
                        label = w.value()
        u.extend([label, first_connected])

    # GUID를 이용하여 usb 마지막 연결 시간을 매핑합니다
    last_connected = []
    path = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"
    key = ntuser_registry.open(path)
    for v in key.subkeys():
        last_connected.append([v.name(), v.timestamp().strftime("%Y-%m-%d %H:%M:%S")])
    for u in usb:
        tmp = None
        for l in last_connected:
            if u[2] == l[0]:
                tmp = l[1]
                u.append(tmp)

    # DCID에서 제조사명, 제품명, 버전을 분리하여 리스트에 추가한 후, 결과를 반환합니다.
    for u in usb:
        vendor_name = u[0].split("&")[1].split("Ven_")[1]
        product_name = u[0].split("&")[2].split("Prod_")[1]
        version = u[0].split("&")[3].split("Rev_")[1]       # u[0] == DCID

        u.extend([vendor_name, product_name, version])

    # UIID에서 serial number를 추출합니다.
    for u in usb:
        # {Serial Number}&#
        # &가 1개 있으면 usb의 고유한 serial number입니다.
        if u[1].count("&") == 1:
            serial_num = u[1].split("&")[0]
            random_yn = False
        # #&{Random Number by PnP Manager}&#
        # &가 2개 있으면 PnP Manager가 부여한 random number입니다.
        # random number라면 random_yn 값을 True로 설정합니다.
        else:
            serial_num = u[1].split("&")[1]
            random_yn = True
        u.extend([serial_num, random_yn])

    return usb


# 최근 실행한 문서
def recent_docs(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs"
    key = registry.open(path)

    extensions = []
    for v in key.subkeys():
        extensions.append(v.name())

    # 확장자 별로 MRUListEX를 읽어 실행 순서가 저장된 extensions_order 리스트 생성
    # 확장자 별로 마지막 수정 시간이 저장된 extensions_timestamp 리스트 생성
    # 확장자 별로 MRUListEX를 제외한 값과 데이터가 저장된 extensions_list 리스트 생성
    extensions_order = []
    extensions_timestamp = []
    extensions_list = []
    for e in extensions:
        sub_path = path + "\\" + e
        sub_key = registry.open(sub_path)
        timestamp = sub_key.timestamp().strftime("%Y-%m-%d %H:%M:%S")
        order = []
        list = []

        for v in sub_key.values():
            if v.name() == "MRUListEx":
                for i in range(0, 10000):
                    if v.value()[i*4] == 255:
                        break
                    order.append(str(v.value()[i*4]))
            else:
                program = ""
                lnk = ""
                length = int(len(v.value())/2)
                var = struct.unpack("H"*length, v.value())
                for i in range(0, length):
                    if var[i] == 0:
                        for j in range(i + 8, length):
                            if var[j] == 0:
                                for k in range(j + 24, length):
                                    if var[k] == 0:
                                        break
                                    lnk = lnk + struct.pack("<H", var[k]).decode("utf-16")
                                break
                        break
                    else:
                        program = program + (struct.pack("<H", var[i]).decode("utf-16"))
                list.append([v.name(), program, lnk])

        extensions_order.append(order)
        extensions_list.append(list)
        extensions_timestamp.append(timestamp)

    result = []
    for i in range(len(extensions)):
        e = extensions[i]
        order = extensions_order[i]
        list = extensions_list[i]

        for j in range(len(order)):
            if j == 0:
                timestamp = extensions_timestamp[i]
            else:
                timestamp = None

            for l in list:
                if l[0] == order[j]:
                    result.append([e, j, l[1], l[2], timestamp])

    return result


# ComDlg32의 LastVisitedPidlMRU 키
# 사용자가 가장 최근에 접근했던 폴더
def LastVisitedPidl(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\LastVisitedPidlMRU"
    key = registry.open(path)
    last_opened = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

    order = []
    for v in key.values():
        if v.name() == "MRUListEx":
            for i in range(0, 10000):
                if v.value()[i * 4] == 255:
                    break
                order.append(str(v.value()[i * 4]))

    result = []
    mru_position = 0
    for o in order:
        for v in key.values():
            if v.name() == o:
                program = ""
                vvv = v.value()
                if len(v.value()) % 2 != 0:
                    vvv = v.value() + b'\x00'
                length = int(len(vvv)/2)
                var = struct.unpack("H"*length, vvv) # 데이터의 길이의 1/2번 unsigned short(2 바이트)로 읽습니다.
                for i in range(0, length):
                    if var[i] == 0:                     # 2 바이트씩 묶은 후, utf-16 디코딩합니다.
                        break                           # 00 00이 나온다면 디코딩을 중단합니다.
                    else:
                        program = program + (struct.pack("<H", var[i]).decode("utf-16"))

                if mru_position == 0:
                    result.append([program, mru_position, last_opened])
                else:
                    result.append([program, mru_position, None])
        mru_position = mru_position + 1

    return result


# ComDlg32의 LastVisitedPidlMRULegacy 키
# 대화상자 흔적
def Legacy(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\LastVisitedPidlMRULegacy"
    key = registry.open(path)
    last_opened = key.timestamp().strftime("%Y-%m-%d %H:%M:%S")

    order = []
    for v in key.values():
        if v.name() == "MRUListEx":
            for i in range(0, 10000):
                if v.value()[i * 4] == 255:
                    break
                order.append(str(v.value()[i * 4]))

    result = []
    mru_position = 0
    for o in order:
        for v in key.values():
            if v.name() == o:
                program = ""
                vvv = v.value()
                if len(v.value()) % 2 != 0:
                    vvv = v.value() + b'\x00'
                length = int(len(vvv) / 2)
                var = struct.unpack("H" * length, vvv)  # 데이터의 길이의 1/2번 unsigned short(2 바이트)로 읽습니다.
                for i in range(0, length):
                    if var[i] == 0:  # 2 바이트씩 묶은 후, utf-16 디코딩합니다.
                        break  # 00 00이 나온다면 디코딩을 중단합니다.
                    else:
                        program = program + (struct.pack("<H", var[i]).decode("utf-16"))

                if mru_position == 0:
                    result.append([program, mru_position, last_opened])
                else:
                    result.append([program, mru_position, None])
        mru_position = mru_position + 1

    return result


# ComDlg32의 OpenSavePidlMRU 키
# 사용자가 최근에 열고 저장했던 파일 목록
def OpenSavePidl(ntuser_reg):
    registry = Registry.Registry(ntuser_reg)
    path = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\OpenSavePidlMRU"
    key = registry.open(path)

    extensions = []
    for v in key.subkeys():
        extensions.append(v.name())

    # 확장자 별로 MRUListEX를 읽어 실행 순서가 저장된 extensions_order 리스트 생성
    # 확장자 별로 마지막 수정 시간이 저장된 extensions_timestamp 리스트 생성
    # 확장자 별로 MRUListEX를 제외한 값과 데이터가 저장된 extensions_list 리스트 생성
    extensions_order = []
    extensions_timestamp = []
    extensions_list = []
    for e in extensions:
        sub_path = path + "\\" + e
        sub_key = registry.open(sub_path)
        timestamp = sub_key.timestamp().strftime("%Y-%m-%d %H:%M:%S")
        order = []
        list = []

        for v in sub_key.values():
            if v.name() == "MRUListEx":
                for i in range(0, 10000):
                    if v.value()[i * 4] == 255:
                        break
                    order.append(str(v.value()[i * 4]))
            else:
                program = b''
                vvv = v.value()
                if len(v.value()) % 2 != 0:
                    vvv = v.value() + b'\x00'
                length = int(len(vvv) / 2)
                var = struct.unpack("H" * length, vvv)
                for i in range(length-5, 0, -1):
                    if var[i] == 0:
                        break
                    else:
                        program = struct.pack("<H", var[i]) + program
                try:
                    list.append([v.name(), program.decode("utf-8")])
                except:
                    list.append([v.name(), None])

        extensions_order.append(order)
        extensions_list.append(list)
        extensions_timestamp.append(timestamp)

    result = []
    for i in range(len(extensions)):
        e = extensions[i]
        order = extensions_order[i]
        list = extensions_list[i]

        for j in range(len(order)):
            if j == 0:
                timestamp = extensions_timestamp[i]
            else:
                timestamp = None

            for l in list:
                if l[0] == order[j]:
                    result.append([e, l[1], j, timestamp])

    return result


# SAM 하이브 파일에서 사용자 계정 정보를 이중 리스트로 반환하는 함수
def user_account():
    registry = Registry.Registry(sam_reg)

    # Users 경로의 하위 키들을 구합니다.
    path = "SAM\\Domains\\Account\\Users"
    key = registry.open(path)
    RID = []    # Relative ID :Users의 하위 키
    for v in key.subkeys():
        if v.name() != "Names":
            RID.append(v.name())

    # 각 하위 키에 대해 F와 V 값을 구해 계정 정보를 얻습니다.
    accounts = []
    for r in RID:
        sub_path = path + "\\" + r
        sub_key = registry.open(sub_path)
        for v in sub_key.values():
            if v.name() == "F":
                F = v.value()
                last_login_t = decode.convert_time(F[8:16])
                last_password_change_t = decode.convert_time(F[24:32])
                expires_on_t = decode.convert_time(F[32:40])
                last_incorrect_password_t = decode.convert_time(F[40:48])
                rid = int.from_bytes(F[48:52], byteorder="little")
                logon_failure_count = int.from_bytes(F[64:66], byteorder="little", signed=False)
                logon_success_count = int.from_bytes(F[66:68], byteorder="little", signed=False)
            if v.name() == "V":
                V = v.value()
                account_name_offset = int.from_bytes(V[12:16], byteorder="little") + 204
                account_name_len = int.from_bytes(V[16:20], byteorder="little")
                account_name = V[account_name_offset:account_name_offset + account_name_len].decode("utf-16")

                complete_account_offset = int.from_bytes(V[24:28], byteorder="little") + 204
                complete_account_name_len = int.from_bytes(V[28:32], byteorder="little")
                complete_account_name = V[complete_account_offset:complete_account_offset + complete_account_name_len].decode("utf-16")

                comment_offset = int.from_bytes(V[36:40], byteorder="little") + 204
                comment_len = int.from_bytes(V[40:44], byteorder="little")
                comment = V[comment_offset:comment_offset + comment_len].decode("utf-16")

                homedir_offset = int.from_bytes(V[72:76], byteorder="little") + 204
                homedir_len = int.from_bytes(V[76:80], byteorder="little")
                homedir = V[homedir_offset:homedir_offset+homedir_len].decode("utf-16")

        accounts.append([r, rid, last_login_t, last_password_change_t, expires_on_t, last_incorrect_password_t, logon_failure_count, logon_success_count,
                         account_name, complete_account_name, comment, homedir])

    # Names 키의 timestamp에서 계정 생성 시간을 얻습니다
    key = registry.open("SAM\\Domains\\Account\\Users\\Names")
    timestamp = []
    for v in key.subkeys():
        timestamp.append([v.name(), v.timestamp().strftime("%Y-%m-%d %H:%M:%S")])
    for a in accounts:
        for t in timestamp:
            if a[8] == t[0]:
                a.append(t[1])

    return accounts

def make_regDB():
    conn = sqlite3.connect("Believe_Me_Sister.db")
    cur = conn.cursor()

    # OSInformation
    data_list = os_info() + timezone() + others()
    query = "CREATE TABLE IF NOT EXISTS OSInformation" \
            "(product_name TEXT, product_ID TEXT, system_root TEXT, owner TEXT, install_date TEXT, organization TEXT, build_lab, " \
            "timezone_name TEXT, active_time_bias TEXT, UTC INTEGER, " \
            "computer_name TEXT, default_user_name TEXT, last_used_user_name TEXT, shutdown_time TEXT)"
    conn.execute(query)
    cur.execute("INSERT INTO OSInformation VALUES(?, ?, ?, ?, "
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data_list)
    conn.commit()

    # Uninstall:
    data_list = Uninstall()
    query = "CREATE TABLE IF NOT EXISTS Uninstall(id TEXT, name TEXT, version TEXT, install_location TEXT, publisher TEXT, install_date TEXT, type TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO Uninstall VALUES(?, ?, ?, ?, ?, ?, ?)", data_list)
    conn.commit()

    # BAM
    data_list = BAM()
    query = "CREATE TABLE IF NOT EXISTS BAM(SID TEXT, program_path TEXT, last_executed TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO BAM VALUES(?, ?, ?)", data_list)
    conn.commit()

    #UserAccounts():
    data_list = user_account()
    query = "CREATE TABLE IF NOT EXISTS UserAccounts(RID TEXT, RID_int INTEGER, last_login_time TEXT, last_password_change_time TEXT," \
            "expires_on TEXT, last_incorrect_password_time TEXT, logon_failure_count INTEGER, logon_success_count INTEGER," \
            "account_name TEXT, complete_account_name TEXT, comment TEXT, homedir TEXT, created_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO UserAccounts VALUES(?, ?, ?, "
                     "?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data_list)
    conn.commit()


    ##############################################################################################################
    ########## 이 부분부터는 계정이 n개면 n번 실행해야 함 ###############################################################
    ##############################################################################################################
    # MuiCache(usrclass_reg):
    data_list = MuiCache(usrclass_reg)
    query = "CREATE TABLE IF NOT EXISTS MuiCache(name TEXT, path TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO MuiCache VALUES(?, ?)", data_list)
    conn.commit()

    # UseraAsist_CEB(ntuser_reg):
    data_list = UserAssist_CEB(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS UserAssist_CEB(name TEXT, run_count INTEGER, last_executed TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO UserAssist_CEB VALUES(?, ?, ?)", data_list)
    conn.commit()

    #UserAssist_F4E(ntuser_reg):
    data_list = UserAssist_F4E(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS UserAssist_F4E(name TEXT, run_count INTEGER, last_executed TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO UserAssist_F4E VALUES(?, ?, ?)", data_list)
    conn.commit()

    # CIDSizeMUR(ntuser_reg):
    data_list = CIDSizeMRU(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS CIDSizeMRU(program_name TEXT, mru INTEGER, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO CIDSizeMRU VALUES(?, ?, ?)", data_list)
    conn.commit()

    # FirstFolder(ntuser_reg):
    data_list = FirstFolder(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS FirstFolder(program_name TEXT, folder TEXT, mru INTEGER, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO FirstFolder VALUES(?, ?, ?, ?)", data_list)
    conn.commit()

    # Connected_USB(ntuser_reg):
    data_list = connected_usb(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS Connected_USB(DCID TEXT, UIID TEXT, GUID TEXT, label TEXT, " \
            "first_connected TEXT, last_connected TEXT, vendor_name TEXT, product_name TEXT, version TEXT, serial_num TEXT, random_yn INTEGER)"
    conn.execute(query)
    cur.executemany("INSERT INTO Connected_USB VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data_list)
    conn.commit()

    # RecentDocs(ntuser_reg):
    data_list = recent_docs(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS RecentDocs(extension TEXT, mru INTEGER, program TEXT, lnk TEXT, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO RecentDocs VALUES(?, ?, ?, ?, ?)", data_list)
    conn.commit()

    # LastVisitedPidl(ntuser_reg):
    data_list = LastVisitedPidl(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS LastVisitedPidl(program TEXT, mru INTEGER, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO LastVisitedPidl VALUES(?, ?, ?)", data_list)
    conn.commit()

    # Legacy(ntuser_reg):
    data_list = Legacy(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS Legacy(program TEXT, mru INTEGER, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO Legacy VALUES(?, ?, ?)", data_list)
    conn.commit()

    # OpenSavePidl(ntuser_reg):
    data_list = OpenSavePidl(ntuser_reg)
    query = "CREATE TABLE IF NOT EXISTS OpenSavePidl(extension TEXT, program TEXT, mru INTEGER, opened_on TEXT)"
    conn.execute(query)
    cur.executemany("INSERT INTO OpenSavePidl VALUES(?, ?, ?, ?)", data_list)
    conn.commit()

    conn.close()

if __name__ == "__main__":
    sys_reg = sys.argv[1]
    soft_reg = sys.argv[2]
    sam_reg = sys.argv[3]
    ntuser_reg = sys.argv[4]
    usrclass_reg = sys.argv[5]

    ControlSet00n = get_controlset00n()

    make_regDB()

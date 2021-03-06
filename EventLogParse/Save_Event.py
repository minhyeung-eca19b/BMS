from EventLogParse import Log_Collect
import Database

def Save_Event():
    system_et = 'eventlogs/Logs/System.evtx'
    security_et = 'eventlogs/Logs/Security.evtx'
    application_et = 'eventlogs/Logs/Application.evtx'
    setup_et = 'eventlogs/Logs/Setup.evtx'
    compat_assistant_et = 'eventlogs/Logs/Microsoft-Windows-Application-Experience%4Program-Compatibility-Assistant.evtx'
    terminal_local_et = 'eventlogs/Logs/Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx'
    terminal_remote_et = 'eventlogs/Logs/Microsoft-Windows-TerminalServices-RemoteConnectionManager%4Operational.evtx'
    terminal_rdp_et = 'eventlogs/Logs/Microsoft-Windows-TerminalServices-RDPClient%4Operational.evtx'
    wlan_config_et = 'eventlogs/Logs/Microsoft-Windows-WLAN-AutoConfig%4Operational.evtx'
    net_profile_et = 'eventlogs/Logs/Microsoft-Windows-NetworkProfile%4Operational.evtx'
    kernel_boot_et = 'eventlogs/Logs/Microsoft-Windows-Kernel-Boot%4Operational.evtx'
    partition_et = 'eventlogs/Logs/Microsoft-Windows-Partition%4Diagnostic.evtx'
    biometrics_et = 'eventlogs/Logs/Microsoft-Windows-Biometrics%4Operational.evtx'

    #pc on/off and sleep mode
    all_information = {
        biometrics_et:{
          '1004':'Login Success using fingerprint recognition.', '1005':'Login Failed using fingerprint recognition.'
         },
        partition_et:{
            '1006':''
         },
        terminal_remote_et:{
            '261':'Listener received a connection',
            '1149':'Remote Desktop Services: User authentication succeeded'
        },
        terminal_local_et:{
            '24':'Remote Desktop Services: Session has been disconnected',
            '25':'Remote Desktop Services: Session reconnection succeeded',
            '40':'Session <X> has been disconnected, reason code',
            '41':'Start session arbitration',
            '42':'End session arbitration'
        },
        terminal_rdp_et:{
            '1024':'RDP ClientActiveX is trying to connect to the server',
            '1025':'RDP ClientActiveX has connected to the server.',
            '1026':'RDP ClientActiveX has been disconnected',
            '1027':'Connected to domain',
            '1028':'The server supports SSL',
            '1102':'The client has initiated a multi-transport connection to the server'
        },
        compat_assistant_et:{
          '17':'Install and Execute Program'
        },
        setup_et:{
            '2':'was successfully changed to the Installed state.'
        },
        system_et: {
            '12':'Start Windows',                           '13':'Shut down Windows',
            '1074':'Shut down/Restart',                     '104':'Log is deleted',
            '42':'Turn on Sleep Mode',                      '1':'Turn off Sleep Mode',
            '7045':'Install service in System',             '22':'Changed Time Zone',
            '24580':'Decryption of volume started.',
            '24660':'Encrypt of volume started',
            '10000':'Driver package is being installed',
            '10002':'service upgrade',                      '10100':'The driver package installation has succeeded',
            '20003':'Service Installation or Update',       '24576':'Drivers were successfully installed for device .',
            '24577':'Compatibility Layer Successful Registration',
            '24579':'Autoplay Skipping'
        },
        security_et:{
            '4624':'Success Login',          '4625':'Failed Login',
            '4634':'Logoff',                 '4720':'Created Account',
            '4726':'Deleted Account',        '4724':'Changed Password',
            '4738':'Changed Account Name',   '4732':'Add to Admin group',
            '4733':'Remove from Admin group','1102':'The audit log was cleared',
            '4648':'A logon was attempted using explicit credentials',
            '4616':'System time was changed'
        },
        net_profile_et:{
          '10000':'Connected Network', '10001':'Disconnected Network'
        },
        wlan_config_et:{
          '8003':'Disconnected Network'
        },
        kernel_boot_et:{
            '12':'Start Windows'
        },
        application_et: {
            '1002': 'Kill process'
        }
    }

    data_list = Log_Collect.PC_Processing(all_information)

    Database.Event_Log_Database(data_list)
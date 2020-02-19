#!/usr/bin/env python3


#############ATTEMPT OF USING A FUNCTION :)
############ USING COMMANDS from YAML


import netmiko
import yaml
import json
import os
from pprint import pprint
from copy import deepcopy
import json
from ntc_templates.parse import parse_output, clitable
import ntc_templates.parse
import netdev
import asyncio
#import textfsm
path='inventory.yml'
commands='commands_platforms.yml'
netmiko_exceptions = (netmiko.ssh_exception.NetMikoTimeoutException,
                          netmiko.ssh_exception.NetMikoAuthenticationException)

def create_dir(dir_to_create):
    if not os.path.exists(dir_to_create):
                   os.mkdir(dir_to_create) 
                   print ("Directory",dir_to_create,"created")

def get_yaml_content():
    with open(path) as f:
        yaml_content = yaml.safe_load(f.read())
  
    parsed_yaml = deepcopy(yaml_content)
    result = []
    global_params = parsed_yaml['all']['vars']
    device_params = parsed_yaml['all'].get('hosts')
    g_delay = {'banner_timeout' :200}
    #pprint (device_params)
    with open(commands) as g:
          commands_content = yaml.safe_load(g.read())
    parsed_commands = deepcopy(commands_content)
    for host in device_params:
        host_dict = {}
        hostname = host.pop('hostname')
        host_dict['hostname'] = hostname
        host_dict.update(global_params)
        host_dict.update(host)
        result.append(host_dict)
    #pprint (result)
    return [device_params,parsed_commands,global_params,result]

def main():
    create_dir('outputs')
    device_params = get_yaml_content()[0]
    parsed_commands = get_yaml_content()[1]
    global_params = get_yaml_content()[2]
    result = get_yaml_content()[3]
    print (parsed_commands)
    print (device_params)
    print (global_params)
#    pprint (result)
    '''
    for device in result:
        group = device.pop('group')
        hostname = device.pop('hostname')
        platform_os =  device['device_type']
        pprint(device)
        exit()
    '''
    
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(commands_async(device,parsed_commands))
             for device in result]
    loop.run_until_complete(asyncio.wait(tasks))

async def commands_async(devices,parsed_commands):
        
        hostname = devices.pop('hostname')
        newdir = hostname
        newdir = f'outputs/{hostname}'
        create_dir(newdir)
        group = devices.pop('group')
        platform_os =  devices['device_type']
        pprint (devices)
        
        try:
            async with netdev.create(**devices) as connection:
                device_output = ['{0} {1} {0}'.format ('=' * 30, hostname)]
                
                print(device_output)
            
                               
                   
                for platform in parsed_commands['commands']:
                      plat_com = platform
                      comm = parsed_commands['commands'][platform]
                      
                      if plat_com == platform_os:
                              print (plat_com)
                              for i in comm:    
                                    output = await connection.send_command(i)
                                                    
                                    print('{0}{1}{0}'.format('=' * 30, i, hostname, platform_os))
                                                    
                                    parse_commands(output,platform_os,i,newdir)
            
            
            
            
        except netmiko_exceptions as x:
            log_dir = 'logs'
            create_dir(log_dir)
            filename = hostname + '.log'
            filename = '/'.join((log_dir,filename))
            fd=open(filename,"w+")
            log='Failed to connect to ' +  hostname
            reason = x.__class__.__name__
            print (hostname,'Failed to connect',reason)
            log= log +' '+ reason
            fd.write (log )
            fd.write ('\n')

def parse_commands(output,platform_os,command,newdir):
    #ntc_exceptions = (textfsm.clitable.CliTableError)
    try:
       vlans_dict =[]
       print (command,platform_os)
       command_parsed = parse_output( platform = platform_os , command = command , data = output)

       dump_command(command,command_parsed,newdir)

    except:
       print ('Command ERROR')
       command_parsed = f'{command} NOT AVAILABLE on {platform_os} or not template available'
       dump_command(command,command_parsed,newdir)
       
def dump_command(command,command_parsed,newdir):
       
       filename = command.replace(' ','_')+'.json'
       filename2 = command.replace(' ','_')+'.yml'
       filename = '/'.join((newdir, filename))
       filename2 = '/'.join((newdir, filename2))
       end_var = command.replace(' ','_')
       END = end_var.upper()
       print (END)
       print ('FILENAME',filename)
       END_DICT = { END : command_parsed }
       with open(filename,'w') as f:
               json.dump(END_DICT,f, indent = 2)
       with open(filename2,'w') as g:
               yaml.dump(END_DICT,g,sort_keys=False)


if __name__ == '__main__':
    main()





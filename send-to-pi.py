import paramiko
from scp import SCPClient

print('started...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('172.24.1.1', username='pi', password='raspberry')

print('copying pycontrolserver')
scp = SCPClient(ssh.get_transport())
scp.put('picontrolserver.py','/home/pi/picontrolserver/.')
scp.close()

print('copying index')
scp = SCPClient(ssh.get_transport())
scp.put('index.html','/home/pi/picontrolserver/.')
scp.close()

print('ensuring server is down')
ssh.exec_command('sudo /etc/init.d/picontrolserver stop')

#print('run server')
#(stdin, stdout, stderr) = ssh.exec_command('python /home/pi/picontrolserver/picontrolserver.py')
#for line in iter(stdout.readline, ""):
#    print(line, end="")

#for line in iter(stderr.readline, ""):
#    print(line, end="")

print('finished.')

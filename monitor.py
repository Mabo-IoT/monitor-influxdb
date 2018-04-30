# -*- coding: utf-8 -*-
import time 
import subprocess
import psutil
import traceback


from util import get_conf
from logging_init import setup_logging

conf = get_conf('./conf/conf.toml')
log = setup_logging(conf['log'])

class Monitor(object):
    def __init__(self, conf):
        #log.debug(conf)
        self.process_name = conf['process']
        self.memory_limit = conf['memory_limit']
        self.restart_cmd = conf['restart_cmd']
        self.process = self.get_process(conf['process']) 
    
    def get_process(self, name='influxdb'):
        """
        get specified process
        """
        self.process_id = self.get_process_pid(name)
        return psutil.Process(self.process_id)

    def get_process_pid(self, name='influxdb'):
        """
        get specified process id if it is alived
        """
        for proc in psutil.process_iter():
            pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
            #log.debug(pinfo)
            if pinfo['name'] == name:
                return pinfo['pid']
        
        return None

    def get_process_memory(self):
        """
        get process current memory
        """
        pmem = self.process.memory_info()
        log.debug(pmem)
        return pmem.rss

    def process_restart(self):
        """
        restart influxdb 
        """
        cmd = subprocess.Popen(self.restart_cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = cmd.communicate()
        return output, err

    def run(self):
        
        while True:
            try:
                # confirm influxdb process is alive
                if self.process.name() == self.process_name: 

                    self.process_memory = self.get_process_memory()

                    if self.process_memory > self.memory_limit:
                        output, err = self.process_restart()
                        log.debug("Output:%s", output)
                        log.debug("Error:%s", err)
                        self.process = self.get_process(self.process_name)
                
                # keep fetch influxdb process if it is dead
                else:
                    log.debug('No %s process, keep looking', self.process_name)
                    self.process = self.get_process(self.process_name)
                
                time.sleep(1)
            except Exception as e:
                log.error(e)
                # traceback.print_exc()
                self.process = self.get_process(self.process_name)
    
if __name__ == '__main__':
    monitor = Monitor(conf['monitor'])
    monitor.run()

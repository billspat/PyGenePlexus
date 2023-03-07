# download_with_scp.py
""" for those with access to a linux host where these files are stored, 
use scp to download.    

assumes that the hostname has been setup with ssh keys in this systems config (~/.ssh)
documentation for how to setup ssh keys and ssh config are beyond the scope of this package

"""
import os,sys
import geneplexus
from paramiko import SSHClient
from scp import SCPClient


def missing_files(file_loc):
    """find which files are not downloaded yet using list from gp package"""
    m = [d for d in geneplexus.util.get_all_filenames() if not(os.path.exists(os.path.join(file_loc,d)))]
    return(m)

def scp_files(filenames, file_loc, host_name, remote_path):
    """ use scp to download files in list provided"""

    def scp_progress(filename, size, sent):
        sys.stdout.write("%s's progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )
        
    with SSHClient() as ssh:
        ssh.load_system_host_keys()
        ssh.connect(host_name)

        with SCPClient(ssh.get_transport(),progress=scp_progress) as scp:
            for fname in filenames:
                try:
                    scp.get(remote_path=os.path.join(remote_path,fname), 
                        local_path=os.path.join(file_loc,fname), 
                        recursive=False, 
                        preserve_times=False)
                except:
                    print(f"error downloading {fname}, continuing")
    

if __name__ == "__main__":
    usage = "download_with_scp.py <host> </path/on/host/to/sourcefiles> <optional destination/path, default .data>"
    if len(sys.argv) < 3:
        print(usage)
    remote_host = sys.argv[1] # eg. 'hpcc.msu.edu'
    remote_path = sys.argv[2] # eg. '/mnt/research/etc/etc/geneplexus_data/'
    
    if len(sys.argv) < 4:
        file_loc = sys.argv[3]  
    else:
        file_loc = '.data'

    try:    
        scp_files(filenames = missing_files(file_loc),
              file_loc = file_loc, 
              host_name = remote_host, 
              remote_path = remote_path)
    except Exception as e:
        print(f"SCP download failed for host={remote_host}, remote path = {remote_path}, destination = {file_loc} {e}")
        


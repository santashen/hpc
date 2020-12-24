# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: lab
#     language: python
#     name: lab
# ---

# +
import os
import re
import stat

import paramiko


class Hpc:
    """Interact with super computers.
    
        Attributes:
            ip: ip of server
            username: account name
            passwd: account password 
    """

    def __init__(self, ip,username,passwd):
        """Specify ip,username and password for server conncection """

        self.name = name
        self.ip = ip
        self.username = username
        self.passwd = passwd
        self.trans = paramiko.Transport((self.ip, 22))

    def __enter__(self):
        """Build the connection passage."""
        self.trans.connect(username=self.username, password=self.passwd)
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)
        self.ssh = paramiko.SSHClient()
        self.ssh._transport = self.trans
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Close the connection passage."""
        self.trans.close()

    def __get_all_files(self, directory, remote=True):  # revise from CSDN:littleRpl
        all_files = []
        if remote == True:
            files = self.sftp.listdir_attr(directory)
            for file in files:
                filename = directory + "/" + file.filename

                if stat.S_ISDIR(file.st_mode):  # 如果是文件夹的话递归处理
                    all_files.extend(self.__get_all_files(filename))
                else:
                    all_files.append(filename)

            return all_files
        else:
            for direc, folder, files in os.walk(directory):
                for file in files:
                    all_files.append(os.path.join(direc, file))
            return all_files

    def upload(self, localpath, remotepath):
        """Upload local files to remote servers.
        
        Args:
            localpath: local file or local folder
            remotepath: remote file or remote folder
        """
        if os.path.isfile(localpath):
            try:
                sftp.stat(remotepath)
            except:
                self.run_shell("mkdir -p {}".format(os.path.dirname(remotepath)))

            self.sftp.put(localpath, remotepath)
            print("successfully upload {} ^w^".format(localpath))
        else:
            all_files = self.__get_all_files(localpath, remote=False)
            for file in all_files:

                remote_filename = file.replace(localpath, remotepath).replace("\\", "/")
                remote_path = os.path.dirname(remote_filename)

                try:
                    sftp.stat(remote_path)
                except:
                    self.run_shell("mkdir -p {}".format(remote_path))  # 使用这个远程执行命令

                self.sftp.put(file, remote_filename)
                print("successfully upload {} ^w^".format(file))

    def download(self, localpath, remotepath):
        """Download files in remote server to local path.
        
        Args:
            localpath: local file or local folder
            remotepath: remote file or remote folder
        """
        if stat.S_ISREG(self.sftp.lstat(remotepath).st_mode):
            self.sftp.get(remotepath, localpath)
            print("successfully download {}".format(remotepath))
        else:
            all_files = self.__get_all_files(remotepath, remote=True)
            for file in all_files:

                local_filename = file.replace(remotepath, localpath)
                local_path = os.path.dirname(local_filename)
                if not os.path.exists(local_path):
                    os.makedirs(local_path)
                self.sftp.get(file, local_filename)
                print("successfully download {} ^w^".format(file))

    def delete(self, remote_file_or_folder):
        """Delete file or folder"""
        self.run_shell("rm -r {}".format(remote_file_or_folder))
        try:
            sftp.stat(remotefile)
        except:
            print("successfully delete {} ^w^".format(remotefile))

    def run_shell(self, command, stream_out=False, line_nums=5):
        """Run shell command.
        
        Args:
            command: shell command, for multi commands, use semicolon to seperate.
        ------------
        Examples:
            with Hpc(name="sunway") as sunway:
                print(sunway.run_shell("cd some_folder; ls"))
        """
        command = "bash -lc '{}'".format(command)
        stdin, stdout, stderr = self.ssh.exec_command(command, get_pty=True)
        if stream_out == False:
            out = stdout.read().decode()
            error = stderr.read().decode()
            return out
        else:
            for i, line in enumerate(iter(lambda: stdout.readline(2048), "")):
                print(line, end="")
                if i >= line_nums:
                    break

    def bjobs(self, job_name=None):
        """Return the queue numbers of job_name"""
        if job_name is None:
            return self.run_shell("bjobs")
        else:
            job_information = self.run_shell("bjobs")
            job_numbers = [
                re.findall("[0-9]+", line)[0]
                for line in job_information.split("\n")
                if re.findall(job_name, line)
            ]
            return job_numbers

    def bpeek(self, job_number, line_nums=5):
        """bpeek -f job_number"""
        self.run_shell(
            "bpeek -f {}".format(job_number), stream_out=True, line_nums=line_nums
        )

    def bkill(self, job):
        """Kill job by job_name"""
        try:
            int(job)
            message = self.run_shell("bkill {}".format(job))
            print(message)
        except:
            job_numbers = self.bjobs(job)
            for job_number in job_numbers:
                message = self.run_shell("bkill {}".format(job_number))
                print(message)

    def bsub(
        self,
        directory,
        file,
        node=3,
        processor=24,
        software="lammps",
        job_name="lmp_Mr_shen",
    ):
        """bsub specified file"""
        if software == "lammps":
            message = self.run_shell(
                "cd {};bsub -q q_x86_share -J {} -N {} -np {} -o out.log -i {}\
               /GFPS8p/caoby/shen/lammps/src/lmp_Mr_shen -sf opt".format(
                    directory, job_name, node, processor, file
                )
            )
        print(
            message,
            "submitted file is :   " + os.path.join(directory, file).replace("\\", "/"),
            "----^w^------",
            sep="\n",
        )

    def qload(self):
        """show current works"""
        message = self.run_shell("qload -w")
        return message

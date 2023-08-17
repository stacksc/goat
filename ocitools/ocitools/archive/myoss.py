#!/usr/bin/env python3
# ==============================================================================
# Copyright (c) 2020, Oracle and/or its affiliates. All rights reserved.
# ==============================================================================

import sys, argparse, logging
import sys, os, threading, socket, argparse, re, tty, termios, fnmatch, os.path, pexpect, time, datetime, collections, locale, socket, struct, subprocess
import shutil
from collections import defaultdict
from termcolor import cprint
from time import sleep
from glob import glob
from multiprocessing import Process
from tqdm.auto import tqdm
import common
import color

import oci
from oci.object_storage.models import CreateBucketDetails

# initial directory stack
pushstack = list()
global targets, regions
targets = {}

home = os.getenv("HOME")
lock = threading.Lock()

# get our regions
with open(home + "/.oci/config") as f:
    regions = []
    for line in f:
        if line.startswith('['):
            s = line.replace(']','').replace('[','').strip()
            regions.append(s)
    regions.append("ALL")

class ProgressBar(object):

    DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
    FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(remaining)d to go'

    def __init__(self, num_lines, width=80, fmt=DEFAULT, symbol='#',
                 output=sys.stderr):
        assert len(symbol) == 1

        total = num_lines
        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d',
            r'\g<name>%dd' % len(str(total)), fmt)
        self.current = 0

    def __call__(self):
        percent = self.current / float(self.total)
        size = int(self.width * percent)
        remaining = self.total - self.current
        bar = '[' + self.symbol * size + ' ' * (self.width - size) + ']'

        args = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % args, file=self.output, end='')

    def done(self):
        self.current = self.total
        self()
        print('', file=self.output)

def delBucket(object_storage, namespace, bucket, profile):

    try:
        response = oci.pagination.list_call_get_all_results(object_storage.list_preauthenticated_requests, namespace_name=namespace, bucket_name=bucket)
    except:
        print("FAIL: bucket {} not found in region:  {}".format(bucket, profile), end='')
        print(common.MOVE2 + common.RED + "FAILURE" + common.RESET)
        return -1

    if response:
        for auth in response.data:
            oci.object_storage.ObjectStorageClient.delete_preauthenticated_request(object_storage, namespace_name=namespace, bucket_name=bucket, par_id=auth.id)

    try:
        object_storage.delete_bucket(namespace, bucket)
        print('INFO: deleted bucket ' + bucket + ' from: ' + profile)
        return 0
    except:
        cmd='oci --profile %s os object bulk-delete --bucket-name %s --force >/dev/null 2>&1' %(profile, bucket)
        os.system(cmd)
        # delete the bucket now
        object_storage.delete_bucket(namespace, bucket)
        print('INFO: deleted bucket ' + bucket + ' from: ' + profile)
        return 0
    return 0

def createBucket(object_storage, namespace, bucket, profile):
    if args.ocid:
        c = str(args.ocid)

    request = CreateBucketDetails(public_access_type='NoPublicAccess')     # private bucket
    request.compartment_id = c
    request.name = bucket
    bucket = object_storage.create_bucket(namespace, request)

    if bucket.data.etag:
        print("INFO: bucket created for " + profile + " and bucket tag " + bucket.data.etag)
        return 0

def upload_to_object_storage(config, namespace, bucket, path, profile):

    with open(path, "rb") as in_file:
        name = os.path.basename(path)
        ostorage = oci.object_storage.ObjectStorageClient(config)
        try:
            ostorage.put_object(namespace,
                                bucket,
                                name,
                                in_file)
            print("INFO: finished uploading {} to {}".format(name, profile), end='')
            print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
        except:
            print("ERROR")

class BamBam(threading.Thread):

    output_lock = threading.Lock()

    def __init__(self):
        threading.Thread.__init__(self)
        # A flag to notify the thread that it should finish up and exit
        self.kill_received = False

    def run(self):

        while not self.kill_received:
            try:
                line = str(queue.get(True, 1))
                profile = line.strip()
            except Queue.Empty:
                continue

            chk = any(c.isalpha() for c in profile)

            if chk is False:
                break

            config = oci.config.from_file(profile_name=profile)
            object_storage = oci.object_storage.ObjectStorageClient(config)
            namespace = object_storage.get_namespace(compartment_id=request.compartment.id).data
            client = oci.identity.IdentityClient(config)
            request.compartment_id = c

            if args.create:
                try:
                    result = self.createBucket(object_storage, namespace, bucket, profile)
                except:
                    print(common.RED + "ERROR: " + common.RESET + " unable to create bucket")
                    result = -1
                    pass
            elif args.delete:
                try:
                    result = self.delBucket(object_storage, namespace, bucket, profile)
                except:
                    print(common.RED + "ERROR: " + common.RESET + " unable to delete bucket")
                    result = -1
                    pass
            elif args.fname:
                self.uploadObjects(object_storage, namespace, bucket, profile, config)
                result = 0
            elif args.verify:
                result = self.verifyProfile(config, client, profile)
            elif args.agents or args.patches or args.solr or args.cookbooks:
                prefix_files_name = 'patch'
                listfiles = object_storage.list_objects(namespace,bucket,prefix=prefix_files_name)

                if not listfiles.data.objects:
                    print("INFO: no files found to be deleted in profile " + profile)
                    result = 0
                else:
                    for filenames in listfiles.data.objects:
                        object_storage.delete_object(namespace, bucket,filenames.name)
                        print("INFO: deleted " + filenames.name + " from bucket " + bucket + " and profile " + profile)
                    result = 0

            return_queue.put([profile, result])
            continue

    def verifyProfile(self, config, client, profile):

        try:
            oci.config.validate_config(config)
            blah = client.list_regions()
            with self.output_lock:
                print("INFO: verifying profile and access for: " + profile, end='')
                print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
            return 0
        except:
            with self.output_lock:
                print("INFO: verifying profile and access for: " + profile, end='')
                print(common.MOVE2 + common.RED + "FAILURE" + common.RESET)
            return -1
        return 0

    def delBucket(self, object_storage, namespace, bucket, profile):

        try:
            response = oci.pagination.list_call_get_all_results(object_storage.list_preauthenticated_requests, namespace_name=namespace, bucket_name=bucket)
        except:
            print("FAIL: bucket {} not found in region:  {}".format(bucket, profile), end='')
            print(common.MOVE2 + common.RED + "FAILURE" + common.RESET)
            return -1

        if response:
            for auth in response.data:
                oci.object_storage.ObjectStorageClient.delete_preauthenticated_request(object_storage, namespace_name=namespace, bucket_name=bucket, par_id=auth.id)

        try:
            object_storage.delete_bucket(namespace, bucket)
            print('INFO: deleted bucket from: ' + profile)
            return 0
        except:
            cmd='oci --profile %s os object bulk-delete --bucket-name %s --force >/dev/null 2>&1' %(profile, bucket)
            os.system(cmd)
            object_storage.delete_bucket(namespace, bucket)
            print('INFO: deleted bucket from: ' + profile)
            return 0
        return 0

    def createBucket(self, object_storage, namespace, bucket, profile):
        if args.ocid:
            c = str(args.ocid)

        #request = CreateBucketDetails(public_access_type='ObjectWrite')
        request = CreateBucketDetails(public_access_type='NoPublicAccess')
        request.compartment_id = c
        request.name = bucket
        bucket = object_storage.create_bucket(namespace, request)

        if bucket.data.etag:
            print("INFO: bucket created for " + profile + " and bucket tag " + bucket.data.etag)
            return 0

        return -1

    def upload_to_object_storage(self, config, namespace, bucket, path, profile):

        with open(path, "rb") as in_file:
            name = os.path.basename(path)
            ostorage = oci.object_storage.ObjectStorageClient(config)
            try:
                ostorage.put_object(namespace,
                                    bucket,
                                    name,
                                    in_file)
                print("INFO: finished uploading {} to {}".format(name, profile), end='')
                print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
            except:
                print("ERROR")

    def uploadObjects(self, object_storage, namespace, bucket, profile, config):

        object_name = str(args.fname)
        if not os.path.isfile(object_name) and not os.path.isdir(object_name):
            print(common.RED + "ERROR: " + common.RESET + " unable to upload object to OSS because file does not exist " + object_name)
            parser.parse_args(['-h'])

        if os.path.isfile(object_name):
            with open(object_name, 'rb') as f:
                try:
                    obj = object_storage.put_object(namespace, bucket, object_name, f)
                    print("INFO: finished uploading {} to {}".format(object_name, profile), end='')
                    print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
                except:
                    print(common.RED + "ERROR: " + common.RESET + " unable to upload object to OSS " + object_name)
                    pass
        else:
            dir = args.fname + os.path.sep + "*"
            proc_list = []

            for f in glob(dir):
                if os.path.isfile(f):
                    p = Process(target=upload_to_object_storage, args=(config, namespace, bucket, f, profile))
                    p.start()
                    proc_list.append(p)

            for job in proc_list:
                job.join()

        return 0

def startWork(profiles):

    global queue
    global return_queue
    global interval
    global number

    queue = Queue.Queue(0)
    return_queue = Queue.Queue(0)

    number = 0
    threadlist = []
    start = time.time()
    num_of_threads = maxthread

    if len(targets) < maxthread:
        num_of_threads = len(targets)

    for x in range(num_of_threads):
        t = BamBam()
        threadlist.append(t)
        t.start()

    for p in targets:
        queue.put(p)

    for t in threadlist:
        queue.put([0, 0])

    while has_live_threads(threadlist):
        try:
            [t.join(1) for t in threadlist
             if t is not None and t.isAlive()]
        except KeyboardInterrupt:
            print(common.RED + "\nCaught KeyboardInterrupt, exiting...\n" + common.RESET)
            for t in threadlist:
                t.kill_received = True
            return_code = 1
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    for x in range(len(targets)):
        profile, results = return_queue.get()

    finish = time.time()
    interval = finish - start

def timeMessage():

    print (common.YELLOW + "#####################################################################" + common.RESET)
    print (common.YELLOW + "# EXECUTION TIME: " + str(interval) + " seconds" + common.RESET)
    print (common.YELLOW + "#####################################################################\n" + common.RESET)

parser = argparse.ArgumentParser(description=common.BLUE + 'OSS utility' + common.RESET)
commands = parser.add_argument_group('available tasks')
commands.add_argument('--bucket', default=False, type=str, dest='bucket', help=common.BLUE + 'provide a bucket name for operations'  + common.RESET)
commands.add_argument('--delete', action='store_true', dest='delete', default=False, help=common.BLUE + 'delete a bucket in compartment'  + common.RESET)
commands.add_argument('--create', action='store_true', dest='create', default=False, help=common.BLUE + 'create a bucket in compartment'  + common.RESET)
commands.add_argument('--verify', action='store_true', dest='verify', default=False, help=common.BLUE + 'verify profile connection keys'  + common.RESET)
commands.add_argument('--file', dest='fname', default=False, type=str, help=common.BLUE + 'provide file/directory name to upload to specific bucket'  + common.RESET)
commands.add_argument('--pull', dest='object', default=False, type=str, help=common.BLUE + 'provide object name to download from bucket'  + common.RESET)

options = parser.add_argument_group('options')
options.add_argument('--profile', default=False, nargs='?', help=common.BLUE + 'supply profile name for connection' + common.RESET, choices=regions)
options.add_argument('--compartment', default=False, type=str, dest="ocid", help=common.BLUE + 'supply optional compartment OCID' + common.RESET)

def has_live_threads(threadlist):
    return True in [t.isAlive() for t in threadlist]

def populateTargets(fname):

    num_lines = sum(1 for line in open(fname))
    progress = ProgressBar(num_lines, fmt=ProgressBar.FULL)
    cprint("\n[*] compiling profile target list ", "green")

    my_file = open(fname, 'r')
    number = 0
    flag = False

    for line in my_file:
        progress.current += 1
        progress()
        number = number + 1
        head, sep, tail = line.partition(',')
        profile = head.strip()

        flag = True

        targets[profile] = [number]
        targets[profile].append(profile)
    progress.done()
    progress.current = 0

    return targets

def main():

    start = time.time()
    global maxthread, args, bucket

    maxthread = 40
    count_args = len(sys.argv)

    if count_args <= 0:
        parser.parse_args(['-h'])
    else:
        args = parser.parse_args()

    if args.profile:
        profile = str(args.profile)

        if args.bucket:
            bucket = str(args.bucket)
        elif not args.bucket and args.verify:
            verify = True
        else:
            parser.parse_args(['-h'])

        if profile == 'ALL':
            populateTargets(regions)
            try:
                startWork(regions)
            except KeyboardInterrupt:
                print(common.RED + "\nCaught KeyboardInterrupt, exiting...\n" + common.RESET)
                return_code = 1
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)
        else:
            c = str(args.ocid)
            config = oci.config.from_file(profile_name=profile)
            object_storage = oci.object_storage.ObjectStorageClient(config)
            namespace = object_storage.get_namespace(compartment_id=c).data
            client = oci.identity.IdentityClient(config)

            if args.verify:
                print("INFO: verifying profile and access for: " + profile, end='')
                try:
                    oci.config.validate_config(config)
                    blah = client.list_regions()
                    print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
                except:
                    print(common.MOVE2 + common.RED + "FAILURE" + common.RESET)
                    sys.exit()

            elif args.create:
                try:
                    createBucket(object_storage, namespace, bucket, profile)
                except:
                    print(common.RED + "ERROR: " + common.RESET + " unable to create bucket")
                    pass
            elif args.delete:
                try:
                    delBucket(object_storage, namespace, bucket, profile)
                except:
                    print(common.RED + "ERROR: " + common.RESET + " unable to delete bucket")
                    pass
            elif args.object:
                object_name = str(args.object)
                print('INFO: retrieving file from object storage')
                get_obj = object_storage.get_object(namespace, bucket, object_name)
                total = int(get_obj.headers.get('content-length', 0))
                output = home + '/.gen2/downloads/%s' %(str(object_name))
                os.makedirs(os.path.dirname(output), exist_ok=True)
                print()
                try:
                    with open(output, 'wb', buffering = 2 ** 24) as f, tqdm(
                        desc=str(object_name),
                        total=total,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                        for data in get_obj.data.iter_content(chunk_size=1024):
                            size = f.write(data)
                            bar.update(size)
                except KeyboardInterrupt:
                    print(color.RED + "\nCaught KeyboardInterrupt, exiting...\n" + color.RESET)
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                print()
            elif args.fname:
                object_name = str(args.fname).rstrip("/")

                if not os.path.isfile(object_name) and not os.path.isdir(object_name):
                    print(common.RED + "ERROR: " + common.RESET + " unable to upload object to OSS because file does not exist " + object_name)
                    parser.parse_args(['-h'])

                if os.path.isfile(object_name):
                    with open(object_name, 'rb') as f:
                        try:
                            obj = object_storage.put_object(namespace, bucket, object_name, f)
                            print("INFO: finished uploading {} to {}".format(object_name, profile), end='')
                            print(common.MOVE2 + common.GREEN + "SUCCESS" + common.RESET)
                        except:
                            print(common.RED + "ERROR: " + common.RESET + " unable to upload object to OSS " + object_name)
                            pass
                else:
                    dir = args.fname + os.path.sep + "*"
                    proc_list = []

                    for f in glob(dir):
                        if os.path.isfile(f):
                            print("INFO: starting upload for {}".format(f))
                            p = Process(target=upload_to_object_storage, args=(config, namespace, bucket, f, profile))
                            p.start()
                            proc_list.append(p)

                    print()
                    for job in proc_list:
                        job.join()
                    print()
    else:
        print(common.RED + "ERROR: " + common.RESET + " please provide a profile for operations\n")
        parser.parse_args(['-h'])

if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print(common.RED + "\nCaught KeyboardInterrupt, exiting...\n" + common.RESET)
        return_code = 1
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

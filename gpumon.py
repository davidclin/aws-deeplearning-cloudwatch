# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  or in the "license" file accompanying this file. This file is distributed
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#  express or implied. See the License for the specific language governing
#  permissions and limitations under the License.

import urllib2
import boto3
import os
from pynvml import *
from datetime import datetime
from time import sleep

### CHOOSE REGION ####
EC2_REGION = 'us-east-1'
print "EC2_REGION is " + str(EC2_REGION)

###USE AWS INSTANCE NAME OBTAINED FROM get_ec2_name.sh##
my_NameSpace = os.environ["TAG_VALUE"]
print "my_NameSpace is " + str(my_NameSpace)

### CHOOSE PUSH INTERVAL ####
sleep_interval = 10
print "Push interval is " + str(sleep_interval) + "seconds"

### CHOOSE STORAGE RESOLUTION (BETWEEN 1-60) ####
store_reso = 1
print "Storage resolution is " + str(store_reso) + "seconds"

print "Obtaining instance information ..."
#Instance information
BASE_URL = 'http://169.254.169.254/latest/meta-data/'
INSTANCE_ID = urllib2.urlopen(BASE_URL + 'instance-id').read()
IMAGE_ID = urllib2.urlopen(BASE_URL + 'ami-id').read()
INSTANCE_TYPE = urllib2.urlopen(BASE_URL + 'instance-type').read()
INSTANCE_AZ = urllib2.urlopen(BASE_URL + 'placement/availability-zone').read()
EC2_REGION = INSTANCE_AZ[:-1]

TIMESTAMP = datetime.now().strftime('%Y-%m-%dT%H')
TMP_FILE = '/tmp/GPU_TEMP'
TMP_FILE_SAVED = TMP_FILE + TIMESTAMP

print "Creating CloudWatch client ..."
# Create CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name=EC2_REGION)


# Flag to push to CloudWatch
PUSH_TO_CW = True

def getPowerDraw(handle):
    try:
        print "Getting power draw ..."
        powDraw = nvmlDeviceGetPowerUsage(handle) / 1000.0
        powDrawStr = '%.2f' % powDraw
    except NVMLError as err:
        powDrawStr = handleError(err)
        PUSH_TO_CW = False
    return powDrawStr

def getTemp(handle):
    try:
        print "Getting temperature ..."
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
    except NVMLError as err:
        temp = handleError(err)
        PUSH_TO_CW = False
    return temp

def getUtilization(handle):
    try:
        print "Getting utilization ..."
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_util = str(util.gpu)
        mem_util = str(util.memory)
    except NVMLError as err:
        error = handleError(err)
        gpu_util = error
        mem_util = error
        PUSH_TO_CW = False
    return util, gpu_util, mem_util

def logResults(i, util, gpu_util, mem_util, powDrawStr, temp):
    try:
        gpu_logs = open(TMP_FILE_SAVED, 'a+')
        writeString = str(i) + ',' + gpu_util + ',' + mem_util + ',' + powDrawStr + ',' + temp + '\n'
        gpu_logs.write(writeString)
    except:
        print("Error writing to file ", gpu_logs)
    finally:
        gpu_logs.close()
    if (PUSH_TO_CW):
        MY_DIMENSIONS=[
                    {
                        'Name': 'InstanceId',
                        'Value': INSTANCE_ID
                    },
                    {
                        'Name': 'ImageId',
                        'Value': IMAGE_ID
                    },
                    {
                        'Name': 'InstanceType',
                        'Value': INSTANCE_TYPE
                    },
                    {
                        'Name': 'GPUNumber',
                        'Value': str(i)
                    }
                ]
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'GPU Usage',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'Percent',
                    'StorageResolution': store_reso,
                    'Value': util.gpu
                },
                {
                    'MetricName': 'Memory Usage',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'Percent',
                    'StorageResolution': store_reso,
                    'Value': util.memory
                },
                {
                    'MetricName': 'Power Usage (Watts)',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'None',
                    'StorageResolution': store_reso,
                    'Value': float(powDrawStr)
                },
                {
                    'MetricName': 'Temperature (C)',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'None',
                    'StorageResolution': store_reso,
                    'Value': int(temp)
                },
        ],
            Namespace=my_NameSpace
        )


nvmlInit()
deviceCount = nvmlDeviceGetCount()

def main():
    try:
        while True:
            PUSH_TO_CW = True
            # Find the metrics for each GPU on instance
            print "Finding metrics for each GPU on instance ..."
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)

                powDrawStr = getPowerDraw(handle)
                temp = getTemp(handle)
                util, gpu_util, mem_util = getUtilization(handle)
                logResults(i, util, gpu_util, mem_util, powDrawStr, temp)

            sleep(sleep_interval)

    finally:
        print "Shutting down NVML"
        nvmlShutdown()

if __name__=='__main__':
    main()

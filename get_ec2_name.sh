#!/bin/bash
export TAG_VALUE
KEY=Name
INSTANCE_ID=$(ec2metadata --instance-id)
REGION=us-east-1
TAG_VALUE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=$KEY" --region=$REGION --output=text | cut -f5)
python /home/ubuntu/gpumon.py

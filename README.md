# aws-deeplearning-cloudwatch

This repository is inspired by the blog titled "Monitoring GPU Utilization with Amazon CloudWatch"
https://aws.amazon.com/blogs/machine-learning/monitoring-gpu-utilization-with-amazon-cloudwatch/

These scripts improve upon the example provided in the blog by allowing Deep Learning (DL) EC2 instances to post GPU performance metrics to CloudWatch using the EC tag name as the namespace. These scripts can further be extended by integrating into a CI/CD Jenkins pipeline where the shell script get_ec2_name.sh is provided as user data to each DL EC2 slave instance.

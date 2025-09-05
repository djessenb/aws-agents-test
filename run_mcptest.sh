#!/bin/bash

# Set AWS profile (no interactive prompt needed!)
export AWS_PROFILE=ts-workload-test-admin

# Run the Python script
echo "Running with AWS profile: $AWS_PROFILE"
python3 agent.py
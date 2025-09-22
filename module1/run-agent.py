#!/usr/bin/env python3
"""
AWS Agent Runner with Profile Selection
"""
import os
import sys
import subprocess
from typing import List

def get_available_profiles() -> List[str]:
    """Get list of available AWS profiles"""
    try:
        result = subprocess.run(['aws', 'configure', 'list-profiles'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def set_profile_and_run(profile: str, query: str = None):
    """Set AWS profile and run the agent"""
    os.environ['AWS_PROFILE'] = profile
    
    print(f"🚀 Running agent with profile: {profile}")
    print(f"📍 Region: eu-central-1")
    print(f"🤖 Model: claude-3-5-sonnet-20241022")
    print("-" * 50)
    
    # Import and run the agent
    from agent import agent
    
    if query:
        result = agent(query)
        print(f"Result: {result}")
    else:
        # Interactive mode
        print("Enter your questions (type 'quit' to exit):")
        while True:
            user_input = input("\n> ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            if user_input.strip():
                result = agent(user_input)
                print(f"Result: {result}")

def main():
    profiles = get_available_profiles()
    
    if not profiles:
        print("❌ No AWS profiles found. Please configure AWS CLI first.")
        sys.exit(1)
    
    print("Available AWS Profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"  {i}. {profile}")
    
    try:
        choice = input(f"\nSelect profile (1-{len(profiles)}) or enter profile name: ").strip()
        
        # Handle numeric selection
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                selected_profile = profiles[idx]
            else:
                print("❌ Invalid selection")
                sys.exit(1)
        else:
            # Handle direct profile name
            if choice in profiles:
                selected_profile = choice
            else:
                print(f"❌ Profile '{choice}' not found")
                sys.exit(1)
        
        # Check if profile has access
        print(f"🔍 Checking access for profile: {selected_profile}")
        try:
            result = subprocess.run(['aws', 'sts', 'get-caller-identity', '--profile', selected_profile], 
                                  capture_output=True, text=True, check=True)
            print("✅ Profile access confirmed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Profile access failed: {e.stderr}")
            sys.exit(1)
        
        # Get query from command line or run interactively
        query = sys.argv[1] if len(sys.argv) > 1 else None
        set_profile_and_run(selected_profile, query)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

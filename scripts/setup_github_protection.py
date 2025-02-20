"""
Script to set up GitHub branch protection rules using the REST API.
Requires requests package and a GitHub token with repo access.

Usage:
    python setup_github_protection.py --token YOUR_GITHUB_TOKEN
"""

import argparse
import requests
import sys
import json

def setup_branch_protection(token: str):
    """Set up branch protection rules for main and cloud branches."""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    
    protection_rules = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["validate-cloud"]
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False
    }
    
    repo = "eljapo22/modularized_app4"
    branches = ["main", "cloud"]
    
    for branch in branches:
        url = f"https://api.github.com/repos/{repo}/branches/{branch}/protection"
        
        try:
            response = requests.put(url, headers=headers, json=protection_rules)
            if response.status_code == 200:
                print(f" {branch} branch protection rules set")
            else:
                print(f"Failed to set {branch} branch protection:")
                print(json.dumps(response.json(), indent=2))
                if "documentation_url" in response.json():
                    print(f"See: {response.json()['documentation_url']}")
        except Exception as e:
            print(f"Error setting {branch} branch protection: {str(e)}")
            if branch == "cloud":
                print("This is normal if the cloud branch doesn't exist yet.")
            else:
                sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="GitHub token with repo access")
    args = parser.parse_args()
    
    setup_branch_protection(args.token)

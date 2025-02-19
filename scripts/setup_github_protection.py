"""
Script to set up GitHub branch protection rules.
Requires PyGithub package and a GitHub token with repo access.

Usage:
    python setup_github_protection.py --token YOUR_GITHUB_TOKEN
"""

import argparse
from github import Github
import sys

def setup_branch_protection(token: str):
    """Set up branch protection rules for main and cloud branches."""
    try:
        # Initialize GitHub client
        g = Github(token)
        
        # Get repository
        repo = g.get_repo("eljapo22/modularized_app4")
        
        # Protection rules for main branch
        main_branch = repo.get_branch("main")
        main_branch.edit_protection(
            strict=True,  # Require branches to be up to date
            require_code_owner_reviews=True,
            required_approving_review_count=1,
            enforce_admins=True,
            dismiss_stale_reviews=True,
            require_status_checks=True,
            required_status_checks=["validate-cloud"],
            include_admins=True
        )
        print("✓ Main branch protection rules set")
        
        # Protection rules for cloud branch
        cloud_branch = repo.get_branch("cloud")
        cloud_branch.edit_protection(
            strict=True,
            require_code_owner_reviews=True,
            required_approving_review_count=1,
            enforce_admins=True,
            dismiss_stale_reviews=True,
            require_status_checks=True,
            required_status_checks=["validate-cloud"],
            include_admins=True
        )
        print("✓ Cloud branch protection rules set")
        
    except Exception as e:
        print(f"Error setting up branch protection: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="GitHub token with repo access")
    args = parser.parse_args()
    
    setup_branch_protection(args.token)

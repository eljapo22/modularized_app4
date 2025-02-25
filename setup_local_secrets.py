"""
Script to set up local secrets for development
"""
import os
import toml

# Create .streamlit directory if it doesn't exist
os.makedirs('.streamlit', exist_ok=True)

# Secrets configuration
secrets = {
    'MOTHERDUCK_TOKEN': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImpobmFwbzIyMTNAZ21haWwuY29tIiwic2Vzc2lvbiI6ImpobmFwbzIyMTMuZ21haWwuY29tIiwicGF0IjoibTl6dmIzUzRCbnUxWTZSOTRCVVRKb2ZCbDNPZno5MzJ0TmdacTNkVjIyVSIsInVzZXJJZCI6IjI4Mzg5MGMwLTZhYmEtNDIyZi04OTI1LWQyNTg0YjJiZmU1NiIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTc0MDAzNDYzOX0.GF9qa32LWZNnUsRyAsLsHhxZb8oug5_lUrnIAIWSVjU',
    'USE_MOTHERDUCK': 'true',
    'DEFAULT_RECIPIENT': 'jhnapo2213@gmail.com'
}

# Write secrets to .streamlit/secrets.toml
with open('.streamlit/secrets.toml', 'w') as f:
    toml.dump(secrets, f)

print("✓ Local secrets configured successfully")

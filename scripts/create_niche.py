#!/usr/bin/env python3
"""
create_niche.py - Create a new niche by copying the template
"""

import os
import shutil
import sys

def create_niche(niche_name):
    template_dir = 'template'
    niche_dir = f'niches/{niche_name}'

    if os.path.exists(niche_dir):
        print(f"Niche {niche_name} already exists!")
        return

    shutil.copytree(template_dir, niche_dir)
    print(f"Created niche: {niche_name}")

    # Create niche-specific .env
    env_content = f"""# Niche-specific environment for {niche_name}
NICHE={niche_name}

# Copy and customize from .env.example
"""
    with open(f'{niche_dir}/.env', 'w') as f:
        f.write(env_content)

    print(f"Created {niche_dir}/.env")

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_niche.py <niche_name>")
        return
    niche_name = sys.argv[1]
    create_niche(niche_name)

if __name__ == '__main__':
    main()
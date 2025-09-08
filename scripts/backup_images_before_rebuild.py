#!/usr/bin/env python3
"""
Script to backup current images with their txt file associations before running build_from_google_sheets.py
This ensures we can restore images to the correct projects after the ui_x numbering changes.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def backup_current_images():
    """Backup all images with their associated txt file names for later restoration."""
    projects_dir = Path("docs/public/projects")
    backup_dir = Path("docs/public/projects_image_backup")
    
    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = backup_dir / f"backup_{timestamp}"
    backup_root.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 Creating image backup in: {backup_root}")
    
    # Store mapping of txt files to their images
    mapping = {}
    backed_up_projects = 0
    total_images = 0
    
    # Get all ui_x folders
    ui_folders = [f for f in projects_dir.iterdir() if f.is_dir() and f.name.startswith('ui_')]
    
    for ui_folder in sorted(ui_folders):
        print(f"📂 Processing {ui_folder.name}...")
        
        # Find txt file(s) in this folder
        txt_files = list(ui_folder.glob("*.txt"))
        if not txt_files:
            print(f"  ⚠️  No txt file found in {ui_folder.name}")
            continue
            
        txt_file = txt_files[0]  # Use first txt file
        txt_filename = txt_file.name
        
        # Check for images
        images_dir = ui_folder / "images"
        if not images_dir.exists():
            print(f"  ⚠️  No images directory in {ui_folder.name}")
            continue
            
        # Get all image files
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            image_files.extend(images_dir.glob(f"*{ext}"))
            image_files.extend(images_dir.glob(f"*{ext.upper()}"))
            
        if not image_files:
            print(f"  ⚠️  No image files found in {ui_folder.name}/images")
            continue
            
        # Create backup folder for this project
        project_backup_dir = backup_root / ui_folder.name
        project_backup_dir.mkdir(exist_ok=True)
        
        # Copy txt file
        shutil.copy2(txt_file, project_backup_dir / txt_filename)
        
        # Copy images
        images_backup_dir = project_backup_dir / "images"
        images_backup_dir.mkdir(exist_ok=True)
        
        copied_images = []
        for image_file in image_files:
            try:
                dest_path = images_backup_dir / image_file.name
                shutil.copy2(image_file, dest_path)
                copied_images.append(image_file.name)
                total_images += 1
            except Exception as e:
                print(f"  ❌ Error copying {image_file}: {e}")
                
        if copied_images:
            mapping[txt_filename] = {
                'original_folder': ui_folder.name,
                'images': copied_images,
                'backup_path': str(project_backup_dir)
            }
            backed_up_projects += 1
            print(f"  ✅ Backed up {len(copied_images)} images for {txt_filename}")
        
    # Save mapping file
    mapping_file = backup_root / "image_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
        
    print(f"\n📋 Backup Summary:")
    print(f"   📂 Projects backed up: {backed_up_projects}")
    print(f"   🖼️  Total images backed up: {total_images}")
    print(f"   💾 Backup location: {backup_root}")
    print(f"   📝 Mapping file: {mapping_file}")
    
    return str(backup_root), str(mapping_file)

if __name__ == "__main__":
    print("🔒 Starting image backup before rebuild...")
    backup_path, mapping_path = backup_current_images()
    print(f"\n✅ Backup completed!")
    print(f"   You can now safely run build_from_google_sheets.py")
    print(f"   After that, use the restoration script with: {mapping_path}")

#!/usr/bin/env python3
"""
Script to restore images to the correct projects after build_from_google_sheets.py has reshuffled ui_x folders.
This matches txt file names between the backup and current structure to put images back in the right places.
"""

import os
import shutil
import json
from pathlib import Path

def find_txt_file_in_folder(folder_path):
    """Find the txt file in a ui_x folder."""
    folder_path = Path(folder_path)
    txt_files = list(folder_path.glob("*.txt"))
    if txt_files:
        return txt_files[0].name
    return None

def restore_images_from_backup(backup_mapping_file):
    """Restore images based on txt file name matching."""
    
    # Load the backup mapping
    with open(backup_mapping_file, 'r', encoding='utf-8') as f:
        backup_mapping = json.load(f)
    
    projects_dir = Path("docs/public/projects")
    
    print(f"🔄 Starting image restoration using mapping: {backup_mapping_file}")
    print(f"📂 Looking for current projects in: {projects_dir}")
    
    # Get current ui_x folders and their txt files
    current_folders = {}
    ui_folders = [f for f in projects_dir.iterdir() if f.is_dir() and f.name.startswith('ui_')]
    
    for ui_folder in sorted(ui_folders):
        txt_filename = find_txt_file_in_folder(ui_folder)
        if txt_filename:
            current_folders[txt_filename] = ui_folder
            print(f"📝 Found current: {ui_folder.name} -> {txt_filename}")
    
    print(f"\n🔍 Matching backup images to current folders...")
    
    successful_restorations = 0
    failed_restorations = 0
    total_images_copied = 0
    
    # For each backed up project, find its new location
    for backup_txt_filename, backup_info in backup_mapping.items():
        print(f"\n🔎 Processing backup: {backup_txt_filename}")
        
        if backup_txt_filename in current_folders:
            # Found exact match
            current_folder = current_folders[backup_txt_filename]
            backup_path = Path(backup_info['backup_path'])
            
            print(f"  ✅ Match found: {backup_info['original_folder']} -> {current_folder.name}")
            
            # Copy images from backup to current folder
            backup_images_dir = backup_path / "images"
            current_images_dir = current_folder / "images"
            
            if not backup_images_dir.exists():
                print(f"  ⚠️  No backup images directory found: {backup_images_dir}")
                failed_restorations += 1
                continue
            
            # Ensure current images directory exists
            current_images_dir.mkdir(exist_ok=True)
            
            # Remove any existing images first
            existing_images = []
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                existing_images.extend(current_images_dir.glob(f"*{ext}"))
                existing_images.extend(current_images_dir.glob(f"*{ext.upper()}"))
            
            for existing_image in existing_images:
                try:
                    existing_image.unlink()
                    print(f"    🗑️  Removed existing: {existing_image.name}")
                except Exception as e:
                    print(f"    ❌ Error removing {existing_image}: {e}")
            
            # Copy backup images
            copied_images = 0
            for image_name in backup_info['images']:
                backup_image_path = backup_images_dir / image_name
                target_image_path = current_images_dir / image_name
                
                if backup_image_path.exists():
                    try:
                        shutil.copy2(backup_image_path, target_image_path)
                        copied_images += 1
                        total_images_copied += 1
                        print(f"    📸 Copied: {image_name}")
                    except Exception as e:
                        print(f"    ❌ Error copying {image_name}: {e}")
                else:
                    print(f"    ⚠️  Backup image not found: {backup_image_path}")
            
            if copied_images > 0:
                successful_restorations += 1
                print(f"  ✅ Successfully restored {copied_images} images to {current_folder.name}")
            else:
                failed_restorations += 1
                print(f"  ❌ Failed to restore any images to {current_folder.name}")
        else:
            print(f"  ❌ No current folder found for: {backup_txt_filename}")
            failed_restorations += 1
    
    print(f"\n📊 Restoration Summary:")
    print(f"   ✅ Successful restorations: {successful_restorations}")
    print(f"   ❌ Failed restorations: {failed_restorations}")
    print(f"   📸 Total images copied: {total_images_copied}")
    
    return successful_restorations, failed_restorations, total_images_copied

def main():
    # Auto-detect the most recent backup
    backup_dir = Path("docs/public/projects_image_backup")
    
    if not backup_dir.exists():
        print("❌ No backup directory found!")
        return
    
    backup_folders = [f for f in backup_dir.iterdir() if f.is_dir() and f.name.startswith('backup_')]
    
    if not backup_folders:
        print("❌ No backup folders found!")
        return
    
    # Get the most recent backup
    latest_backup = max(backup_folders, key=lambda x: x.stat().st_mtime)
    mapping_file = latest_backup / "image_mapping.json"
    
    if not mapping_file.exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        return
    
    print(f"🔧 Using backup: {latest_backup.name}")
    print(f"📝 Using mapping: {mapping_file}")
    
    # Ask for confirmation
    response = input(f"\nProceed with image restoration? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    successful, failed, total_copied = restore_images_from_backup(mapping_file)
    
    if successful > 0:
        print(f"\n🎉 Image restoration completed!")
        print(f"   Run 'python scripts/generate_catalog.py' to update the website with restored images.")
    else:
        print(f"\n⚠️  No images were successfully restored. Please check the logs above.")

if __name__ == "__main__":
    main()

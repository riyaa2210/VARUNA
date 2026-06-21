"""
Dataset Preparation Script for Fire Detection
Helps organize Kaggle fire dataset into YOLO format

Steps:
1. Download from: https://www.kaggle.com/datasets/atulyakumar98/fire-and-gun-dataset
2. Extract the downloaded file
3. Run this script with the extracted folder path
"""

import os
import shutil
import argparse
from pathlib import Path
from sklearn.model_selection import train_test_split

def prepare_fire_dataset(input_folder, output_folder='datasets/fire', train_ratio=0.7, val_ratio=0.2):
    """
    Prepare fire detection dataset in YOLO format
    
    Expected input structure:
    - input_folder/
      - images/
        - fire/     (fire images)
        - non-fire/ (non-fire images, optional)
      - annotations/ (or labels with .txt files)
    """
    
    print("=" * 60)
    print("  📊 FIRE DATASET PREPARATION 📊")
    print("=" * 60)
    
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    if not input_path.exists():
        print(f"[ERROR] Input folder not found: {input_path}")
        return False
    
    # Create output structure
    for folder in ['images/train', 'images/val', 'images/test', 'labels/train', 'labels/val', 'labels/test']:
        (output_path / folder).mkdir(parents=True, exist_ok=True)
    
    print(f"\n[OK] Created output structure at: {output_path}")
    
    # Find fire images
    fire_images = []
    possible_fire_paths = [
        input_path / 'fire',
        input_path / 'images' / 'fire',
        input_path / 'Fire',
    ]
    
    for path in possible_fire_paths:
        if path.exists():
            fire_images = list(path.glob('*.jpg')) + list(path.glob('*.png')) + list(path.glob('*.jpeg'))
            print(f"[OK] Found {len(fire_images)} fire images in: {path}")
            break
    
    if not fire_images:
        print("[ERROR] No fire images found. Check your dataset structure.")
        print("\nExpected structure:")
        print("  input_folder/")
        print("    ├── fire/")
        print("    │   ├── image1.jpg")
        print("    │   ├── image2.jpg")
        print("    │   └── ...")
        print("    ├── annotations/ (optional, for labels)")
        return False
    
    print(f"[OK] Total fire images: {len(fire_images)}")
    
    # Split into train/val/test
    train_size = int(len(fire_images) * train_ratio)
    val_size = int(len(fire_images) * val_ratio)
    test_size = len(fire_images) - train_size - val_size
    
    train_imgs, temp_imgs = train_test_split(fire_images, train_size=train_size, random_state=42)
    val_imgs, test_imgs = train_test_split(temp_imgs, train_size=val_size, random_state=42)
    
    print(f"\n[SPLIT] Train: {len(train_imgs)} | Val: {len(val_imgs)} | Test: {len(test_imgs)}")
    
    # Copy images and create dummy labels if they don't exist
    def copy_split(images, split_name):
        for img in images:
            dest = output_path / 'images' / split_name / img.name
            shutil.copy(img, dest)
            
            # Create dummy label file if not exists
            label_path = output_path / 'labels' / split_name / (img.stem + '.txt')
            if not label_path.exists():
                # Dummy label: all fire with centered bounding box
                # Format: <class_id> <x_center> <y_center> <width> <height>
                with open(label_path, 'w') as f:
                    f.write("0 0.5 0.5 0.8 0.8\n")
        
        print(f"[OK] Copied {len(images)} {split_name} images")
    
    copy_split(train_imgs, 'train')
    copy_split(val_imgs, 'val')
    copy_split(test_imgs, 'test')
    
    print("\n" + "=" * 60)
    print("  ✅ DATASET PREPARED SUCCESSFULLY ✅")
    print("=" * 60)
    print(f"\nDataset location: {output_path}")
    print("\nNext steps:")
    print("1. Review the generated labels in datasets/fire/labels/")
    print("2. If you have proper YOLO format labels (.txt files), replace the dummy ones")
    print("3. Run: python train_fire_detection.py")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Prepare fire detection dataset for YOLO training')
    parser.add_argument('input_folder', type=str, help='Path to extracted Kaggle fire dataset')
    parser.add_argument('--output', type=str, default='datasets/fire', help='Output folder path')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='Training data ratio (0.0-1.0)')
    parser.add_argument('--val-ratio', type=float, default=0.2, help='Validation data ratio (0.0-1.0)')
    
    args = parser.parse_args()
    
    success = prepare_fire_dataset(
        args.input_folder,
        args.output,
        args.train_ratio,
        args.val_ratio
    )
    
    if not success:
        exit(1)

if __name__ == '__main__':
    # If no arguments provided, show example usage
    if len(__import__('sys').argv) == 1:
        print("=" * 60)
        print("  FIRE DATASET PREPARATION TOOL")
        print("=" * 60)
        print("\nUsage:")
        print("  python prepare_dataset.py <path_to_extracted_kaggle_dataset>")
        print("\nExample:")
        print("  python prepare_dataset.py ./fire-and-gun-dataset")
        print("  python prepare_dataset.py C:\\Downloads\\fire_dataset --output datasets/fire")
        print("\nRequired:")
        print("  - sklearn (pip install scikit-learn)")
        print("\nDataset source:")
        print("  https://www.kaggle.com/datasets/atulyakumar98/fire-and-gun-dataset")
    else:
        main()

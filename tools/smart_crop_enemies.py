"""
Smart Sprite Cropper for Enemy Assets
Crops sprites dengan konsistensi per enemy untuk menghindari floating/jumping sprites.

Workflow:
1. Untuk setiap enemy, scan SEMUA frames dari SEMUA actions
2. Temukan bounding box TERLUAS yang mencakup semua pixel berwarna
3. Crop SEMUA frames dengan bounding box yang SAMA
4. Bottom-align: pixel berwarna paling bawah touch bottom frame
"""

import os
from PIL import Image
import shutil

def get_pixel_bounds(image):
    """
    Scan image untuk menemukan bounding box dari pixel berwarna (non-transparent).
    Returns: (left, top, right, bottom) atau None jika semua transparent
    """
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    pixels = image.load()
    width, height = image.size
    
    # Find bounds
    left = width
    top = height
    right = 0
    bottom = 0
    
    found_pixel = False
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # Check if pixel is not transparent (alpha > threshold)
            if a > 10:  # Threshold untuk menghindari semi-transparent artifacts
                found_pixel = True
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    
    if not found_pixel:
        return None
    
    return (left, top, right, bottom)


def get_unified_bounds_for_enemy(enemy_path):
    """
    Scan SEMUA frames dari SEMUA actions untuk enemy ini.
    Returns bounding box terluas yang mencakup semua frames.
    """
    unified_left = float('inf')
    unified_top = float('inf')
    unified_right = 0
    unified_bottom = 0
    
    total_frames = 0
    
    # Iterate through all action folders
    for action_folder in os.listdir(enemy_path):
        action_path = os.path.join(enemy_path, action_folder)
        
        if not os.path.isdir(action_path):
            continue
        
        # Iterate through all frames in this action
        for filename in os.listdir(action_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(action_path, filename)
                
                try:
                    img = Image.open(filepath)
                    bounds = get_pixel_bounds(img)
                    
                    if bounds:
                        left, top, right, bottom = bounds
                        unified_left = min(unified_left, left)
                        unified_top = min(unified_top, top)
                        unified_right = max(unified_right, right)
                        unified_bottom = max(unified_bottom, bottom)
                        total_frames += 1
                    
                    img.close()
                except Exception as e:
                    print(f"[ERROR] Failed to process {filepath}: {e}")
    
    if total_frames == 0:
        return None
    
    print(f"  Scanned {total_frames} frames")
    print(f"  Unified bounds: left={unified_left}, top={unified_top}, right={unified_right}, bottom={unified_bottom}")
    
    return (unified_left, unified_top, unified_right, unified_bottom)


def crop_and_align_sprite(image, unified_bounds, original_width, original_height):
    """
    Crop sprite dengan unified bounds dan bottom-align.
    
    Args:
        image: PIL Image
        unified_bounds: (left, top, right, bottom) - bounds dari semua frames
        original_width: lebar original image
        original_height: tinggi original image
    
    Returns:
        Cropped image
    """
    left, top, right, bottom = unified_bounds
    
    # Calculate content size
    content_width = right - left + 1
    content_height = bottom - top + 1
    
    # Determine horizontal centering
    # Standard sprite: center the content horizontally
    horizontal_padding = 10  # Padding kiri-kanan
    new_width = content_width + (2 * horizontal_padding)
    
    # Vertical: bottom-align (pixel berwarna paling bawah touch bottom)
    vertical_padding_top = 10  # Padding atas
    new_height = content_height + vertical_padding_top
    
    # Create new image with calculated size
    new_img = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    
    # Calculate paste position
    # Horizontal: center
    paste_x = horizontal_padding
    # Vertical: bottom-align (content bottom touches new image bottom)
    paste_y = new_height - content_height
    
    # Crop content from original
    content = image.crop((left, top, right + 1, bottom + 1))
    
    # Paste into new image
    new_img.paste(content, (paste_x, paste_y))
    
    return new_img


def process_enemy_folder(enemy_name, enemy_path, output_base_path):
    """
    Process semua sprites untuk satu enemy dengan unified cropping.
    """
    print(f"\n[PROCESSING] {enemy_name}")
    
    # Step 1: Get unified bounds dari semua frames
    unified_bounds = get_unified_bounds_for_enemy(enemy_path)
    
    if not unified_bounds:
        print(f"  [SKIP] No valid frames found")
        return
    
    left, top, right, bottom = unified_bounds
    content_width = right - left + 1
    content_height = bottom - top + 1
    
    print(f"  Content size: {content_width}x{content_height}")
    
    # Step 2: Create output directory
    output_enemy_path = os.path.join(output_base_path, enemy_name)
    os.makedirs(output_enemy_path, exist_ok=True)
    
    # Step 3: Process all frames with unified bounds
    processed_count = 0
    
    for action_folder in os.listdir(enemy_path):
        action_path = os.path.join(enemy_path, action_folder)
        
        if not os.path.isdir(action_path):
            continue
        
        output_action_path = os.path.join(output_enemy_path, action_folder)
        os.makedirs(output_action_path, exist_ok=True)
        
        for filename in os.listdir(action_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                input_filepath = os.path.join(action_path, filename)
                output_filepath = os.path.join(output_action_path, filename)
                
                try:
                    img = Image.open(input_filepath)
                    original_width, original_height = img.size
                    
                    # Crop and align dengan unified bounds
                    cropped_img = crop_and_align_sprite(img, unified_bounds, original_width, original_height)
                    
                    # Save
                    cropped_img.save(output_filepath, 'PNG')
                    
                    img.close()
                    cropped_img.close()
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"  [ERROR] Failed to crop {filename}: {e}")
    
    print(f"  [DONE] Cropped {processed_count} frames")


def main():
    """Main processing function."""
    print("=" * 60)
    print("SMART SPRITE CROPPER - Enemy Assets")
    print("=" * 60)
    
    # Base paths
    base_enemy_path = 'assets/graphics/enemies'
    output_base_path = 'assets/graphics/enemies_cropped'
    
    # Create output directory
    if os.path.exists(output_base_path):
        shutil.rmtree(output_base_path)
    os.makedirs(output_base_path)
    
    # Enemy categories
    categories = {
        'dungeon_monster': ['boss_demon_slime', 'bringer_of_death', 'Skullwolf'],
        'grass_monster': ['Flying eye', 'Goblin', 'Mushroom', 'Skeleton'],
        'ice_monster': ['golem', 'guardian']
    }
    
    total_enemies = 0
    
    for category, enemies in categories.items():
        category_path = os.path.join(base_enemy_path, category)
        output_category_path = os.path.join(output_base_path, category)
        
        if not os.path.exists(category_path):
            print(f"\n[SKIP] Category not found: {category}")
            continue
        
        os.makedirs(output_category_path, exist_ok=True)
        
        print(f"\n{'=' * 60}")
        print(f"CATEGORY: {category}")
        print(f"{'=' * 60}")
        
        for enemy_name in enemies:
            enemy_path = os.path.join(category_path, enemy_name)
            
            if not os.path.exists(enemy_path):
                print(f"\n[SKIP] Enemy not found: {enemy_name}")
                continue
            
            process_enemy_folder(enemy_name, enemy_path, output_category_path)
            total_enemies += 1
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE! Processed {total_enemies} enemies")
    print(f"Output: {output_base_path}")
    print(f"{'=' * 60}")
    
    # Instructions
    print("\n[NEXT STEPS]")
    print("1. Review cropped sprites in:", output_base_path)
    print("2. If satisfied, backup original and replace:")
    print(f"   Move {output_base_path}/* to {base_enemy_path}/")
    print("3. Test in-game to verify sprites are grounded correctly")


if __name__ == "__main__":
    main()

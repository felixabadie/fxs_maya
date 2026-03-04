from pathlib import Path
from typing import List, Tuple
import re
import random
import shutil
from data_generation import dict_export_path, image_export_path
from const import split_data_path


#Input directories for images and JSONs
JSON_DIR = Path(dict_export_path)
IMAGE_DIR = Path(image_export_path)

#Output base directory
OUTPUT_DIR = Path(split_data_path)

#Split ratio
SPLIT_RATIOS = {
    "train": 0.7,
    "val": 0.2,
    "test": 0.1
}

#File extensions
IMAGE_EXT = ".jpg"
JSON_EXT = ".json"


#Random Seed
SEED = 42


def get_sorted_file_list(directory: Path, ext: str) -> List[Path]:

    """sorts files according to index umber"""
   
    files = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == ext.lower()]

    # Extract number using regex
    def extract_number(file: Path):
        match = re.search(r'\d+', file.stem)
        return int(match.group()) if match else -1                                  #Use -1 to push non-numeric files to the start
    
    return sorted(files, key=extract_number) 


def split_indices(total: int, ratios: dict) -> Tuple[List[int], List[int], List[int]]:

    """shuffles data with predetermind seed and creates split for training/validation/test"""
   
    indices = list(range(total))
    random.seed(SEED)
    random.shuffle(indices)

    train_end = int(ratios["train"] * total)
    val_end = train_end + int(ratios["val"] * total)

    return (
        indices[:train_end],
        indices[train_end:val_end],
        indices[val_end:]
    )


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def move_files(src_files: List[Path], dst_dir: Path):
    for file in src_files:
        destination = dst_dir / file.name
        shutil.move(file, destination)


#Hauptlogik
def main():

    """
    Main Logic: Reads files, sorts them by index, shuffles data, splits data into

    split_data
     ├── images
     │ ├── test
     │ ├── train
     │ └── validation
     └── labels
        ├── test
        ├── train
        └── val

    """

    print("Starting dataset split")
    print(f"Reading images from: {IMAGE_DIR.resolve()}")
    print(f"Reading JSONs from: {JSON_DIR.resolve()}")

    # Get sorted files
    image_files = get_sorted_file_list(IMAGE_DIR, IMAGE_EXT)
    print(image_files)
    json_files = get_sorted_file_list(JSON_DIR, JSON_EXT)
    print(json_files)


    image_dict = {f.stem: f for f in image_files}
    json_dict = {f.stem: f for f in json_files}
    common_keys = sorted(set(image_dict.keys()) & set(json_dict.keys()))

    image_files = [image_dict[k] for k in common_keys]
    json_files = [json_dict[k] for k in common_keys]

    
    if len(image_files) != len(json_files):
        raise ValueError(
            f"Mismatch: found {len(image_files)} images and {len(json_files)} JSON files. "
        )
    
    total_files = len(image_files)

    if total_files == 0:
        raise ValueError("Keine Dateien gefunden")

    # Get shuffled, split indices
    train_idx, val_idx, test_idx = split_indices(total_files, SPLIT_RATIOS)

    
    # Map indices to file lists
    split_map = {
        "train": ([image_files[i] for i in train_idx], [json_files[i] for i in train_idx]),
        "val":   ([image_files[i] for i in val_idx],   [json_files[i] for i in val_idx]),
        "test":  ([image_files[i] for i in test_idx],  [json_files[i] for i in test_idx]),
    }


    # For each split, move files to appropriate output directories
    for split_name, (img_list, json_list) in split_map.items():
        img_out_dir = OUTPUT_DIR / "images" / split_name
        json_out_dir = OUTPUT_DIR / "labels" / split_name

        ensure_dir(img_out_dir)
        ensure_dir(json_out_dir)

        move_files(img_list, img_out_dir)
        move_files(json_list, json_out_dir)

    print("Data split and moved.")


if __name__ == "__main__":
    main()
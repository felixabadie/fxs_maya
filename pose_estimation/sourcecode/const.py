from pathlib import Path

PROJECT_BASE_DIR = Path(__file__).parent

FILE_DIR = PROJECT_BASE_DIR.parent.parent

training_data_path = FILE_DIR / r"bachelor\bachelor_training_data"

split_data_path = FILE_DIR / r"bachelor\split_data"
ml_model_save_dir = FILE_DIR / r"bachelor"

best_model_dir = PROJECT_BASE_DIR / "best_model.pth"

active_mask_path = PROJECT_BASE_DIR / "active_rotation_values.json"
server_icon = PROJECT_BASE_DIR / "pose_server" / "favicon_02.ico"
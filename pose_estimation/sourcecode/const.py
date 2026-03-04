from pathlib import Path

project_base_dir = Path(__file__).parent

training_data_path = r"---------------- placeholder -----------------"

split_data_path = r"---------------- placeholder -----------------"
ml_model_save_dir = r"---------------- placeholder -----------------"

best_model_dir = project_base_dir / "best_model.pth"

active_mask_path = project_base_dir / "active_rotation_values.json"
server_icon = project_base_dir / "pose_server" / "favicon_02.ico"
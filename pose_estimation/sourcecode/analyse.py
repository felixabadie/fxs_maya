from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import json
import cv2
import os

tpose_ref = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss\tpose_ref.jpg"
export_dir = Path(r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss")
reassign_joint_dir = r"N:\Artists\Felix\Bachelor\venv\reassign_joints.json"

dict_export_path = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss"
indices_path = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\models\combination_active_inputs_v11\active_indices.json"


with open(indices_path, 'r') as f:
    training_active_indices = json.load(f)["active_indices"]




#exportiert alle Rotationswerte als Python Dict in einer JSON Datei. Datei wird zu dict_export_path gespeichert
def export_json_data(data, dict_export_path):
    filename = "axis_influence.json"
    full_path = os.path.join(dict_export_path, filename)
    
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)


def compare_image(viewport_image, ref_image):
    input_img = cv2.imread(viewport_image, cv2.IMREAD_GRAYSCALE)
    ref_img = cv2.imread(ref_image, cv2.IMREAD_GRAYSCALE)
    
    if input_img is None:
        raise ValueError(f"Konnte Bild nicht laden: {viewport_image}")
    if ref_img is None:
        raise ValueError(f"Konnte Referenzbild nicht laden: {ref_image}")
    
    score, *_ = ssim(input_img, ref_img, full=True)
    return score


def merge_active_and_passive_values(active_axis_influence, joint_rotation_axis):
    full_axis_influence = {}
    active_rotation_axis = list(active_axis_influence.keys())
    
    found_matches = 0
    for axis in joint_rotation_axis:
        if axis in active_rotation_axis:
            full_axis_influence[axis] = active_axis_influence[axis]
            found_matches += 1
            print(f"  ✓ {axis}: {active_axis_influence[axis]:.6f}")
        else:
            full_axis_influence[axis] = 0
            # Nur erste 5 Nullwerte anzeigen

    return full_axis_influence


def visualize(joint_axis, axis_influence):
    fontsize_var = 14
   
    fig, (ax1) = plt.subplots(1, 1, figsize=(16, 10))
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
    x_labels = joint_axis
    x_pos = np.arange(len(axis_influence))
    #x_pos = np.arange(len(joint_axis))
    
    
    bars = ax1.bar(x_pos, axis_influence, color="green", alpha=0.7)
    ax1.set_xlabel("Joint Axes", fontsize = fontsize_var)
    ax1.set_ylabel("Normalized Silhouette Change", fontsize = fontsize_var)
    #ax1.set_title("Average Influence of Axis over Silhouette", fontsize = fontsize_var)
    ax1.set_xticks(x_pos)
    
    # Dynamische Y-Achse basierend auf tatsächlichen Werten
    max_val = max(axis_influence) if axis_influence else 0.1

    y_ticks = np.arange(0, max_val + 0.01, step=0.005)

    """if max_val > 0:
        step_size = max(0.01, max_val / 10)  # Mindestens 0.01, sonst max_val/10
        ax1.set_yticks(np.arange(0, max_val + step_size, step=step_size))
    else:
        ax1.set_yticks(np.arange(0, 0.1, step=0.02))"""
    
    ax1.set_yticks(y_ticks)
    ax1.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    ax1.grid(True, alpha=0.3)
    
    # Zeige Höhe der höchsten Balken
    for i, (bar, val) in enumerate(zip(bars, axis_influence)):
        if val > max_val * 0.01:  # Zeige nur Labels für Balken > 10% vom Maximum
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.01, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=12, rotation = 90)
    
    plt.tight_layout()
    plt.show()


# KORREKTUR: __name__ statt **name**
if __name__ == "__main__":
   
    active_axis_influence = {}
    
    for axis_folder in export_dir.iterdir():
        if not axis_folder.is_dir():
            continue
        
        ssim_scores = []
        
        # Debug: Zeige Bilder im Ordner
        images = list(axis_folder.glob("*.jpg"))
        
        for img_path in images:
            try:
                score = compare_image(str(img_path), tpose_ref)
                ssim_scores.append(score)
            except Exception as e:
                print(f"  FEHLER bei {img_path.name}: {e}")
        
        if ssim_scores:
            avg_scores = sum(ssim_scores) / len(ssim_scores)
            inv_avg_score = 1 - avg_scores
        else:
            print("  Keine gültigen SSIM-Scores gefunden")
            avg_scores = 0
            inv_avg_score = max(0, min(1, 1 - avg_scores))
        
        active_axis_influence[axis_folder.name] = inv_avg_score
    
    for key, value in active_axis_influence.items():
        print(f"{key}: {value:.6f}")
    
    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
   
    joint_rotation_axis = list(axis_dict.keys())

    active_joint_axis = [joint_rotation_axis[i] for i in training_active_indices]

    full_axis_influence = merge_active_and_passive_values(active_axis_influence, joint_rotation_axis)
    influence_values = list(full_axis_influence.values())
    active_influence_values = [full_axis_influence[axis] for axis in active_joint_axis]

    try:
        export_json_data(full_axis_influence, dict_export_path)
        print("exported successfully")
    except:
        print("EXPORT FAILED")
        

    #visualize(joint_rotation_axis, influence_values)
    visualize(active_joint_axis, active_influence_values)
import os
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score
from matplotlib.colors import LinearSegmentedColormap
from out_source_stuff import FilteredJointPoseDataSet, val_transform_method, AdaptiveShortNetwork5

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_path = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\models\combination_active_inputs_v11\best_model.pth"
indices_path = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\models\combination_active_inputs_v11\active_indices.json"

active_mask_path = r"N:\Artists\Felix\Bachelor\venv\active_rotation_values.json"

image_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\split_data_alternative\images\test"
label_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\split_data_alternative\labels\test"

color_image_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\color\images\tmp"
color_label_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\color\labels\tmp"

white_image_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\white\images\tmp"
white_label_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\white\labels\tmp"

black_and_white_image_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\black_and_white\images"
black_and_white_label_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\validation_data\black_and_white\labels"

train_image_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\split_data_alternative\images\train"
train_label_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\split_data_alternative\labels\train"

reassign_joint_dir = r"N:\Artists\Felix\Bachelor\venv\reassign_joints.json"

axis_influence_dir = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Auswertung_achseneinfluss\axis_influence.json"

#test_index = random.randint(0, 1999)
#test_index = 1448
test_index = 593

print("test_index: ", test_index)
test_images = os.listdir(image_dir)
color_test_images = os.listdir(color_image_dir)
white_test_images = os.listdir(white_image_dir)
file_name = test_images[test_index]
#file_name = color_test_images[test_index]
#file_name = white_test_images[test_index]
print(f"Testbild an Index {test_index}: {file_name}")


def merge_active_and_passive_values(pred_active, active_indices, full_length=51):
    full_output = np.zeros(full_length, dtype=np.float32)
    for i, idx in enumerate(active_indices):
        full_output[idx] = pred_active[i]
    return full_output


def get_all_indices(active_indices, full_length=51):
    full_output = np.zeros(full_length, dtype=np.float32)
    for i, idx in enumerate(active_indices):
        full_output[idx] = 1
    return full_output


with open(indices_path, 'r') as f:
    training_active_indices = json.load(f)["active_indices"]

print(f"Loaded {len(training_active_indices)} active indices: {training_active_indices}")



# === Dataset + Model ===
test_dataset = FilteredJointPoseDataSet(image_dir, label_dir, active_indices=training_active_indices, transform=val_transform_method, active_mask_path=active_mask_path)
color_dataset = FilteredJointPoseDataSet(color_image_dir, color_label_dir, active_indices=training_active_indices, transform=val_transform_method, active_mask_path=active_mask_path)
white_dataset = FilteredJointPoseDataSet(white_image_dir, white_label_dir, active_indices=training_active_indices, transform=val_transform_method, active_mask_path=active_mask_path)
black_and_white_dataset = FilteredJointPoseDataSet(black_and_white_image_dir, black_and_white_label_dir, active_indices=training_active_indices, transform=val_transform_method, active_mask_path=active_mask_path)

train_dataset = FilteredJointPoseDataSet(train_image_dir, train_label_dir, active_indices=training_active_indices, transform=val_transform_method, active_mask_path=active_mask_path)

print(f"Dataset created with {test_dataset.get_output_size()} active outputs")
print(f"Dataset active indices: {test_dataset.active_indices}")


current_dataset = test_dataset
current_label_dir = label_dir


# Konsistenz-Check
if test_dataset.active_indices != training_active_indices:
    print("⚠️ WARNING: Dataset active_indices differ from training!")
    print(f"Training: {training_active_indices}")
    print(f"Dataset:  {test_dataset.active_indices}")
else:
    print("Active indices are consistent with training")

#model = AdaptiveShortNetwork(output_size=len(training_active_indices))
model = AdaptiveShortNetwork5(output_size=len(training_active_indices))
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

print(f"Model loaded with output size: {len(training_active_indices)}")

# === Prediction Funktion ===
def predict(model, image_tensor):
    with torch.no_grad():
        return model(image_tensor).squeeze()



def visualize(pred_full, label_full, joint_axis, all_indices, idx):

    linewidth_var = 0.3
    fontsize_var = 14

    #fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), dpi=100)
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
    x_labels = joint_axis
    x_pos = np.arange(len(pred_full))

    ax1_max_val = np.max(pred_full) if len(pred_full) > 0 else 0.1
    ax1_min_val = np.min(pred_full)

    # Plot predictions vs ground truth
    ax1.axhline(0, color='black', linewidth=linewidth_var)  # Dunkle Linie bei 0
    ax1.bar(x_pos - 0.2, pred_full, 0.4, label='Predictions', alpha=0.7, color='blue')
    ax1.bar(x_pos + 0.2, label_full, 0.4, label='Ground Truth', alpha=0.7, color='red')
    ax1.set_xlabel('Joint Axes',fontsize = fontsize_var)
    ax1.set_ylabel('Rotation Values in degree', fontsize = fontsize_var)
    #ax1.set_title(f'Predictions vs Ground Truth - Sample {idx}', fontsize = 14)
    ax1.legend()
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    #ax1_y_ticks = np.arange(ax1_min_val - 4, ax1_max_val + 5, step=10)
    ax1_y_ticks = np.arange(-90, 90, step=10)
    ax1.set_yticks(ax1_y_ticks)
    ax1.grid(True, alpha=0.3)

    # Plot absolute differences
    abs_diff = np.abs(pred_full - label_full)

    ax2_max_val = np.max(abs_diff)

    bars = ax2.bar(x_pos, abs_diff, color='orange', alpha=0.7)
    ax2.set_xlabel('Joint Axes', fontsize = fontsize_var)
    ax2.set_ylabel('Absolute Difference in degree', fontsize = fontsize_var)
    #ax2.set_title('Absolute Prediction Errors')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    ax_2_y_ticks = np.arange(0, ax2_max_val + 1.5, step=0.5)
    ax2.set_yticks(ax_2_y_ticks)
    ax2.grid(True, alpha=0.3)

    threshold = 0.01

    for i, (bar, val) in enumerate(zip(bars, abs_diff)):
        if val > threshold:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + ax2_max_val*0.01, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=12, rotation=90)

    # Plot mask (which joints are active)


    mask = all_indices != 0.0
    """ax3.bar(x_pos, mask.astype(int), color='green', alpha=0.7)
    ax3.set_xlabel('Joint Axes')
    ax3.set_ylabel('Active (1) / Inactive (0)')
    ax3.set_title(f'Active Joint Mask (Total: {mask.sum()} active joints)')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    #ax3.set_ylim(0, 1.1)
    ax3.grid(True, alpha=0.3)"""

    plt.tight_layout()
    plt.show()

    # Zusätzliche Statistiken ausgeben
    print(f"\n=== Detailed Analysis for Sample {idx} ===")
    print(f"Total joints: {len(pred_full)}")
    print(f"Active joints (non-zero): {mask.sum()}")
    print(f"Predicted active joints: {np.sum(np.abs(pred_full) > 1e-6)}")
    print(f"Max absolute error: {np.max(abs_diff):.6f}")
    print(f"Mean absolute error (all): {np.mean(abs_diff):.6f}")
    if mask.any():
        print(f"Mean absolute error (active only): {np.mean(abs_diff[mask]):.6f}")
    print("=" * 50)



def visualize_2(joint_axis, average_absolute_difference, std, idx):
    """Verbesserte visualize_2 Funktion mit dynamischer Y-Achse und Debug-Ausgaben"""
    
    fontsize_var = 14
    

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 10))
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
    x_labels = joint_axis
    x_pos = np.arange(len(average_absolute_difference))

    bars = ax1.bar(x_pos, average_absolute_difference, color='orange', alpha=0.7, zorder=2)
    ax1.errorbar(x_pos, average_absolute_difference, yerr=std, fmt='none', color='black', capsize=5, zorder=1)
    ax1.set_xlabel('Joint Axes', fontsize = fontsize_var)
    ax1.set_ylabel('Average Absolute Difference in degree (and std)', fontsize = fontsize_var)
    # ax1.set_ylabel('Standard Deviation in degree', fontsize = fontsize_var)
    #ax1.set_title(f'Average Absolute Prediction Errors over Indices: {idx}')
    ax1.set_xticks(x_pos)

    # Dynamische Y-Achsen-Skalierung
    max_val = np.max(average_absolute_difference) if len(average_absolute_difference) > 0 else 0.1
    min_val = np.min(average_absolute_difference) if len(average_absolute_difference) > 0 else 0
    
    
    y_ticks = np.arange(0, max_val + 3, step=0.2)
    ax1.set_yticks(y_ticks)
    

    ax1.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    ax1.grid(True, alpha=0.3)

    # Zeige Werte für signifikante Balken
    threshold = max_val * 0.05  # Zeige Labels für Balken > 5% vom Maximum
    labels_shown = 0
    for i, (bar, val) in enumerate(zip(bars, average_absolute_difference)):
        if val > threshold and labels_shown < 30:  # Maximal 30 Labels
            ax1.text(bar.get_x() + bar.get_width()/4, bar.get_height() + max_val*0.01,                              #+ bar.get_width()/2
                    f'{val:.3f}', ha='center', va='bottom', fontsize=12, rotation=90)
            labels_shown += 1

    print(f"Labels angezeigt: {labels_shown}")
    plt.tight_layout()
    plt.show()


#Evaluation einzelnes Sample
def evaluate_sample(idx):

    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)

    joint_rotation_axis = list(axis_dict.keys())

    active_joint_axis = [joint_rotation_axis[i] for i in training_active_indices]




    print(f"\n=== Evaluating Sample {idx} ===")
    
    image, label_active = current_dataset[idx]

    print(f"Label active shape: {label_active.shape}")
    print(f"Expected active joints: {len(training_active_indices)}")

    
    image = image.unsqueeze(0).to(device)
    pred_active = predict(model, image).cpu().numpy()
    print(f"Prediction active shape: {pred_active.shape}")

    # Full Ground Truth laden
    label_path = os.path.join(current_label_dir, current_dataset.label_files[idx])
    

    with open(label_path, 'r') as f:
        label_dict = json.load(f)
    label_full = np.array(current_dataset._parse_rotations(label_dict))

    all_indices = get_all_indices(training_active_indices, full_length=len(label_full))

    print(f"Full label length: {len(label_full)}")

    # Full Prediction erstellen
    pred_full = merge_active_and_passive_values(pred_active, training_active_indices, full_length=len(label_full))
    print(f"Full prediction length: {len(pred_full)}")

    # Vergleich: Aktive Werte aus Full Label vs. gefilterte Label
    active_from_full = label_full[training_active_indices]
    print(f"Active values from full label: {active_from_full}")
    print(f"Filtered label from dataset: {label_active.numpy()}")
    print(f"Values match: {np.allclose(active_from_full, label_active.numpy())}")

    # Fehler nur auf aktiven vergleichen
    mask = label_full != 0.0
    if mask.any():
        mse_all = np.mean((pred_full - label_full) ** 2)
        mae_all = np.mean(np.abs(pred_full - label_full))
        mse_active = np.mean((pred_full[mask] - label_full[mask]) ** 2)
        mae_active = np.mean(np.abs(pred_full[mask] - label_full[mask]))
        
        print(f"MSE (all joints): {mse_all:.6f}")
        print(f"MAE (all joints): {mae_all:.6f}")
        print(f"MSE (active only): {mse_active:.6f}")
        print(f"MAE (active only): {mae_active:.6f}")
        print(f"Active joints: {mask.sum()}")
    else:
        print("No active joints found.")

    pred_active_only = pred_active  # Bereits nur aktive Werte
    label_active_only = label_active.numpy()  # Bereits nur aktive Werte
    active_mask_only = np.ones(len(training_active_indices))
    
    #visualize(pred_full, label_full, joint_rotation_axis, all_indices, idx)
    visualize(pred_active_only, label_active_only, active_joint_axis, active_mask_only, idx)



#Evaluation mehrerer Samples
def evaluate_multiple(dataset, n=10):
    print(f"\n=== Evaluating {n} Random Samples ===")
    indices = np.random.choice(len(dataset), n, replace=False)
    mses_all, maes_all = [], []
    mses_active, maes_active = [], []
    
    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
    
    joint_rotation_axis = list(axis_dict.keys())
    average_absolute_difference = []

    for idx in indices:
        image, label_active = dataset[idx]
        image = image.unsqueeze(0).to(device)
        pred_active = predict(model, image).cpu().numpy()

        # Full Label
        label_path = os.path.join(current_label_dir, dataset.label_files[idx])
        with open(label_path, 'r') as f:
            label_dict = json.load(f)
        label_full = np.array(dataset._parse_rotations(label_dict))

        # Full Prediction
        pred_full = merge_active_and_passive_values(pred_active, training_active_indices, full_length=len(label_full))

        # Metriken berechnen
        mse_all = np.mean((pred_full - label_full) ** 2)
        mae_all = np.mean(np.abs(pred_full - label_full))
        mses_all.append(mse_all)
        maes_all.append(mae_all)

        abs_diff = np.abs(pred_full - label_full)
        average_absolute_difference.append(abs_diff)

        mask = label_full != 0.0
        if mask.any():
            mse_active = np.mean((pred_full[mask] - label_full[mask]) ** 2)
            mae_active = np.mean(np.abs(pred_full[mask] - label_full[mask]))
            mses_active.append(mse_active)
            maes_active.append(mae_active)
            print(f"[{idx}] MSE_all: {mse_all:.6f}, MAE_all: {mae_all:.6f}, MSE_active: {mse_active:.6f}, MAE_active: {mae_active:.6f}, Active: {mask.sum()}")
        else:
            print(f"[{idx}] MSE_all: {mse_all:.6f}, MAE_all: {mae_all:.6f}, No active joints")

    average_absolute_difference = np.mean(
        np.vstack(average_absolute_difference),
        axis=0
    )


#Evaluation aller Samples
def evaluate_all(dataset):
    print("Evaluate Average Absolute Difference over all test images")
    indices = range(len(dataset))
    

    all_active_predictions = []
    all_active_labels = []

    prediction_dict = {}

    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
    
    joint_rotation_axis = list(axis_dict.keys())
    active_joint_axis = [joint_rotation_axis[i] for i in training_active_indices]
    average_absolute_difference = []
    active_average_absolute_difference = []

    for idx in indices:
        image, label_active = dataset[idx]
        image = image.unsqueeze(0).to(device)
        pred_active = predict(model, image).cpu().numpy()

        all_active_predictions.append(pred_active)
        all_active_labels.append(label_active.numpy())

        # Full Label
        label_path = os.path.join(current_label_dir, dataset.label_files[idx])
        with open(label_path, 'r') as f:
            label_dict = json.load(f)
        label_full = np.array(dataset._parse_rotations(label_dict))

        # Full Prediction
        pred_full = merge_active_and_passive_values(pred_active, training_active_indices, full_length=len(label_full))

        prediction_dict[idx] = pred_full

        abs_diff = np.abs(pred_full - label_full)

        active_abs_diff = np.abs(pred_active - label_active.numpy())


        average_absolute_difference.append(abs_diff)
        active_average_absolute_difference.append(active_abs_diff)

    all_abs_diff = np.vstack(average_absolute_difference)  # Shape: (n_samples, n_joints)
    std_per_axis = {active_joint_axis[i]: np.std(all_abs_diff[:, training_active_indices[i]]) 
                    for i in range(len(active_joint_axis))}

    active_difference_array = np.array(active_average_absolute_difference)
    active_label_array = np.array(label_active)
    
    """#Collapses all Arrays and takes average result
    average_absolute_difference = np.mean(
        np.vstack(average_absolute_difference),
        axis=0
    )"""

    #print(prediction_dict)
    active_average_difference = np.mean(np.vstack(active_average_absolute_difference), axis=0)

    std_values = [std_per_axis[axis] for axis in active_joint_axis]

    #visualize_2(joint_rotation_axis, average_absolute_difference, "All")
    #visualize_2(active_joint_axis, active_average_difference, "All")
    visualize_2(active_joint_axis, active_average_difference, std_values, "All")


#Evaluation aller Samples
def evaluate_all_adapted(dataset):
    print("Evaluate Average Absolute Difference over all test images")
    indices = range(len(dataset))
    
    # Listen für alle Predictions und Labels (nur aktive)
    all_active_predictions = []
    all_active_labels = []

    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
    
    joint_rotation_axis = list(axis_dict.keys())
    
    # Erstelle Liste der aktiven Achsennamen
    active_axis_names = [joint_rotation_axis[i] for i in training_active_indices]

    for idx in indices:
        image, label_active = dataset[idx]
        image = image.unsqueeze(0).to(device)
        pred_active = predict(model, image).cpu().numpy()

        # label_active ist bereits gefiltert auf aktive Indizes
        # pred_active ist bereits gefiltert auf aktive Indizes
        
        # Füge zu Listen hinzu
        all_active_predictions.append(pred_active)
        all_active_labels.append(label_active.numpy())

    # Konvertiere Listen zu numpy Arrays
    active_pred_array = np.array(all_active_predictions)  # Shape: (n_samples, n_active_joints)
    active_label_array = np.array(all_active_labels)     # Shape: (n_samples, n_active_joints)
    
    print(f"Active Predictions shape: {active_pred_array.shape}")
    print(f"Active Labels shape: {active_label_array.shape}")
    print(f"Number of active joints: {len(training_active_indices)}")
    print(f"Active indices: {training_active_indices}")

    # Plot nur die aktiven Achsen
    plot_scatter(predictions=active_pred_array, truth=active_label_array)
    


def load_axis_influence_as_array(axis_influence_path, joint_axis_order):
    """
    Lädt die Achseneinfluss-Werte und ordnet sie entsprechend der joint_axis Reihenfolge an.
    
    Args:
        axis_influence_path: Pfad zur JSON-Datei mit Achseneinfluss-Werten
        joint_axis_order: Liste mit der Reihenfolge der Gelenk-Achsen
    
    Returns:
        numpy array mit Einfluss-Werten in korrekter Reihenfolge
    """
    with open(axis_influence_path, "r") as f:
        axis_influence_dict = json.load(f)
    
    # Erstelle Array in korrekter Reihenfolge
    axis_influence_array = np.array([
        axis_influence_dict.get(joint_name, 0.0) for joint_name in joint_axis_order
    ])
    
    return axis_influence_array


def evaluate_with_axis_influence_weighting(dataset, model, training_active_indices, 
                                         label_dir, reassign_joint_dir, axis_influence_dir,
                                         device, weighting_method="multiply"):
    """
    Evaluiert das Dataset mit verschiedenen Gewichtungsmethoden basierend auf Achseneinfluss.
    
    Args:
        weighting_method: "multiply", "divide", "relative_error"
    """
    print(f"Evaluating with axis influence weighting method: {weighting_method}")
    
    # Lade Joint-Achsen Reihenfolge
    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
    joint_rotation_axis = list(axis_dict.keys())
    
    # Lade Achseneinfluss-Werte
    axis_influence = load_axis_influence_as_array(axis_influence_dir, joint_rotation_axis)
    
    print(f"Loaded axis influence values:")
    print(f"Min influence: {np.min(axis_influence):.6f}")
    print(f"Max influence: {np.max(axis_influence):.6f}")
    print(f"Zero influence count: {np.sum(axis_influence == 0)}")
    
    indices = range(len(dataset))
    weighted_differences = []
    raw_differences = []
    
    for idx in indices:
        # Vorhersage
        image, label_active = dataset[idx]
        image = image.unsqueeze(0).to(device)
        pred_active = predict(model, image).cpu().numpy()
        
        # Full Label laden
        label_path = os.path.join(label_dir, dataset.label_files[idx])
        with open(label_path, 'r') as f:
            label_dict = json.load(f)
        label_full = np.array(dataset._parse_rotations(label_dict))
        
        # Full Prediction erstellen
        pred_full = merge_active_and_passive_values(pred_active, training_active_indices, 
                                                   full_length=len(label_full))
        
        # Rohe absolute Differenz
        abs_diff = np.abs(pred_full - label_full)
        raw_differences.append(abs_diff)
        
        # Gewichtete Differenz basierend auf Methode
        if weighting_method == "multiply":
            # Fehler mit Einfluss multiplizieren (höhere Gewichtung für einflussreiche Achsen)
            weighted_diff = abs_diff * axis_influence
            
        elif weighting_method == "divide":
            # Fehler durch Einfluss teilen (normalisierte Fehler)
            # Verhindere Division durch 0
            safe_influence = np.where(axis_influence == 0, 1e-8, axis_influence)
            weighted_diff = abs_diff / safe_influence
            
        elif weighting_method == "relative_error":
            # Relativer Fehler: Fehler geteilt durch erwarteten Einfluss
            safe_influence = np.where(axis_influence == 0, 1e-8, axis_influence)
            weighted_diff = abs_diff / safe_influence
            
        else:
            weighted_diff = abs_diff
            
        weighted_differences.append(weighted_diff)
    
    # Durchschnitte berechnen
    avg_raw_diff = np.mean(np.vstack(raw_differences), axis=0)
    avg_weighted_diff = np.mean(np.vstack(weighted_differences), axis=0)
    
    return {
        'joint_axes': joint_rotation_axis,
        'axis_influence': axis_influence,
        'avg_raw_difference': avg_raw_diff,
        'avg_weighted_difference': avg_weighted_diff,
        'weighting_method': weighting_method
    }


def visualize_weighted_analysis(results):
    """
    Visualisiert die gewichtete Analyse mit mehreren Subplots.
    """
    joint_axes = results['joint_axes']
    axis_influence = results['axis_influence']
    avg_raw_diff = results['avg_raw_difference']
    avg_weighted_diff = results['avg_weighted_difference']
    method = results['weighting_method']
    

    active_joint_axes = [joint_axes[i] for i in training_active_indices]
    active_axis_influence = axis_influence[training_active_indices]
    active_avg_raw_diff = avg_raw_diff[training_active_indices]
    active_avg_weighted_diff = avg_weighted_diff[training_active_indices]


    fontsize_var = 14
    #x_pos = np.arange(len(joint_axes))
    x_pos = np.arange(len(active_joint_axes))
    
    #fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
    fig, ax3 = plt.subplots(1, 1, figsize=(16, 10))
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
    
    
    # Plot 3: Gewichtete Fehler
    #bars = ax3.bar(x_pos, avg_weighted_diff, alpha=0.7, color='purple')
    bars = ax3.bar(x_pos, active_avg_weighted_diff, alpha=0.7, color='purple')
    #ax3.set_title(f'Durchschnittliche Fehler gewichtet mit deren Einfluss auf die Silhouette', fontsize = fontsize_var)
    ax3.set_xlabel("Joint Axes", fontsize = fontsize_var)
    ax3.set_ylabel('Weighted Difference', fontsize = fontsize_var)
    ax3.set_xticks(x_pos)
    ax3.grid(True, alpha=0.3)

    max_val = np.max(avg_weighted_diff) if len(avg_weighted_diff) > 0 else 0.01
    min_val = np.min(avg_weighted_diff) if len(avg_weighted_diff) > 0 else 0

    max_val = np.max(active_avg_weighted_diff) if len(active_avg_weighted_diff) > 0 else 0.01
    min_val = np.min(active_avg_weighted_diff) if len(active_avg_weighted_diff) > 0 else 0

    y_ticks = np.arange(0, max_val + 0.007, step=0.002)

    ax3.set_yticks(y_ticks)
    #ax3.set_xticklabels(joint_axes, rotation=90, fontsize=fontsize_var)
    ax3.set_xticklabels(active_joint_axes, rotation=90, fontsize=fontsize_var)

    threshold = max_val * 0.05
    """for i, (bar, val) in enumerate(zip(bars, avg_weighted_diff)):
        if val > threshold:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.01, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=12, rotation=90)"""
    
    for i, (bar, val) in enumerate(zip(bars, active_avg_weighted_diff)):
        if val > threshold:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_val*0.01, 
                    f'{val:.3f}', ha='center', va='bottom', fontsize=12, rotation=90)
    
    plt.tight_layout()
    plt.show()
    

def evaluate_all_in_relation_to_axis_influence(dataset):
    results = evaluate_with_axis_influence_weighting(
        dataset, model, training_active_indices, 
        current_label_dir, reassign_joint_dir, axis_influence_dir, 
        device, weighting_method="multiply"  # oder "divide", "relative_error"
    )
    visualize_weighted_analysis(results)


def plot_scatter(predictions, truth):
 
    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)

    all_axis_names = list(axis_dict.keys())

    active_axis_names = [all_axis_names[i] for i in training_active_indices]

    n_joints = truth.shape[1]
    
    # Berechne Grid-Dimensionen basierend auf Anzahl der Joints
    n_cols = 5
    n_rows = int(np.ceil(n_joints / n_cols))
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 2*n_rows))
    
    # Falls nur eine Reihe, stelle sicher dass axes 2D ist
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    
    #fig.suptitle('Vergleich zwischen geschätzten und Ground-Truth Werten für jede aktive Rotationsachse')
    
    for i in range(n_joints):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]
        
        # Standard scatter plot mit Transparenz für Überlappungen
        ax.scatter(predictions[:, i], truth[:, i], alpha=0.6, s=1, c='blue')
        
        # Diagonale Linie für perfekte Vorhersagen
        min_val = min(predictions[:, i].min(), truth[:, i].min())
        max_val = max(predictions[:, i].max(), truth[:, i].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.75, linewidth=1)
        
        # R² Score berechnen und anzeigen
        from sklearn.metrics import r2_score
        r2 = r2_score(truth[:, i], predictions[:, i])
        
        joint_name = active_axis_names[i]

        ax.set_title(f'{joint_name}\nR² = {r2:.3f}', fontsize=10)
        ax.set_xlabel("Predicted", fontsize=10)
        ax.set_ylabel("Ground Truth", fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Achsen-Ticks kleiner machen
        ax.tick_params(axis='both', which='major', labelsize=6)
    
    # Verstecke unbenutzte Subplots
    for i in range(n_joints, n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        axes[row, col].set_visible(False)
    
    plt.tight_layout()
    plt.show()
    return fig




#==================================




def evaluate_multiple_datasets():
    """
    Evaluiert mehrere Datasets und berechnet durchschnittliche Fehler für jeden
    """
    print("Evaluating multiple datasets: color, white, black_and_white")
    
    # Dictionary für die Ergebnisse
    results = {}
    
    # Datasets und ihre Namen
    datasets_info = {
        'Color': (color_dataset, color_label_dir),
        'White': (white_dataset, white_label_dir), 
        'Black & White': (black_and_white_dataset, black_and_white_label_dir)
    }
    
    with open(reassign_joint_dir, 'r') as f:
        axis_dict = json.load(f)
    
    joint_rotation_axis = list(axis_dict.keys())
    active_joint_axis = [joint_rotation_axis[i] for i in training_active_indices]
    
    for dataset_name, (dataset, label_dir) in datasets_info.items():
        print(f"\nEvaluating {dataset_name} dataset...")
        
        indices = range(len(dataset))
        active_average_absolute_difference = []
        
        for idx in indices:
            image, label_active = dataset[idx]
            image = image.unsqueeze(0).to(device)
            pred_active = predict(model, image).cpu().numpy()
            
            # Nur aktive Werte vergleichen (effizienter)
            active_abs_diff = np.abs(pred_active - label_active.numpy())
            active_average_absolute_difference.append(active_abs_diff)
        
        # Durchschnitt über alle Samples für dieses Dataset
        active_average_difference = np.mean(np.vstack(active_average_absolute_difference), axis=0)
        results[dataset_name] = active_average_difference
        
        print(f"{dataset_name}: Mean error = {np.mean(active_average_difference):.3f}°")
    
    return results, active_joint_axis


def visualize_multi_dataset_comparison(results_dict, joint_axis):
    """
    Visualisiert Vergleich zwischen mehreren Datasets mit drei Balken pro Achse
    """
    fontsize_var = 14
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.15)
    
    # Farben für die verschiedenen Datasets
    colors = {
        'Color': 'blue',
        'White': 'gray', 
        'Black & White': 'black'
    }
    
    x_labels = joint_axis
    x_pos = np.arange(len(joint_axis))
    
    # Balkenbreite und Positionen
    bar_width = 0.25
    dataset_names = list(results_dict.keys())
    
    # Balken für jedes Dataset
    for i, (dataset_name, values) in enumerate(results_dict.items()):
        offset = (i - 1) * bar_width  # Zentriert um 0
        bars = ax.bar(x_pos + offset, values, bar_width, 
                     label=dataset_name, alpha=0.8, 
                     color=colors.get(dataset_name, f'C{i}'))
    
    # Achsenbeschriftungen und Titel
    ax.set_xlabel('Joint Axes', fontsize=fontsize_var)
    ax.set_ylabel('Average Absolute Difference in degrees', fontsize=fontsize_var)
    #ax.set_title('Comparison of Average Prediction Errors Across Different Datasets', fontsize=fontsize_var)
    
    # X-Achse
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=90, fontsize=fontsize_var)
    
    # Y-Achse (dynamisch)
    all_values = np.concatenate(list(results_dict.values()))
    max_val = np.max(all_values) if len(all_values) > 0 else 0.1
    y_ticks = np.arange(0, max_val + 10, step=5)
    ax.set_yticks(y_ticks)
    
    # Legende und Grid
    ax.legend(fontsize=fontsize_var)
    ax.grid(True, alpha=0.3)
    
    # Zeige Werte für signifikante Balken (nur für die höchsten Werte)
    threshold = max_val * 0.1  # Zeige Labels für Balken > 10% vom Maximum
    
    for i, (dataset_name, values) in enumerate(results_dict.items()):
        offset = (i - 1) * bar_width
        for j, val in enumerate(values):
            if val > threshold:
                ax.text(j + offset, val + max_val*0.01, 
                       f'{val:.2f}', ha='center', va='bottom', 
                       fontsize=11, rotation=90)
    
    plt.tight_layout()
    plt.show()
    
    # Zusätzliche Statistiken ausgeben
    print(f"\n=== Dataset Comparison Statistics ===")
    for dataset_name, values in results_dict.items():
        print(f"{dataset_name}:")
        print(f"  Mean error: {np.mean(values):.3f}°")
        print(f"  Max error: {np.max(values):.3f}°")
        print(f"  Min error: {np.min(values):.3f}°")
        print(f"  Std error: {np.std(values):.3f}°")
    print("=" * 50)


def run_multi_dataset_evaluation():
    """
    Führt die komplette Multi-Dataset Evaluation aus
    """
    results, active_joint_axis = evaluate_multiple_datasets()
    visualize_multi_dataset_comparison(results, active_joint_axis)




#=================================================================




# === Startpunkt ===
if __name__ == "__main__":
    print("==================================================================")
    print("Evaluation")
    #evaluate_sample(test_index)
    #evaluate_multiple(current_dataset, n=10)
    evaluate_all(current_dataset)
    #evaluate_all_adapted(current_dataset)
    #evaluate_all_in_relation_to_axis_influence(current_dataset)
    #run_multi_dataset_evaluation()
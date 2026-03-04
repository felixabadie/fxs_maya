import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from data_prep import OUTPUT_DIR
from const import project_base_dir, ml_model_save_dir, active_mask_path
from out_source_stuff import (
    train_transform_method,
    val_transform_method,
    FilteredJointPoseDataSet,
    AdaptiveShortNetwork5,
    train_corrected,
    comprehensive_evaluation,
)


#device is in this case the gpu -> used to move data and the model to the gpu for parallelisation
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


#All necessary paths
image_train_dir = OUTPUT_DIR + r"\images\train"
image_validation_dir = OUTPUT_DIR + r"\images\val"
image_test_dir =  OUTPUT_DIR + r"\images\test"

label_train_dir = OUTPUT_DIR + r"\labels\train"
label_validation_dir = OUTPUT_DIR + r"\labels\val"
label_test_dir = OUTPUT_DIR +r"\labels\test"

                
if __name__ == "__main__":
    batch_size = 32
    learning_rate = 0.0001
    num_epochs = 100
    
    # Create datasets for Training, Validation and Testing
    train_dataset = FilteredJointPoseDataSet(
        image_train_dir, 
        label_train_dir, 
        transform=train_transform_method,
        active_mask_path=active_mask_path  
    )
    val_dataset = FilteredJointPoseDataSet(
        image_validation_dir, 
        label_validation_dir, 
        active_indices=train_dataset.active_indices,
        transform=val_transform_method,
        active_mask_path=active_mask_path
    )  
    test_dataset = FilteredJointPoseDataSet(
        image_test_dir, 
        label_test_dir, 
        active_indices=train_dataset.active_indices,
        transform=val_transform_method,
        active_mask_path=active_mask_path
    )

    # Get dynamic output size
    output_size = train_dataset.get_output_size()
    print(f"Training with {output_size} active outputs instead of 51")
    
    #Create dataloaders
    train_dataloader = DataLoader(train_dataset, batch_size, shuffle=True)
    val_dataloader = DataLoader(val_dataset, batch_size, shuffle=False)
    test_dataloader = DataLoader(test_dataset, batch_size, shuffle=False)
    
    #Create model with correct output size
    model = AdaptiveShortNetwork5(output_size)
    
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.00089)
    steps_per_epoch = len(train_dataloader)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, 
        max_lr=0.002,
        steps_per_epoch=steps_per_epoch,
        epochs=num_epochs, 
        final_div_factor=50,
        pct_start=0.3 
    )
    
    
    active_indices_path = os.path.join(ml_model_save_dir, "active_indices.json")
    with open(active_indices_path, 'w') as f:
        json.dump({"active_indices": train_dataset.active_indices}, f)
    
    print("Starting training")

    print(f"Train dataset active indices: {len(train_dataset.active_indices)}")
    print(f"Val dataset active indices: {len(val_dataset.active_indices)}")
    print(f"Test dataset active indices: {len(test_dataset.active_indices)}")
    
    # Get dynamic output size
    output_size = train_dataset.get_output_size()
    print(f"Training with {output_size} active outputs")

    print("Starting corrected training")

    training_history = train_corrected(
        model, train_dataloader, val_dataloader, 
        optimizer, scheduler, ml_model_save_dir, num_epochs
        )

    lrs = training_history['learning_rates']
    total_train_loss = training_history['train_losses']
    total_val_loss = training_history['val_losses']
    total_r2_score = training_history['r2_scores']
    total_train_r2 = training_history['train_r2_scores']
    total_val_r2 = training_history['val_r2_scores']

    print('Training complete. Model parameters saved.')
    
    best_model_path = os.path.join(ml_model_save_dir, "best_model.pth")
    model.load_state_dict(torch.load(best_model_path, map_location=device))
    
    # training evaluation
    evaluation_results = comprehensive_evaluation(
        model, test_dataloader, train_dataloader, val_dataloader
    )


    # Save training results as JSON
    results_path = os.path.join(ml_model_save_dir, "evaluation_results.json")
    with open(results_path, 'w') as f:
        json_results = {}
        for split, metrics in evaluation_results.items():
            json_results[split] = {k: float(v) if isinstance(v, (np.float32, np.float64)) else v 
                                 for k, v in metrics.items()}
        json.dump(json_results, f, indent=2)
    
    print(f"Evaluation results saved to: {results_path}")

        # Plot training results
    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle('Training Results - Optuna Optimized Model', fontsize=16, fontweight='bold')
    
    # Learning rate schedule
    axes[0, 0].plot(lrs, color='blue', alpha=0.7)
    axes[0, 0].set_title("Learning Rate Schedule")
    axes[0, 0].set_xlabel("Steps")
    axes[0, 0].set_ylabel("Learning Rate")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_yscale('log')

    # Training vs Validation Loss
    axes[0, 1].plot(total_train_loss, label='Training Loss', color='blue', alpha=0.8)
    axes[0, 1].plot(total_val_loss, label='Validation Loss', color='red', alpha=0.8)
    axes[0, 1].set_title("Loss over Epochs")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Loss")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_yscale('log')

    # R2 Score
    axes[1, 0].plot(total_r2_score, color='green', alpha=0.8)
    axes[1, 0].set_title("R2 Score over Epochs")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("R2 Score")
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_ylim(0, 1)

    # Overfitting indicator
    if len(total_train_loss) == len(total_val_loss):
        loss_diff = np.array(total_val_loss) - np.array(total_train_loss)
        axes[1, 1].plot(loss_diff, color='purple', alpha=0.8)
        axes[1, 1].set_title("Overfitting Indicator\n(Val Loss - Train Loss)")
        axes[1, 1].set_xlabel("Epoch")
        axes[1, 1].set_ylabel("Loss Difference")
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(ml_model_save_dir, "training_plots_optuna.png"), dpi=300, bbox_inches='tight')
    plt.show()
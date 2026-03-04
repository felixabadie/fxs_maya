import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import json
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Transform for training with stretching and slight blurring of image for data augmentation
train_transform_method = transforms.Compose([
    transforms.Resize((256, 256)),

    # imgage stretching
    transforms.RandomAffine(
        degrees=0,
        scale=(0.9, 1.1), 
        translate=(0.05, 0.05), 
    ),
    
    transforms.GaussianBlur(kernel_size=3, sigma=(0.01, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])

# validation transform without data augmentation
val_transform_method = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])


class FilteredJointPoseDataSet(Dataset):

    """Creation of Dataset for machine learning and contains functions to determin active axis"""

    def __init__(self, image_dir, label_dir, active_indices=None, all_indices=None,  transform=None, active_mask_path=None):
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.active_indices = active_indices

        self.active_mask_path = active_mask_path
        
        self.image_files = sorted([f for f in os.listdir(image_dir) if f.endswith(".jpg")])
        self.label_files = sorted([f for f in os.listdir(label_dir) if f.endswith(".json")])
        
        image_stems = {os.path.splitext(f)[0] for f in self.image_files}
        label_stems = {os.path.splitext(f)[0] for f in self.label_files}
        common_stems = sorted(image_stems & label_stems)
        
        self.image_files = [f"{stem}.jpg" for stem in common_stems]
        self.label_files = [f"{stem}.json" for stem in common_stems]
        
        if len(self.image_files) != len(self.label_files):
            raise ValueError(f"Mismatch: {len(self.image_files)} images vs {len(self.label_files)} labels")
        
        self.transform = transform
        
        if self.active_indices is None:
            self.active_indices = self._detect_active_indices()
    
    def _parse_rotations(self, joint_data):

        """extracts array of all axis-states (1=active, 0=passive)"""

        if "rotations" in joint_data and isinstance(joint_data["rotations"], list):
            return joint_data["rotations"]
        else:
            flat = []
            for joint_id in sorted(joint_data.keys(), key=int):
                if joint_id.isdigit():
                    values = joint_data[joint_id]
                    if isinstance(values, list):
                        flat.extend(values)
            return flat

    def _detect_active_indices(self):
        
        """determines all active indices"""

        if self.active_mask_path and os.path.exists(self.active_mask_path):
            print(f"Loading active indices from: {self.active_mask_path}")
            try:
                with open(self.active_mask_path, 'r') as f:
                    mask_data = json.load(f)
              
                rotations = self._parse_rotations(mask_data)
                active_indices = []
                for idx, value in enumerate(rotations):
                    if abs(value) > 1e-6:
                        active_indices.append(idx)
                
                print(f"Detected {len(active_indices)} active indices from reference file: {active_indices}")
                return active_indices
                
            except Exception as e:
                print(f"Error loading active_mask_path: {e}")


    def __getitem__(self, index):
        image_name = self.image_files[index]
        image_path = os.path.join(self.image_dir, image_name)
        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)
        
        label_path = os.path.join(self.label_dir, self.label_files[index])
        
        with open(label_path, 'r') as f:
            joint_data = json.load(f)
        
        all_rotations = self._parse_rotations(joint_data)
        
        if len(self.active_indices) == 0:
            
            filtered_rotations = all_rotations
        else:
            
            filtered_rotations = []
            for i in self.active_indices:
                if i < len(all_rotations):
                    filtered_rotations.append(all_rotations[i])
                else:
                    print(f"Error: Index {i} out of bounds for sample {index} (length: {len(all_rotations)})")
                    raise IndexError(f"Invalid active index {i} for rotation array of length {len(all_rotations)}")
        
        label_tensor = torch.tensor(filtered_rotations, dtype=torch.float32)
        return image, label_tensor

    def __len__(self):
        return len(self.image_files)

    def get_output_size(self):
        return len(self.active_indices)


class AdaptiveShortNetwork5(nn.Module):

    """Defines final Model and its architecture"""

    def __init__(self, output_size):
        super(AdaptiveShortNetwork5, self).__init__()
        
        # Convolutional + Pooling layers
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)   # keeps size 256x256
        self.pool1 = nn.MaxPool2d(2, 2)                           # half -> 128x128
        
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)  # keeps -> 128x128
        self.pool2 = nn.MaxPool2d(2, 2)                           # halfs -> 64x64
        
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)  # keeps -> 64x64
        self.pool3 = nn.MaxPool2d(2, 2)                           # halfs -> 32x32
        
        self.conv4 = nn.Conv2d(64, 128, kernel_size=3, padding=1) # keeps -> 32x32
        self.pool4 = nn.MaxPool2d(2, 2)                           # halfs -> 16x16

        self.conv5 = nn.Conv2d(128, 256, kernel_size=3, padding=1)# keeps -> 16x16
        self.pool5 = nn.MaxPool2d(2, 2)                           # halfs -> 8x8

        #Feature Map size: (256, 8, 8)
        flattened_size = 256 * 8 * 8 
        
        # Fully connected layers
        self.fc1 = nn.Linear(flattened_size, 256)
        self.fc2 = nn.Linear(256, output_size)
    
    def _forward_conv_layers(self, x):
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = F.relu(self.conv3(x))
        x = self.pool3(x)
        x = F.relu(self.conv4(x))
        x = self.pool4(x)
        x = F.relu(self.conv5(x))
        x = self.pool5(x)
        return x
    
    def forward(self, x):
        x = self._forward_conv_layers(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


def to_numpy(tensor):
    return tensor.cpu().detach().numpy()
    
 
def simple_mse_loss(predictions, labels):
    return F.mse_loss(predictions, labels)


def save_model_params(model, save_dir, model_filename="latst_model.pth"):
    model_path = os.path.join(save_dir, model_filename)
    torch.save(model.state_dict(), model_path)


def load_model(model, model_path):

    """loads model as state_dict"""

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Model loaded from {model_path}")
    if 'optuna_config' in checkpoint:
        print("Optuna config:", checkpoint['optuna_config'])
    return model


#Evaluation auf Test-Daten
def evaluate_model(model, test_dataloader, evaluation_type, loss_function=None):
    model.to(device)
    model.eval()
    
    if loss_function is None:
        loss_function = simple_mse_loss
    
    test_running_loss = 0.0
    all_test_preds = []
    all_test_labels = []
    num_samples = 0
    
    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(test_dataloader):
            images = images.to(device)
            labels = labels.to(device)
            
            predictions = model(images)
            
            # consistant loss calculation
            batch_loss = loss_function(predictions, labels)
            test_running_loss += batch_loss.item()
            num_samples += labels.size(0)
            
            # Sammle Predictions for metrics
            all_test_preds.append(predictions.cpu().numpy())
            all_test_labels.append(labels.cpu().numpy())
    
    # loss as batchaverage (konsistent mit Training)
    test_loss = test_running_loss / len(test_dataloader)
    
    test_preds = np.concatenate(all_test_preds, axis=0)
    test_labels = np.concatenate(all_test_labels, axis=0)
    
    # flat array for sklearn metrics
    test_preds_flat = test_preds.flatten()
    test_labels_flat = test_labels.flatten()
    
    test_mse = mean_squared_error(test_labels_flat, test_preds_flat)
    test_mae = mean_absolute_error(test_labels_flat, test_preds_flat)
    test_r2 = r2_score(test_labels_flat, test_preds_flat)
    
    print(f"\n{'='*60}")
    print(f"FINAL {evaluation_type} RESULTS:")
    print(f"{'='*60}")
    print(f"{evaluation_type} Loss (Average):     {test_loss:.6f}")
    print(f"{evaluation_type} MSE:               {test_mse:.6f}")
    print(f"{evaluation_type} MAE:               {test_mae:.6f}")
    print(f"{evaluation_type} R2 Score:          {test_r2:.6f}")
    print(f"Total {evaluation_type} Samples:     {num_samples}")
    print(f"Active Parameters:      {test_preds.shape[1]}")
    print(f"{'='*60}\n")
    
    return {
        'test_loss': test_loss,
        'test_mse': test_mse,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'num_samples': num_samples
    }


def comprehensive_evaluation(model, test_dataloader, train_dataloader=None, val_dataloader=None):
    
    print("Starting comprehensive model evaluation...")
    
    results = {}
    
    # Test-Evaluation
    test_results = evaluate_model(model, test_dataloader, evaluation_type="Test")
    results['test'] = test_results
    
    # Optional: Auch Train und Val evaluieren für Vergleich
    if train_dataloader:
        print("Evaluating on training set...")
        model.eval()  # Wichtig: auch Training-Set im eval-Modus bewerten
        train_results = evaluate_model(model, train_dataloader, evaluation_type="Train")
        results['train'] = train_results
    
    if val_dataloader:
        print("Evaluating on validation set...")
        evaluation_type = "Train"
        val_results = evaluate_model(model, val_dataloader, evaluation_type="Val")
        results['val'] = val_results
    
    # comparative analysis
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("COMPARATIVE ANALYSIS:")
        print(f"{'='*60}")
        
        for split_name, split_results in results.items():
            print(f"{split_name.upper():>12} - Loss: {split_results['test_loss']:.6f}, "
                  f"R²: {split_results['test_r2']:.6f}")
        
        # Overfitting-Check
        if 'train' in results and 'val' in results:
            overfitting_indicator = results['val']['test_loss'] - results['train']['test_loss']
            print(f"\nOverfitting Indicator (Val-Train Loss): {overfitting_indicator:.6f}")
            if overfitting_indicator > 0.1:
                print("WARNING: Possible overfitting detected!")
            else:
                print("Model appears well-generalized")
    
    return results


def train_corrected(model, train_dataloader, val_dataloader, optimizer, scheduler, save_dir, num_epochs):

    """Train function including validation and early stopping"""

    model.to(device)
    
    train_losses = []
    val_losses = []
    learning_rates = []
    r2_scores = []
    
    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0
    
    loss_function = simple_mse_loss
    

    for epoch in range(num_epochs):
        # =============== TRAINING PHASE ===============
        model.train()
        train_running_loss = 0.0
        all_train_preds = []
        all_train_labels = []
        
        for batch_idx, (images, labels) in enumerate(train_dataloader):
            images = images.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            predictions = model(images)
            
            # consistant loss calculation
            loss = loss_function(predictions, labels)
            loss.backward()
            
            # Gradient clipping to avoid loss explosion
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            if isinstance(scheduler, torch.optim.lr_scheduler.OneCycleLR):
                scheduler.step()
                learning_rates.append(optimizer.param_groups[0]["lr"])
            
            train_running_loss += loss.item()
            
            all_train_preds.append(predictions.detach().cpu().numpy())
            all_train_labels.append(labels.cpu().numpy())
        
        # loss average batch
        train_loss = train_running_loss / len(train_dataloader)
        train_losses.append(train_loss)
        
        # calculate metrics
        train_preds = np.concatenate(all_train_preds, axis=0)
        train_labels = np.concatenate(all_train_labels, axis=0)
        
        train_preds_flat = train_preds.flatten()
        train_labels_flat = train_labels.flatten()
        
        train_mse = mean_squared_error(train_labels_flat, train_preds_flat)
        train_mae = mean_absolute_error(train_labels_flat, train_preds_flat)
        train_r2 = r2_score(train_labels_flat, train_preds_flat)
        r2_scores.append(train_r2)
        
        # =============== VALIDATION PHASE ===============
        model.eval()
        val_running_loss = 0.0
        all_val_preds = []
        all_val_labels = []
        
        with torch.no_grad():
            for images, labels in val_dataloader:
                images = images.to(device)
                labels = labels.to(device)
                
                predictions = model(images)
                
                loss = loss_function(predictions, labels)
                val_running_loss += loss.item()
                
                all_val_preds.append(predictions.cpu().numpy())
                all_val_labels.append(labels.cpu().numpy())
        
        val_loss = val_running_loss / len(val_dataloader)
        val_losses.append(val_loss)
        
        # calculate validation metrics
        val_preds = np.concatenate(all_val_preds, axis=0)
        val_labels = np.concatenate(all_val_labels, axis=0)
        
        val_preds_flat = val_preds.flatten()
        val_labels_flat = val_labels.flatten()
        
        val_mse = mean_squared_error(val_labels_flat, val_preds_flat)
        val_mae = mean_absolute_error(val_labels_flat, val_preds_flat)
        val_r2 = r2_score(val_labels_flat, val_preds_flat)
        
        if not isinstance(scheduler, torch.optim.lr_scheduler.OneCycleLR):
            scheduler.step()
            learning_rates.append(optimizer.param_groups[0]["lr"])
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            save_model_params(model, save_dir, "best_model.pth")
            print(f"New best model saved! Val Loss: {val_loss:.6f}")
        else:
            patience_counter += 1
        
        # Periodic saving
        if (epoch + 1) % 10 == 0:
            save_model_params(model, save_dir, f"model_epoch{epoch+1}.pth")
        
        #Early stopping
        if patience_counter >= patience:
            print(f"Early stopping triggered after {epoch + 1} epochs")
            break
        
        #Logging
        print(f'Epoch [{epoch + 1:3d}/{num_epochs}]')
        print(f'  Train - Loss: {train_loss:.6f}, MSE: {train_mse:.6f}, MAE: {train_mae:.6f}, R²: {train_r2:.6f}')
        print(f'  Valid - Loss: {val_loss:.6f}, MSE: {val_mse:.6f}, MAE: {val_mae:.6f}, R²: {val_r2:.6f}')
        print(f'  LR: {optimizer.param_groups[0]["lr"]:.2e}, Patience: {patience_counter}/{patience}')
        print('-' * 80)
    
    return {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'learning_rates': learning_rates,
        'r2_scores': r2_scores
    }

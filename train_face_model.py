# train_face_model.py
# Custom Face Recognition Model Training Script
# Uses Transfer Learning with ResNet-18 (lighter than ResNet-50 for CPU training)

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import time

print("=" * 50)
print("  CUSTOM FACE RECOGNITION MODEL TRAINER")
print("=" * 50)
print()

# =============================================
# STEP A: Prepare the data
# =============================================
transform = transforms.Compose([
    transforms.Resize((224, 224)),           # ResNet needs 224x224
    transforms.RandomHorizontalFlip(),       # Data augmentation: flip left-right
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),  # Simulate lighting
    transforms.RandomRotation(15),           # Slight rotation for robustness
    transforms.ToTensor(),                   # Convert image to numbers
    transforms.Normalize([0.485, 0.456, 0.406],   # Standard normalization
                         [0.229, 0.224, 0.225])
])

# Check if dataset folder exists
if not os.path.exists("my_face_dataset"):
    print("ERROR: 'my_face_dataset/' folder not found!")
    print("Run capture_dataset.py first to collect photos.")
    exit(1)

dataset = datasets.ImageFolder("my_face_dataset", transform=transform)
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

num_voters = len(dataset.classes)
total_images = len(dataset)

print(f"📁 Found {num_voters} voters: {dataset.classes}")
print(f"📸 Total images: {total_images}")
print()

if num_voters < 2:
    print("ERROR: You need at least 2 voters to train!")
    exit(1)

# Save the class names for later use
class_names = dataset.classes
with open("face_model_classes.txt", "w") as f:
    for name in class_names:
        f.write(name + "\n")
print(f"💾 Saved class names to face_model_classes.txt")

# =============================================
# STEP B: Build the Model (ResNet-18 + Custom Head)
# =============================================
print("🧠 Loading ResNet-18 base model (pre-trained on ImageNet)...")

# Using ResNet-18 (lighter, faster for CPU training)
model = models.resnet18(pretrained=True)

# Freeze early layers (they already know edges, shapes, textures)
for param in model.parameters():
    param.requires_grad = False

# Replace the final classification layer with our custom layers
# Original ResNet-18 outputs 512 features → we map to 128 face embedding → then to num_voters
model.fc = nn.Sequential(
    nn.Linear(512, 256),
    nn.ReLU(),
    nn.Dropout(0.3),       # Prevent overfitting
    nn.Linear(256, 128),   # 128-dimensional face encoding (same as face_recognition library!)
    nn.ReLU(),
    nn.Linear(128, num_voters)  # Final classification layer
)

# Unfreeze the last few layers for fine-tuning
for param in model.layer4.parameters():
    param.requires_grad = True
for param in model.fc.parameters():
    param.requires_grad = True

device = torch.device("cpu")
model = model.to(device)

print("✅ Model ready!")
print()

# =============================================
# STEP C: Training Setup
# =============================================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.0005)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)  # Reduce LR every 5 epochs

num_epochs = 30

# =============================================
# STEP D: Training Loop
# =============================================
print("🚀 Starting training...")
print(f"   Epochs: {num_epochs}")
print(f"   Batch size: 8")
print(f"   Device: CPU")
print()

start_time = time.time()

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        
        # Track accuracy
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    scheduler.step()
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100.0 * correct / total
    elapsed = time.time() - start_time
    
    print(f"  Epoch [{epoch+1}/{num_epochs}] | Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.1f}% | Time: {elapsed:.0f}s")

print()
total_time = time.time() - start_time
print(f"⏱️  Total training time: {total_time:.0f} seconds")

# =============================================
# STEP E: Save the trained model
# =============================================

# Save the FULL model (for easy loading later)
torch.save({
    'model_state_dict': model.state_dict(),
    'class_names': class_names,
    'num_classes': num_voters,
}, "my_face_model.pth")

print()
print("=" * 50)
print(f"  ✅ MODEL SAVED: my_face_model.pth")
print(f"  ✅ CLASSES: {class_names}")
print(f"  ✅ Total images trained on: {total_images}")
print("=" * 50)
print()
print("Next step: Run your E-Vote system and it will use this model!")

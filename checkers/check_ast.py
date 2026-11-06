import torch
from transformers import AutoModelForAudioClassification
import torch.nn as nn

checkpoint = torch.load(
    "models/ast.pt",
    map_location="cpu",
    weights_only=False
)

model = AutoModelForAudioClassification.from_pretrained(
    "MIT/ast-finetuned-audioset-10-10-0.4593",
    num_labels=4096,
    ignore_mismatched_sizes=True
)

head = model.classifier
model.classifier = nn.Sequential(head, nn.ReLU())

checkpoint_keys = set(checkpoint["model_state_dict"].keys())
model_keys = set(model.state_dict().keys())

print("\nCheckpoint keys:", len(checkpoint_keys))
print("Model keys:", len(model_keys))
print("\nCheckpoint sample:", list(checkpoint_keys)[:5])
print("Model sample:", list(model_keys)[:5])

print("\nMissing keys:", len(model_keys - checkpoint_keys))
print("Unexpected keys:", len(checkpoint_keys - model_keys))
checkpoint_state = checkpoint["model_state_dict"]
model_state = model.state_dict()

shape_mismatches = []

for key in checkpoint_state:
    if checkpoint_state[key].shape != model_state[key].shape:
        shape_mismatches.append(
            (key, checkpoint_state[key].shape, model_state[key].shape)
        )

print("\nShape mismatches:", len(shape_mismatches))

for item in shape_mismatches:
    print(item)

if len(shape_mismatches) == 0:
    model.load_state_dict(checkpoint_state)
    print("\nSUCCESS: AST checkpoint loaded successfully!")
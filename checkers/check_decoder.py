import torch
import sys

sys.path.insert(
    0,
    "model_source/Speech-to-face/src"
)

from models.face_decoder import FaceDecoder

checkpoint = torch.load(
    "models/face_decoder.pt",
    map_location="cpu",
    weights_only=False
)

model = FaceDecoder()

checkpoint_state = checkpoint["model_state_dict"]
model_state = model.state_dict()

print("Checkpoint keys:", len(checkpoint_state))
print("Model keys:", len(model_state))

missing = set(model_state) - set(checkpoint_state)
unexpected = set(checkpoint_state) - set(model_state)

print("Missing keys:", len(missing))
print("Unexpected keys:", len(unexpected))

mismatches = []

for key in checkpoint_state:
    if key in model_state:
        if checkpoint_state[key].shape != model_state[key].shape:
            mismatches.append(key)

print("Shape mismatches:", len(mismatches))

if not missing and not unexpected and not mismatches:
    model.load_state_dict(checkpoint_state)
    print("SUCCESS: FaceDecoder checkpoint loaded!")
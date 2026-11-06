
import os
import sys
from types import SimpleNamespace

import torch
import torch.nn as nn
import librosa
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from transformers import AutoModelForAudioClassification, ASTFeatureExtractor


# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(
    BASE_DIR, "model_source", "Speech-to-face", "src"
)

sys.path.insert(0, SRC_DIR)

from models.face_decoder import FaceDecoder
import data_preprocessing.ast_audio_preprocess as audio_processing


# Model configuration
AST_MODEL_NAME = "MIT/ast-finetuned-audioset-10-10-0.4593"

AUDIO_LENGTH = 10.26
SAMPLING_RATE = 16000
MEAN = -5.460994
STD = 3.1129124

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Load models once when the application starts
def load_models():

    print("Loading FaceDecoder...")

    face_decoder = FaceDecoder().to(DEVICE)

    decoder_checkpoint = torch.load(
        os.path.join(BASE_DIR, "models", "face_decoder.pt"),
        map_location=DEVICE,
        weights_only=False
    )

    face_decoder.load_state_dict(
        decoder_checkpoint["model_state_dict"]
    )
    face_decoder.eval()

    print("Loading AST...")

    ast = AutoModelForAudioClassification.from_pretrained(
        AST_MODEL_NAME,
        num_labels=4096,
        ignore_mismatched_sizes=True
    ).to(DEVICE)

    head = ast.classifier
    ast.classifier = nn.Sequential(head, nn.ReLU())

    ast_checkpoint = torch.load(
        os.path.join(BASE_DIR, "models", "ast.pt"),
        map_location=DEVICE,
        weights_only=False
    )

    ast.load_state_dict(ast_checkpoint["model_state_dict"])
    ast.eval()

    feature_extractor = ASTFeatureExtractor(
        sampling_rate=SAMPLING_RATE,
        mean=MEAN,
        std=STD
    )

    print("Both models loaded successfully!")

    return ast, face_decoder, feature_extractor


# Load models once
ast, face_decoder, feature_extractor = load_models()


def generate_face(audio_path, output_path):

    print("Processing audio:", audio_path)

    args = SimpleNamespace(
        audio_length=AUDIO_LENGTH,
        sampling_rate=SAMPLING_RATE
    )

    root = os.path.dirname(audio_path)
    file_base = os.path.splitext(os.path.basename(audio_path))[0]

    normalized_file_path = audio_processing.normalize_audio(
        audio_path, root, file_base
    )

    try:
        waveform, _ = librosa.load(
            normalized_file_path,
            duration=AUDIO_LENGTH,
            sr=SAMPLING_RATE,
            mono=True
        )

        waveform = audio_processing.stretch_audio(args, waveform)

        inputs = feature_extractor(
            waveform,
            sampling_rate=SAMPLING_RATE,
            padding="max_length",
            return_tensors="np"
        )

        input_values = torch.tensor(
            inputs.input_values,
            dtype=torch.float32
        ).to(DEVICE)

        with torch.no_grad():
            embeddings = ast(input_values).logits

            landmarks, images = face_decoder(embeddings)

        temp_image = (
            images[0].detach().cpu().clamp(0, 1) * 255
        ).to(torch.uint8)

        temp_image = temp_image.permute(1, 2, 0).numpy()

        temp_landmarks = landmarks[0].detach().cpu().view(72, 2)
        x, y = zip(*temp_landmarks.numpy())

        fig, axes = plt.subplots(1, 1, figsize=(12, 8))

        axes.imshow(temp_image)
        axes.set_title("Reconstructed image")
        axes.axis("off")
        axes.scatter(x, y, c="red", marker="o", s=2)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        print("Generated face saved:", output_path)

        return output_path

    finally:
        if os.path.exists(normalized_file_path):
            os.remove(normalized_file_path)

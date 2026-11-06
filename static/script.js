const loadingScreen = document.getElementById("loadingScreen");
const loadingMessage = document.getElementById("loadingMessage");
const audioInput = document.getElementById("audioFile");
const audioPreview = document.getElementById("audioPreview");
const generateButton = document.getElementById("generateBtn");
const result = document.getElementById("result");
const recordPlaceholder = document.getElementById("recordPlaceholder");

let selectedAudio = null;
let audioURL = null;
let mediaRecorder = null;
let recordedChunks = [];
let microphoneStream = null;


// ===== RECORDING CONTROLS =====

const recordingControls = document.createElement("div");
recordingControls.style.display = "flex";
recordingControls.style.justifyContent = "center";
recordingControls.style.gap = "10px";
recordingControls.style.flexWrap = "wrap";

const recordButton = document.createElement("button");
recordButton.textContent = "🎙️ START RECORDING";
recordButton.type = "button";

const stopButton = document.createElement("button");
stopButton.textContent = "⏹ STOP";
stopButton.type = "button";
stopButton.disabled = true;

stopButton.style.opacity = "0.5";

recordingControls.append(recordButton, stopButton);

// Put recording buttons inside the recording card
recordPlaceholder.innerHTML = "";
recordPlaceholder.appendChild(recordingControls);


// ===== SELECTED AUDIO HANDLER =====

function setSelectedAudio(file) {

    selectedAudio = file;

    if (audioURL) {
        URL.revokeObjectURL(audioURL);
    }

    audioURL = URL.createObjectURL(file);

    audioPreview.innerHTML = "";

    const fileName = document.createElement("p");
    fileName.textContent = "Selected Audio: " + file.name;

    const player = document.createElement("audio");
    player.controls = true;
    player.src = audioURL;

    audioPreview.append(fileName, player);

    generateButton.disabled = false;
    generateButton.innerHTML = 'GENERATE FACE <span>→</span>';

    result.innerHTML = `
        <div class="result-placeholder">
            <div class="result-placeholder-icon">✦</div>
            <p>Your generated face will appear here.</p>
        </div>
    `;
}


// ===== UPLOAD AUDIO =====

audioInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) return;

    const allowedExtensions = [".wav", ".mp3", ".ogg", ".webm"];

    const extension = file.name
        .substring(file.name.lastIndexOf("."))
        .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
        alert("Please select a WAV, MP3, OGG, or WEBM audio file.");
        audioInput.value = "";
        return;
    }

    setSelectedAudio(file);
});


// ===== START RECORDING =====

recordButton.addEventListener("click", async function () {

    if (
        !navigator.mediaDevices?.getUserMedia ||
        typeof MediaRecorder === "undefined"
    ) {
        alert("Audio recording is not supported by this browser.");
        return;
    }

    try {

        microphoneStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        let mimeType = "";

        const formats = [
            "audio/webm;codecs=opus",
            "audio/webm"
        ];

        for (const format of formats) {
            if (MediaRecorder.isTypeSupported(format)) {
                mimeType = format;
                break;
            }
        }

        if (!mimeType) {
            throw new Error("No compatible recording format found.");
        }

        recordedChunks = [];

        mediaRecorder = new MediaRecorder(microphoneStream, {
            mimeType: mimeType
        });

        mediaRecorder.ondataavailable = function (event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = function () {

            const audioBlob = new Blob(recordedChunks, {
                type: mimeType
            });

            const recordedFile = new File(
                [audioBlob],
                "recorded_audio.webm",
                { type: mimeType }
            );

            setSelectedAudio(recordedFile);

            if (microphoneStream) {
                microphoneStream.getTracks().forEach(track => track.stop());
                microphoneStream = null;
            }

            recordButton.disabled = false;
            recordButton.textContent = "🎙️ RECORD AGAIN";

            stopButton.disabled = true;
            stopButton.style.opacity = "0.5";
        };

        mediaRecorder.start();

        recordButton.disabled = true;
        recordButton.textContent = "🔴 RECORDING...";

        stopButton.disabled = false;
        stopButton.style.opacity = "1";

    } catch (error) {

        if (microphoneStream) {
            microphoneStream.getTracks().forEach(track => track.stop());
            microphoneStream = null;
        }

        alert("Microphone error: " + error.message);
    }
});


// ===== STOP RECORDING =====

stopButton.addEventListener("click", function () {

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
});


// ===== GENERATE FACE =====

generateButton.addEventListener("click", async function () {

    if (!selectedAudio) {
        alert("Please upload or record an audio file first!");
        return;
    }

    generateButton.disabled = true;
    generateButton.textContent = "GENERATING FACE...";

    result.classList.add("hidden");
    loadingScreen.classList.remove("hidden");
    // Automatically jump to the result area
    loadingScreen.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

    const loadingMessages = [
        "Preparing your audio...",
        "Extracting speech features...",
        "Analysing voice characteristics...",
        "Generating facial representation..."
    ];

    let messageIndex = 0;

    loadingMessage.textContent = loadingMessages[0];

    const messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % loadingMessages.length;
        loadingMessage.textContent = loadingMessages[messageIndex];
    }, 3500);

    result.innerHTML = "<p>Processing audio. Please wait...</p>";

    const formData = new FormData();
    formData.append("audio", selectedAudio);

    try {

        const response = await fetch("/generate", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        result.innerHTML = `
            <h2>GENERATED FACE</h2>
            <img
                src="${data.image_url}?t=${Date.now()}"
                alt="AI Generated Face"
            >
            <p>${data.message}</p>
        `;

    } catch (error) {

        result.innerHTML = `
            <p style="color:#e45b63;">
                ${error.message}
            </p>
        `;

        console.error(error);

    } finally {

        clearInterval(messageInterval);

        loadingScreen.classList.add("hidden");
        result.classList.remove("hidden");

        generateButton.disabled = !selectedAudio;
        generateButton.innerHTML = 'GENERATE FACE <span>→</span>';

        // Show the generated face in the same screen position
        result.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
});

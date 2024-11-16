const initCamera = () => {
    const video = document.getElementById('camera-preview');
    const captureBtn = document.getElementById('capture-btn');
    const fileUpload = document.getElementById('file-upload');
    const uploadForm = document.getElementById('upload-form');
    const recognitionResult = document.getElementById('recognition-result');
    const switchToUploadBtn = document.createElement('button');
    let stream = null;

    // Add switch button
    switchToUploadBtn.className = 'btn btn-secondary mt-3';
    switchToUploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Switch to File Upload';
    document.querySelector('.camera-container').appendChild(switchToUploadBtn);

    switchToUploadBtn.addEventListener('click', () => {
        stopCamera();
        video.parentElement.classList.add('d-none');
        fileUpload.classList.remove('d-none');
        switchToUploadBtn.classList.add('d-none');
    });

    // Show loading indicator during file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('image-upload');
            
            if (!fileInput.files || !fileInput.files[0]) {
                showErrorMessage('Please select an image file first');
                return;
            }

            const file = fileInput.files[0];
            if (!file.type.startsWith('image/')) {
                showErrorMessage('Please select a valid image file (JPEG, PNG, etc.)');
                return;
            }

            recognitionResult.innerHTML = `
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Analyzing image...</p>
            `;

            const formData = new FormData();
            formData.append('image', file);

            handleImageSubmission(formData);
        });
    }
    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            video.srcObject = stream;
            video.parentElement.classList.remove('d-none');
            fileUpload.classList.add('d-none');
            cameraError.classList.add('d-none');
        } catch (err) {
            console.error('Camera error:', {
                message: err.message,
                name: err.name,
                stack: err.stack
            });
            video.parentElement.classList.add('d-none');
            fileUpload.classList.remove('d-none');
            cameraError.classList.remove('d-none');
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => {
                track.stop();
            });
            stream = null;
        }
        if (video.srcObject) {
            video.srcObject = null;
        }
    }

    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.camera-container').insertAdjacentElement('afterend', notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function showErrorMessage(message, error = null) {
        if (error) {
            console.error('Error:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
        }
        recognitionResult.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>${message}
            </div>
        `;
    }

    function handleImageSubmission(formData) {
        recognitionResult.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    formData.append('location', `${position.coords.latitude},${position.coords.longitude}`);
                },
                error => {
                    console.warn('Location error:', {
                        message: error.message,
                        name: error.name,
                        code: error.code
                    });
                }
            );
        }
        
        fetch('/api/recognize', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            recognitionResult.innerHTML = `
                <div class="alert alert-success">
                    <h4 class="alert-heading">
                        <i class="fas fa-check-circle me-2"></i>${data.result}
                    </h4>
                    <hr>
                    <div class="animal-details">
                        <p><strong>Habitat:</strong> ${data.details.habitat}</p>
                        <p><strong>Diet:</strong> ${data.details.diet}</p>
                        <p><strong>Behavior:</strong> ${data.details.behavior}</p>
                        <h5 class="mt-3">Interesting Facts:</h5>
                        <ul class="list-unstyled">
                            ${data.details.interesting_facts.map(fact => 
                                `<li><i class="fas fa-circle-info me-2"></i>${fact}</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Recognition error:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            showErrorMessage('Failed to process image. Please try again or use a different image.', error);
        });
    }

    // Handle camera capture
    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            try {
                // Ensure video is playing and has valid dimensions
                if (!video.videoWidth || !video.videoHeight) {
                    throw new Error('Video stream not ready. Please wait or try again.');
                }

                // Set up canvas with video dimensions
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                const ctx = canvas.getContext('2d');
                if (!ctx) {
                    throw new Error('Could not get canvas context');
                }

                // Draw the video frame to canvas
                ctx.drawImage(video, 0, 0);

                // Create blob with proper error handling
                canvas.toBlob(
                    (blob) => {
                        if (!blob) {
                            showErrorMessage('Failed to capture image. Please try again.');
                            return;
                        }
                        const formData = new FormData();
                        formData.append('camera_image', blob, 'capture.jpg');
                        handleImageSubmission(formData);
                        stopCamera();
                    },
                    'image/jpeg',
                    0.95
                );
            } catch (error) {
                console.error('Capture error:', {
                    message: error.message,
                    name: error.name,
                    stack: error.stack
                });
                showErrorMessage('Failed to capture image. Please try again or use file upload.', error);
            }
        });
    }

    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('image-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                showErrorMessage('Please select an image file first');
                return;
            }

            if (!file.type.startsWith('image/')) {
                showErrorMessage('Please select a valid image file (JPEG, PNG, etc.)');
                return;
            }

            const formData = new FormData();
            formData.append('image', file);
            handleImageSubmission(formData);
        });
    }

    // Start camera by default
    startCamera();
};

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCamera);
} else {
    initCamera();
}

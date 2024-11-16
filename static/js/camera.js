const initCamera = () => {
    const video = document.getElementById('camera-preview');
    const captureBtn = document.getElementById('capture-btn');
    const fileUpload = document.getElementById('file-upload');
    const uploadForm = document.getElementById('upload-form');
    const recognitionResult = document.getElementById('recognition-result');
    const switchToUploadBtn = document.createElement('button');
    const canvas = document.createElement('canvas');
    const errorContainer = document.getElementById('camera-error');
    let stream = null;
    let isStreamReady = false;

    // Add switch button
    switchToUploadBtn.className = 'btn btn-secondary mt-3';
    switchToUploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Switch to File Upload';
    switchToUploadBtn.classList.add('d-none');
    document.querySelector('.camera-container').appendChild(switchToUploadBtn);

    switchToUploadBtn.addEventListener('click', () => {
        stopCamera();
        video.parentElement.classList.add('d-none');
        fileUpload.classList.remove('d-none');
        switchToUploadBtn.classList.add('d-none');
    });

    async function startCamera() {
        try {
            if (errorContainer) {
                errorContainer.classList.add('d-none');
            }

            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            video.srcObject = stream;
            
            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Video stream initialization timeout'));
                }, 5000);

                video.addEventListener('loadedmetadata', async () => {
                    clearTimeout(timeout);
                    try {
                        await video.play();
                        isStreamReady = true;
                        resolve();
                    } catch (err) {
                        reject(err);
                    }
                }, { once: true });

                video.addEventListener('error', (err) => {
                    clearTimeout(timeout);
                    reject(new Error('Failed to initialize video stream'));
                }, { once: true });
            });

            video.parentElement.classList.remove('d-none');
            fileUpload.classList.add('d-none');
            if (errorContainer) {
                errorContainer.classList.add('d-none');
            }
            switchToUploadBtn.classList.remove('d-none');
        } catch (err) {
            console.error('Camera error:', {
                message: err.message,
                name: err.name,
                stack: err.stack
            });
            handleCameraError();
        }
    }

    function handleCameraError() {
        video.parentElement.classList.add('d-none');
        fileUpload.classList.remove('d-none');
        if (errorContainer) {
            errorContainer.classList.remove('d-none');
        }
        switchToUploadBtn.classList.add('d-none');
        isStreamReady = false;
    }

    function stopCamera() {
        isStreamReady = false;
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
        }, 5000);
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
        recognitionResult.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Analyzing image...</p>
            </div>
        `;
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    formData.append('location', `${position.coords.latitude},${position.coords.longitude}`);
                    submitImage(formData);
                },
                error => {
                    console.warn('Location error:', {
                        message: error.message,
                        name: error.name,
                        code: error.code
                    });
                    submitImage(formData);
                },
                { timeout: 10000 }
            );
        } else {
            submitImage(formData);
        }
    }

    async function submitImage(formData) {
        try {
            const response = await fetch('/api/recognize', {
                method: 'POST',
                body: formData
            });

            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                let errorMessage = 'Failed to process image';
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.error || `Server error (${response.status})`;
                } else if (response.status === 500) {
                    errorMessage = 'Internal server error. Please try again later.';
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
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

            if (data.new_badges && data.new_badges.length > 0) {
                showNotification(`Congratulations! You earned ${data.new_badges.length} new badge(s): ${data.new_badges.join(', ')}`);
            }
        } catch (error) {
            showErrorMessage(error.message || 'Failed to process image. Please try again or use a different image.', error);
        }
    }

    // Handle camera capture
    if (captureBtn) {
        captureBtn.addEventListener('click', async () => {
            try {
                if (!stream || !video.srcObject || !isStreamReady) {
                    throw new Error('Camera stream is not ready. Please wait or try again.');
                }

                // Verify video dimensions are available
                if (!video.videoWidth || !video.videoHeight) {
                    throw new Error('Video stream dimensions not available. Please wait.');
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
                showErrorMessage(error.message, error);
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
    startCamera().catch(error => {
        console.error('Failed to start camera:', error);
        handleCameraError();
    });
};

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCamera);
} else {
    initCamera();
}

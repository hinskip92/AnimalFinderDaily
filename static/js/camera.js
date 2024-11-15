const initCamera = () => {
    const video = document.getElementById('camera-preview');
    const captureBtn = document.getElementById('capture-btn');
    const canvas = document.getElementById('capture-canvas');
    const cameraError = document.getElementById('camera-error');
    const fileUpload = document.getElementById('file-upload');
    const uploadForm = document.getElementById('upload-form');
    const recognitionResult = document.getElementById('recognition-result');
    let stream = null;

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
            console.error('Camera error:', err);
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

    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            showNotification('<i class="fas fa-check me-2"></i>Link copied to clipboard!');
        } catch (error) {
            console.error('Clipboard error:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            showNotification('Failed to copy link to clipboard', 'danger');
        }
    }

    function openShareWindow(url, platform) {
        const shareWindow = window.open(url, '_blank');
        
        // Check if popup was blocked and use fallback
        if (!shareWindow || shareWindow.closed || typeof shareWindow.closed === 'undefined') {
            // Fallback to opening in new tab
            window.open(url, '_blank');
        }
        
        return shareWindow;
    }

    function createSocialShareButton(platform, url, icon, color) {
        const button = document.createElement('button');
        button.className = `btn btn-outline-${color}`;
        button.innerHTML = `<i class="${icon} me-2"></i>Share on ${platform}`;
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            try {
                const shareWindow = openShareWindow(url, platform);
                if (!shareWindow) {
                    throw new Error('Failed to open share window');
                }
            } catch (error) {
                console.error(`${platform} share error:`, {
                    message: error.message,
                    name: error.name,
                    stack: error.stack
                });
                showNotification(`Failed to open ${platform} share. ${error.message}`, 'warning');
            }
        });
        
        return button;
    }

    function showShareOptions(shareUrl) {
        // Remove existing share container if present
        const existingShare = document.querySelector('.share-container');
        if (existingShare) {
            existingShare.remove();
        }

        try {
            // Encode the URL and text properly
            const encodedUrl = encodeURIComponent(shareUrl);
            const encodedText = encodeURIComponent('Check out this animal I spotted!');
            
            const shareContainer = document.createElement('div');
            shareContainer.className = 'share-container mt-3';
            
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'd-flex justify-content-center gap-2 flex-wrap';
            
            // Twitter share button with properly encoded URL and text
            const twitterUrl = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`;
            buttonContainer.appendChild(
                createSocialShareButton(
                    'Twitter',
                    twitterUrl,
                    'fab fa-twitter',
                    'info'
                )
            );
            
            // Facebook share button
            const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
            buttonContainer.appendChild(
                createSocialShareButton(
                    'Facebook',
                    facebookUrl,
                    'fab fa-facebook',
                    'primary'
                )
            );
            
            // Copy link button
            const copyButton = document.createElement('button');
            copyButton.className = 'btn btn-outline-secondary';
            copyButton.innerHTML = '<i class="fas fa-link me-2"></i>Copy Link';
            copyButton.addEventListener('click', () => copyToClipboard(shareUrl));
            buttonContainer.appendChild(copyButton);
            
            shareContainer.appendChild(buttonContainer);
            recognitionResult.insertAdjacentElement('afterend', shareContainer);
        } catch (error) {
            console.error('Share options error:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            showErrorMessage('Failed to create share options', error);
        }
    }

    function showBadgeNotification(badges) {
        if (!badges || badges.length === 0) return;
        
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show';
        notification.innerHTML = `
            <strong>🎉 New Achievement${badges.length > 1 ? 's' : ''}!</strong><br>
            ${badges.join(', ')}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.camera-container').insertAdjacentElement('afterend', notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
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
            if (data.new_badges) {
                showBadgeNotification(data.new_badges);
            }
            if (data.share_url) {
                showShareOptions(data.share_url);
            }
        })
        .catch(error => {
            console.error('Recognition error:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            showErrorMessage('Error processing image. Please try again.', error);
        });
    }

    // Handle camera capture
    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            try {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                
                if (!ctx) {
                    throw new Error('Could not get canvas context');
                }
                
                ctx.drawImage(video, 0, 0);
                
                canvas.toBlob(blob => {
                    if (!blob) {
                        throw new Error('Failed to create blob from canvas');
                    }
                    
                    const formData = new FormData();
                    formData.append('camera_image', blob, 'capture.jpg');
                    handleImageSubmission(formData);
                    stopCamera();
                }, 'image/jpeg', 0.95);
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
                showErrorMessage('Please select a file first');
                return;
            }

            if (!file.type.startsWith('image/')) {
                showErrorMessage('Please select an image file');
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
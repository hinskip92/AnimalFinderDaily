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
            stream.getTracks().forEach(track => track.stop());
        }
    }

    function showShareOptions(shareUrl) {
        const existingShare = document.querySelector('.share-container');
        if (existingShare) {
            existingShare.remove();
        }

        const shareContainer = document.createElement('div');
        shareContainer.className = 'share-container mt-3';
        shareContainer.innerHTML = `
            <div class="d-flex justify-content-center gap-2">
                <button onclick="window.open('https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}', '_blank')" 
                        class="btn btn-outline-info">
                    <i class="fab fa-twitter me-2"></i>Share on Twitter
                </button>
                <button onclick="window.open('https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}', '_blank')" 
                        class="btn btn-outline-primary">
                    <i class="fab fa-facebook me-2"></i>Share on Facebook
                </button>
                <button onclick="navigator.clipboard.writeText('${shareUrl}').then(() => alert('Link copied!'))" 
                        class="btn btn-outline-secondary">
                    <i class="fas fa-link me-2"></i>Copy Link
                </button>
            </div>
        `;
        recognitionResult.insertAdjacentElement('afterend', shareContainer);
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
        
        // Add location if available
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                formData.append('location', `${position.coords.latitude},${position.coords.longitude}`);
            });
        }
        
        fetch('/api/recognize', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            recognitionResult.textContent = data.result;
            if (data.new_badges) {
                showBadgeNotification(data.new_badges);
            }
            if (data.share_url) {
                showShareOptions(data.share_url);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            recognitionResult.innerHTML = '<div class="alert alert-danger">Error processing image. Please try again.</div>';
        });
    }

    // Handle camera capture
    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            canvas.toBlob(blob => {
                const formData = new FormData();
                formData.append('camera_image', blob, 'capture.jpg');
                handleImageSubmission(formData);
                stopCamera();
            }, 'image/jpeg');
        });
    }

    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('image-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file first');
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

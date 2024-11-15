const initCamera = () => {
    const video = document.getElementById('camera-preview');
    const captureBtn = document.getElementById('capture-btn');
    const canvas = document.getElementById('capture-canvas');
    let stream = null;

    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            video.srcObject = stream;
        } catch (err) {
            console.error('Camera error:', err);
            alert('Could not access camera');
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }

    function showShareOptions(shareUrl) {
        const shareContainer = document.createElement('div');
        shareContainer.className = 'mt-3';
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
        document.getElementById('recognition-result').insertAdjacentElement('afterend', shareContainer);
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
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    captureBtn.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        canvas.toBlob(blob => {
            const formData = new FormData();
            formData.append('image', blob);
            
            // Add task_id if available
            const taskId = document.getElementById('task-id');
            if (taskId) {
                formData.append('task_id', taskId.value);
            }
            
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
            .then(response => response.json())
            .then(data => {
                document.getElementById('recognition-result').textContent = data.result;
                if (data.new_badges) {
                    showBadgeNotification(data.new_badges);
                }
                if (data.share_url) {
                    showShareOptions(data.share_url);
                }
                stopCamera();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error recognizing animal');
            });
        }, 'image/jpeg');
    });

    startCamera();
};

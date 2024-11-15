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

    captureBtn.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        canvas.toBlob(blob => {
            const formData = new FormData();
            formData.append('image', blob);
            
            fetch('/api/recognize', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('recognition-result').textContent = data;
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

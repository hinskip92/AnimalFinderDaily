const getLocationAndTasks = () => {
    const tasksList = document.getElementById('tasks-list');
    
    function showError(message) {
        tasksList.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }

    function updateTasks(tasks) {
        tasksList.innerHTML = '';
        
        const dailyTasks = document.createElement('div');
        dailyTasks.innerHTML = `
            <h3>Daily Tasks</h3>
            <ul class="list-group mb-4">
                ${tasks.daily.map(task => 
                    `<li class="list-group-item">${task}</li>`
                ).join('')}
            </ul>
        `;
        
        const weeklyTasks = document.createElement('div');
        weeklyTasks.innerHTML = `
            <h3>Weekly Tasks</h3>
            <ul class="list-group">
                ${tasks.weekly.map(task => 
                    `<li class="list-group-item">${task}</li>`
                ).join('')}
            </ul>
        `;
        
        tasksList.appendChild(dailyTasks);
        tasksList.appendChild(weeklyTasks);
    }

    if (!navigator.geolocation) {
        showError('Geolocation is not supported by your browser');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        position => {
            fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                })
            })
            .then(response => response.json())
            .then(updateTasks)
            .catch(error => showError('Error fetching tasks'));
        },
        () => showError('Could not get your location')
    );
};

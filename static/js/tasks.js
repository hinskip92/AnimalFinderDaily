const updateTasksDisplay = (tasks) => {
    const tasksContainer = document.getElementById('current-tasks');
    if (!tasksContainer) return;

    if (!tasks || (!tasks.daily?.length && !tasks.weekly?.length)) {
        tasksContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-check-circle me-2"></i>No active tasks
            </div>
        `;
        return;
    }

    const dailyTasks = document.createElement('div');
    dailyTasks.innerHTML = `
        <h4 class="mb-3">Daily Tasks</h4>
        ${tasks.daily.map(task => `
            <div class="task-item">
                <div class="task-status">
                    <i class="far fa-circle"></i>
                </div>
                <div class="task-name">
                    ${task}
                    <span class="task-type-indicator task-type-daily">daily</span>
                </div>
            </div>
        `).join('')}
    `;

    const weeklyTasks = document.createElement('div');
    weeklyTasks.innerHTML = `
        <h4 class="mt-4 mb-3">Weekly Tasks</h4>
        ${tasks.weekly.map(task => `
            <div class="task-item">
                <div class="task-status">
                    <i class="far fa-circle"></i>
                </div>
                <div class="task-name">
                    ${task}
                    <span class="task-type-indicator task-type-weekly">weekly</span>
                </div>
            </div>
        `).join('')}
    `;

    tasksContainer.innerHTML = '';
    tasksContainer.appendChild(dailyTasks);
    tasksContainer.appendChild(weeklyTasks);
};

const fetchTasks = async () => {
    if (!navigator.geolocation) {
        updateTasksDisplay({ daily: [], weekly: [] });
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
            .then(updateTasksDisplay)
            .catch(error => {
                console.error('Error fetching tasks:', error);
                updateTasksDisplay({ daily: [], weekly: [] });
            });
        },
        error => {
            console.error('Geolocation error:', error);
            updateTasksDisplay({ daily: [], weekly: [] });
        }
    );
};

// Initialize tasks display
document.addEventListener('DOMContentLoaded', fetchTasks);
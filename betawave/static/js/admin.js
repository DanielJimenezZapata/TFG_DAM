// Funciones para el panel de administración

function deleteUser(userId, username) {
    if (confirm(`¿Estás seguro de que deseas eliminar al usuario ${username}?`)) {
        fetch('/admin/delete_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userId: userId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.error || 'Error al eliminar usuario');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al eliminar usuario');
        });
    }
}



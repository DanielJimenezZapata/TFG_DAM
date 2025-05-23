// Funciones para el panel de administración

function editUser(userId, username, email, role) {
    const modal = document.getElementById('editUserModal');
    document.getElementById('userId').value = userId;
    document.getElementById('editUsername').value = username;
    document.getElementById('editEmail').value = email;
    document.getElementById('editRole').value = role;
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('editUserModal');
    modal.style.display = 'none';
}

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

// Cerrar el modal si se hace clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('editUserModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

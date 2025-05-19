document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const audioPlayer = document.getElementById('audio-player');
    const songList = document.getElementById('song-list');
    const favoritesList = document.getElementById('favorites-list');
    const nowPlayingTitle = document.getElementById('now-playing-title');
    const nowPlayingArtist = document.getElementById('now-playing-artist');
    const nowPlayingCover = document.getElementById('now-playing-cover');
    const favoriteBtn = document.getElementById('favorite-btn');
    const addSongBtn = document.getElementById('add-song-btn');
    const searchInput = document.querySelector('.search-bar input');
    const navMenuItems = document.querySelectorAll('.nav-menu li');
    const playlistItems = document.querySelectorAll('.playlists li');
    const allSongsSection = document.getElementById('all-songs-section');
    const favoritesSection = document.getElementById('favorites-section');
    
    let currentSongId = null;
    
    // Load initial data
    loadSongs();
    loadFavorites();
    
    // Event listeners
    addSongBtn.addEventListener('click', addSong);
    favoriteBtn.addEventListener('click', toggleCurrentFavorite);
    searchInput.addEventListener('input', handleSearch);
    
    // Navigation event listeners
    navMenuItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            navMenuItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            const sectionName = this.querySelector('span').textContent;
            loadSection(sectionName);
        });
    });
    
    playlistItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            playlistItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            const sectionName = this.querySelector('span').textContent;
            loadSection(sectionName);
        });
    });
    
    // Set "Mis Canciones" as active by default
    document.querySelector('.playlists li:first-child').classList.add('active');
    
    // Functions
    function loadSection(sectionName) {
        // Hide all sections
        allSongsSection.style.display = 'none';
        favoritesSection.style.display = 'none';
        
        switch(sectionName) {
            case 'Inicio':
            case 'Mis Canciones':
                allSongsSection.style.display = 'block';
                loadSongs();
                break;
            case 'Buscar':
                allSongsSection.style.display = 'block';
                searchInput.focus();
                break;
            case 'Favoritos':
            case 'Favoritas':
                favoritesSection.style.display = 'block';
                loadFavorites();
                break;
            case 'Crear Playlist':
                alert('Funcionalidad de crear playlist en desarrollo');
                break;
        }
    }
    
    function handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase();
        
        // Determine which section is active
        const activeSection = favoritesSection.style.display === 'block' ? 
            favoritesList : songList;
        
        const songCards = activeSection.querySelectorAll('.song-card');
        
        songCards.forEach(card => {
            const title = card.querySelector('.song-title').textContent.toLowerCase();
            const artist = card.querySelector('.song-artist').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || artist.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    function loadSongs() {
        fetch('/api/songs')
            .then(response => response.json())
            .then(songs => {
                renderSongs(songs, songList, false);
            })
            .catch(error => {
                console.error('Error loading songs:', error);
                songList.innerHTML = '<div class="error-message">Error al cargar canciones</div>';
            });
    }
    
    function loadFavorites() {
        fetch('/api/favorites')
            .then(response => response.json())
            .then(favorites => {
                renderSongs(favorites, favoritesList, true);
            })
            .catch(error => {
                console.error('Error loading favorites:', error);
                favoritesList.innerHTML = '<div class="error-message">Error al cargar favoritos</div>';
            });
    }
    
    function renderSongs(songs, container, isFavoriteList) {
        container.innerHTML = '';
        
        if (songs.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = isFavoriteList ? 
                'No tienes canciones favoritas aún' : 
                'No tienes canciones aún. ¡Añade alguna!';
            container.appendChild(emptyMessage);
            return;
        }
        
        songs.forEach(song => {
            const songCard = document.createElement('div');
            songCard.className = 'song-card';
            songCard.dataset.songId = song.id;
            
            // Extract video ID from YouTube URL for thumbnail
            let videoId = null;
            try {
                const url = new URL(song.url);
                videoId = url.searchParams.get('v') || url.pathname.split('/').pop();
            } catch (e) {
                console.error('Error parsing URL:', e);
            }
            
            const coverUrl = videoId ? 
                `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : 
                'https://via.placeholder.com/300';
            
            songCard.innerHTML = `
                <div class="song-cover">
                    <img src="${coverUrl}" alt="Portada de canción">
                </div>
                <div class="song-title">${song.name}</div>
                <div class="song-artist">${document.querySelector('.username').textContent}</div>
                <div class="song-actions">
                    <button class="song-action-btn favorite-btn" data-song-id="${song.id}">
                        <i class="far fa-heart"></i>
                    </button>
                    <button class="song-action-btn download-btn" data-song-id="${song.id}">
                        <i class="fas fa-download"></i>
                    </button>
                    ${!isFavoriteList ? `
                    <button class="song-action-btn delete-btn" data-song-id="${song.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                    ` : ''}
                </div>
            `;
            
            // Add event listeners to action buttons
            const favoriteBtn = songCard.querySelector('.favorite-btn');
            const downloadBtn = songCard.querySelector('.download-btn');
            const deleteBtn = songCard.querySelector('.delete-btn');
            
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFavorite(song.id, favoriteBtn);
            });
            
            downloadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showDownloadMenu(song.id, e);
            });
            
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteSong(song.id);
                });
            }
            
            // Check if song is favorite and update button
            checkFavoriteStatus(song.id).then(isFavorite => {
                if (isFavorite) {
                    favoriteBtn.innerHTML = '<i class="fas fa-heart"></i>';
                    favoriteBtn.classList.add('active');
                }
            });
            
            // Play song when card is clicked
            songCard.addEventListener('click', () => playSong(song.id, song.name, coverUrl));
            
            container.appendChild(songCard);
        });
    }
    
    function playSong(songId, songName, coverUrl) {
        currentSongId = songId;
        
        fetch('/api/play', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.audio_stream_url) {
                // Update player UI
                nowPlayingTitle.textContent = songName;
                nowPlayingArtist.textContent = document.querySelector('.username').textContent;
                nowPlayingCover.src = coverUrl;
                
                // Set audio source and play
                audioPlayer.src = data.audio_stream_url;
                audioPlayer.play()
                    .then(() => {
                        console.log(`Reproduciendo canción ID: ${songId}`);
                        updateFavoriteButton(songId);
                    })
                    .catch(e => {
                        console.error("Error al reproducir:", e);
                        if (data.fallback_url) {
                            window.open(data.fallback_url, '_blank');
                        }
                    });
            } else if (data.fallback_url) {
                window.open(data.fallback_url, '_blank');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.status === 401) {
                window.location.href = '/login';
            } else {
                alert('Error: ' + (error.message || 'No se pudo reproducir la canción'));
                if (error.fallback_url) {
                    window.open(error.fallback_url, '_blank');
                }
            }
        });
    }
    
    function addSong() {
        const songName = document.getElementById('song-name').value;
        const songUrl = document.getElementById('song-url').value;
        
        if (!songName || !songUrl) {
            showAlert('Por favor ingresa nombre y URL de la canción', 'error');
            return;
        }
        
        // Validate YouTube URL
        if (!isValidYouTubeUrl(songUrl)) {
            showAlert('Por favor ingresa una URL válida de YouTube', 'error');
            return;
        }
        
        fetch('/api/add_song', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                song_name: songName,
                song_url: songUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Canción añadida correctamente!', 'success');
                document.getElementById('song-name').value = '';
                document.getElementById('song-url').value = '';
                loadSongs();
            } else {
                showAlert('Error: ' + (data.error || 'No se pudo añadir la canción'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al conectar con el servidor', 'error');
        });
    }
    
    function isValidYouTubeUrl(url) {
        const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
        return pattern.test(url);
    }
    
    function deleteSong(songId) {
        if (!confirm('¿Estás seguro de que quieres eliminar esta canción?')) {
            return;
        }
        
        fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Canción eliminada correctamente', 'success');
                loadSongs();
                loadFavorites();
                
                // If deleted song is currently playing, stop it
                if (currentSongId === songId) {
                    audioPlayer.pause();
                    audioPlayer.src = '';
                    nowPlayingTitle.textContent = 'No hay canción seleccionada';
                    nowPlayingCover.src = 'https://via.placeholder.com/60';
                    currentSongId = null;
                    updateFavoriteButton(null);
                }
            } else {
                showAlert('Error al eliminar la canción', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al eliminar la canción', 'error');
        });
    }
    
    function checkFavoriteStatus(songId) {
        return fetch('/api/is_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        })
        .then(response => response.json())
        .then(data => data.is_favorite)
        .catch(error => {
            console.error('Error checking favorite status:', error);
            return false;
        });
    }
    
    function toggleFavorite(songId, button) {
        fetch('/api/toggle_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.is_favorite !== undefined) {
                if (button) {
                    button.innerHTML = data.is_favorite ? 
                        '<i class="fas fa-heart"></i>' : 
                        '<i class="far fa-heart"></i>';
                    button.classList.toggle('active', data.is_favorite);
                }
                
                // Update favorite button in player if this is the current song
                if (currentSongId === songId) {
                    updateFavoriteButton(songId);
                }
                
                // Reload favorites list
                loadFavorites();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.status === 401) {
                window.location.href = '/login';
            }
        });
    }
    
    function toggleCurrentFavorite() {
        if (currentSongId) {
            toggleFavorite(currentSongId, favoriteBtn);
        }
    }
    
    function updateFavoriteButton(songId) {
        if (!songId) {
            favoriteBtn.innerHTML = '<i class="far fa-heart"></i>';
            favoriteBtn.classList.remove('active');
            return;
        }
        
        checkFavoriteStatus(songId).then(isFavorite => {
            favoriteBtn.innerHTML = isFavorite ? 
                '<i class="fas fa-heart"></i>' : 
                '<i class="far fa-heart"></i>';
            favoriteBtn.classList.toggle('active', isFavorite);
        });
    }
    
    function showDownloadMenu(songId, event) {
        const menu = document.createElement('div');
        menu.className = 'format-menu';
        menu.innerHTML = `
            <div class="format-option" data-format="mp3">MP3</div>
            <div class="format-option" data-format="wav">WAV</div>
            <div class="format-option" data-format="ogg">OGG</div>
        `;
        
        const rect = event.target.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.left = `${rect.left}px`;
        menu.style.top = `${rect.bottom + window.scrollY}px`;
        menu.style.zIndex = '1000';
        
        menu.querySelectorAll('.format-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                downloadSong(songId, option.dataset.format);
                document.body.removeChild(menu);
            });
        });
        
        const closeMenu = () => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
            document.removeEventListener('click', closeMenu);
        };
        
        document.addEventListener('click', closeMenu);
        document.body.appendChild(menu);
    }
    
    function downloadSong(songId, format) {
        showAlert(`Preparando descarga en formato ${format.toUpperCase()}...`, 'info');
        
        fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                song_id: songId,
                format: format
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la descarga');
            }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `cancion_${songId}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al descargar la canción', 'error');
        });
    }
    
    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(alert, mainContent.firstChild);
        
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    }
    
    // Audio player event listeners
    audioPlayer.addEventListener('play', () => {
        console.log('Audio started playing');
    });
    
    audioPlayer.addEventListener('pause', () => {
        console.log('Audio paused');
    });
    
    audioPlayer.addEventListener('ended', () => {
        console.log('Audio ended');
    });
    
    audioPlayer.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        showAlert('Error al reproducir la canción', 'error');
    });
});
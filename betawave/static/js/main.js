document.addEventListener('DOMContentLoaded', function() {
    // Player Configuration
    const VOLUME_STEP = 0.1;            // Increment/decrement for volume changes
    const SEEK_STEP = 5;                // Seconds to seek forward/backward
    const UPDATE_INTERVAL = 100;        // Milliseconds between progress updates
    const TRANSITION_DURATION = 300;     // Milliseconds for animations
    
    // Elements
    const audioPlayer = document.getElementById('audio-player');
    const songList = document.getElementById('song-list');
    const favoritesList = document.getElementById('favorites-list');
    const nowPlayingTitle = document.getElementById('now-playing-title');
    const nowPlayingArtist = document.getElementById('now-playing-artist');
    const nowPlayingCover = document.getElementById('now-playing-cover');
    const favoriteBtn = document.getElementById('favorite-btn');
    const playBtn = document.getElementById('play-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const currentTimeEl = document.getElementById('current-time');
    const durationEl = document.getElementById('duration');
    const progressBar = document.querySelector('.progress');
    const seekSlider = document.querySelector('.seek-slider');
    const volumeSlider = document.querySelector('.volume-slider');
    const volumeIcon = document.querySelector('.volume-control i');
    const addSongBtn = document.getElementById('add-song-btn');
    const searchInput = document.querySelector('.search-bar input');
    const navMenuItems = document.querySelectorAll('.nav-menu li');
    const playlistItems = document.querySelectorAll('.playlists li');
    const allSongsSection = document.getElementById('all-songs-section');
    const favoritesSection = document.getElementById('favorites-section');
    
    let currentSongId = null;
    let currentPlaylist = [];
    let isPlayingFavorites = false;
    
    // Load initial data
    loadSongs();
    loadFavorites();
      // Event listeners
    addSongBtn.addEventListener('click', addSong);
    favoriteBtn.addEventListener('click', toggleCurrentFavorite);
    searchInput.addEventListener('input', handleSearch);

    // Player control event listeners
    playBtn.addEventListener('click', togglePlay);
    nextBtn.addEventListener('click', playNextSong);
    prevBtn.addEventListener('click', playPrevSong);
    seekSlider.addEventListener('input', seekTo);
    volumeSlider.addEventListener('input', updateVolume);
    volumeIcon.addEventListener('click', toggleMute);

    // Audio player event listeners
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('loadedmetadata', () => {
        durationEl.textContent = formatTime(audioPlayer.duration);
        seekSlider.max = Math.floor(audioPlayer.duration);
    });
    audioPlayer.addEventListener('play', () => {
        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
    });
    audioPlayer.addEventListener('pause', () => {
        playBtn.innerHTML = '<i class="fas fa-play"></i>';
    });
    audioPlayer.addEventListener('ended', playNextSong);
    
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
    
    // Progress update interval
    setInterval(updateProgress, UPDATE_INTERVAL);
    
    // Keyboard shortcuts for player
    document.addEventListener('keydown', (e) => {
        // Only if not in an input field
        if (e.target.tagName === 'INPUT') return;
        
        switch(e.key.toLowerCase()) {
            case ' ':
                e.preventDefault();
                togglePlay();
                break;
            case 'arrowright':
                if (e.ctrlKey) {
                    playNextSong();
                } else {
                    audioPlayer.currentTime = Math.min(
                        audioPlayer.currentTime + SEEK_STEP,
                        audioPlayer.duration
                    );
                }
                break;
            case 'arrowleft':
                if (e.ctrlKey) {
                    playPrevSong();
                } else {
                    audioPlayer.currentTime = Math.max(
                        audioPlayer.currentTime - SEEK_STEP,
                        0
                    );
                }
                break;
            case 'arrowup':
                e.preventDefault();
                audioPlayer.volume = Math.min(
                    audioPlayer.volume + VOLUME_STEP,
                    1
                );
                volumeSlider.value = audioPlayer.volume * 100;
                updateVolume();
                break;
            case 'arrowdown':
                e.preventDefault();
                audioPlayer.volume = Math.max(
                    audioPlayer.volume - VOLUME_STEP,
                    0
                );
                volumeSlider.value = audioPlayer.volume * 100;
                updateVolume();
                break;
            case 'm':
                toggleMute();
                break;
        }
    });
    
    // Functions
    function loadSection(sectionName) {
        console.log('Cambiando a sección:', sectionName);
        
        // Hide all sections
        allSongsSection.style.display = 'none';
        favoritesSection.style.display = 'none';
        
        // Guardar la canción actual antes de cambiar de sección
        const currentSong = currentPlaylist.find(song => song.id === currentSongId);
        
        switch(sectionName) {
            case 'Inicio':
            case 'Mis Canciones':
                allSongsSection.style.display = 'block';
                isPlayingFavorites = false;
                loadSongs();
                break;
            case 'Buscar':
                allSongsSection.style.display = 'block';
                isPlayingFavorites = false;
                searchInput.focus();
                break;
            case 'Favoritos':
            case 'Favoritas':
                favoritesSection.style.display = 'block';
                isPlayingFavorites = true;
                loadFavorites();
                break;
            case 'Crear Playlist':
                alert('Funcionalidad de crear playlist en desarrollo');
                break;
        }
        
        // Actualizar la playlist después de cambiar de sección
        setTimeout(() => {
            updateCurrentPlaylist();
            // Si había una canción reproduciéndose, actualizar el estado del reproductor
            if (currentSong && !audioPlayer.paused) {
                const newPlaylist = currentPlaylist;
                // Mantener la reproducción en la nueva sección si la canción existe
                const songInNewPlaylist = newPlaylist.find(song => song.id === currentSong.id);
                if (songInNewPlaylist) {
                    currentSongId = songInNewPlaylist.id;
                }
            }
            console.log('Playlist actualizada después de cambiar sección:', 
                currentPlaylist.map(song => song.name));
        }, 100);
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
        songList.innerHTML = '<div class="loading-message"><i class="fas fa-spinner fa-spin"></i> Cargando canciones...</div>';
        
        fetch('/api/songs')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al cargar las canciones');
                }
                return response.json();
            })
            .then(songs => {
                renderSongs(songs, songList, false);
                // Actualizar la playlist después de cargar las canciones
                updateCurrentPlaylist();
            })
            .catch(error => {
                console.error('Error loading songs:', error);
                songList.innerHTML = '<div class="error-message">Error al cargar canciones</div>';
                showAlert('Error al cargar las canciones', 'error');
            });
    }
    
    function loadFavorites() {
        fetch('/api/favorites')
            .then(response => response.json())
            .then(favorites => {
                renderSongs(favorites, favoritesList, true);
                // Actualizar la playlist después de cargar los favoritos
                updateCurrentPlaylist();
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
                </div>                <div class="song-title">${song.name}</div>
                <div class="song-artist">${song.artist || 'Artista Desconocido'}</div>
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
            songCard.addEventListener('click', () => {
                console.log('Playing song:', { id: song.id, name: song.name, artist: song.artist });
                playSong(song.id, song.name, coverUrl, song.artist);
            });
            
            container.appendChild(songCard);
        });
    }      function updateCurrentPlaylist() {
        const activeSection = favoritesSection.style.display === 'block' ? favoritesList : songList;
        const songCards = Array.from(activeSection.querySelectorAll('.song-card')).filter(
            card => window.getComputedStyle(card).display !== 'none'
        );
        
        if (songCards.length === 0) {
            console.log('No hay canciones visibles en la sección actual');
            currentPlaylist = [];
            return;
        }
        
        currentPlaylist = songCards.map(card => ({
            id: card.dataset.songId,
            name: card.querySelector('.song-title').textContent,
            artist: card.querySelector('.song-artist').textContent,
            coverUrl: card.querySelector('.song-cover img').src
        }));
        
        isPlayingFavorites = favoritesSection.style.display === 'block';
        return currentPlaylist;
    }    function playNextSong() {
        console.log('playNextSong llamado');
        
        // Verificar y actualizar la playlist si es necesario
        if (isPlayingFavorites !== (favoritesSection.style.display === 'block')) {
            updateCurrentPlaylist();
        }
            
        if (!currentPlaylist || currentPlaylist.length === 0) {
            console.log('Lista de reproducción vacía');
            return;
        }

        // Encontrar el índice de la canción actual
        const currentIndex = currentPlaylist.findIndex(song => song.id === currentSongId);
        console.log('Índice actual:', currentIndex);

        // Determinar el siguiente índice
        let nextIndex;
        
        // Si no se encuentra la canción actual en la playlist o si es la primera reproducción
        if (currentIndex === -1) {
            // Buscar si la última canción reproducida está después en la playlist
            const lastPlayedIndex = currentSongId ? 
                currentPlaylist.findIndex(song => parseInt(song.id) > parseInt(currentSongId)) : 0;
            
            // Si encontramos una canción después de la última reproducida, empezar desde ahí
            nextIndex = lastPlayedIndex !== -1 ? lastPlayedIndex : 0;
        } else {
            // Avanzar a la siguiente canción
            nextIndex = (currentIndex + 1) % currentPlaylist.length;
        }

        const nextSong = currentPlaylist[nextIndex];
        console.log('Siguiente índice:', nextIndex);
        console.log('Siguiente canción:', nextSong.name);

        // Detener la reproducción actual antes de comenzar la siguiente
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
          // Reproducir la siguiente canción
        playSong(nextSong.id, nextSong.name, nextSong.coverUrl, nextSong.artist);
    }    function playSong(songId, songName, coverUrl, artist) {
        console.log('Intentando reproducir:', songName, 'por', artist);
        currentSongId = songId;
        nowPlayingTitle.textContent = songName;
        // Solo usar 'Artista Desconocido' si no hay información del artista
        nowPlayingArtist.textContent = artist || '';
        nowPlayingCover.src = coverUrl;
        
        fetch('/api/play', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        })
        .then(response => {
            if (!response.ok) throw new Error('Error al reproducir la canción');
            return response.json();
        })
        .then(data => {
            if (data.audio_stream_url) {
                // Actualizar el título y el artista con la información de la base de datos
                if (data.title) nowPlayingTitle.textContent = data.title;
                // Priorizar el artista de la base de datos
                nowPlayingArtist.textContent = data.artist || artist || 'Artista Desconocido';
                
                audioPlayer.src = data.audio_stream_url;
                audioPlayer.currentTime = 0;
                return audioPlayer.play();
            } else if (data.fallback_url) {
                window.open(data.fallback_url, '_blank');
            }
        })
        .then(() => {
            updateFavoriteButton(songId);
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.status === 401) {
                window.location.href = '/login';
            } else {
                showAlert('Error: ' + (error.message || 'No se pudo reproducir la canción'), 'error');
            }
        });
    }    function addSong() {
        const songUrl = document.getElementById('song-url').value;
        
        if (!songUrl) {
            showAlert('Por favor ingresa la URL de la canción', 'error');
            return;
        }
        
        // Validate YouTube URL
        if (!isValidYouTubeUrl(songUrl)) {
            showAlert('Por favor ingresa una URL válida de YouTube', 'error');
            return;
        }
        
        showAlert('Procesando la canción...', 'info');
        
        fetch('/api/add_song', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                song_url: songUrl
            })
        })
        .then(response => response.json().then(data => ({
            ok: response.ok,
            status: response.status,
            data: data
        })))
        .then(({ok, status, data}) => {
            if (ok && data.success) {
                showAlert('Canción añadida correctamente!', 'success');
                document.getElementById('song-url').value = '';
                loadSongs();
            } else {
                throw new Error(data.error || 'No se pudo añadir la canción');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert(error.message || 'Error al conectar con el servidor', 'error');
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
        
        // Primero detener la reproducción si es la canción actual
        if (currentSongId === songId) {
            audioPlayer.pause();
            audioPlayer.src = '';
            nowPlayingTitle.textContent = 'No hay canción seleccionada';
            nowPlayingCover.src = 'https://via.placeholder.com/60';
            nowPlayingArtist.textContent = '';
            currentSongId = null;
            updateFavoriteButton(null);
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
                
                // Esperar un momento antes de actualizar las listas
                setTimeout(() => {
                    loadSongs();
                    // Después de cargar las canciones, cargar los favoritos
                    setTimeout(() => {
                        loadFavorites();
                        // Actualizar la playlist actual
                        setTimeout(() => {
                            updateCurrentPlaylist();
                        }, 100);
                    }, 100);
                }, 100);            } else {
                showAlert(data.error || 'No se pudo eliminar la canción', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al intentar eliminar la canción', 'error');
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
        event.stopPropagation();
        
        // Remove any existing menus
        const existingMenu = document.querySelector('.format-menu');
        if (existingMenu) {
            document.body.removeChild(existingMenu);
        }

        const menu = document.createElement('div');
        menu.className = 'format-menu';
        menu.innerHTML = `
            <div class="format-option" data-format="mp3" role="button" tabindex="0">MP3</div>
            <div class="format-option" data-format="wav" role="button" tabindex="0">WAV</div>
            <div class="format-option" data-format="ogg" role="button" tabindex="0">OGG</div>
        `;
        
        // Position the menu
        const rect = event.target.closest('.song-action-btn').getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        menu.style.position = 'fixed';
        menu.style.zIndex = '1000';
        
        // Determine if menu should appear above or below the button
        if (spaceBelow < 200 && rect.top > 200) {
            menu.style.bottom = `${window.innerHeight - rect.top}px`;
            menu.style.left = `${rect.left}px`;
        } else {
            menu.style.top = `${rect.bottom + window.scrollY}px`;
            menu.style.left = `${rect.left}px`;
        }
        
        // Add keyboard navigation
        menu.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeMenu();
            } else if (e.key === 'Enter') {
                const option = e.target.closest('.format-option');
                if (option) {
                    downloadSong(songId, option.dataset.format);
                    closeMenu();
                }
            }
        });
        
        menu.querySelectorAll('.format-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                downloadSong(songId, option.dataset.format);
                closeMenu();
            });
        });
        
        const closeMenu = () => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
            document.removeEventListener('click', closeMenu);
        };
        
        // Close menu when clicking outside
        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 0);
        
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
    }    // Audio player event listeners
    let isFirstPlay = true;
    
    audioPlayer.addEventListener('play', () => {
        console.log('Audio iniciado');
    });

    audioPlayer.addEventListener('pause', () => {
        console.log('Audio pausado');
    });

    audioPlayer.addEventListener('ended', () => {
        console.log('Canción terminada');
        // Si es la primera reproducción, actualizar la bandera
        if (isFirstPlay) {
            isFirstPlay = false;
        }
        // Asegurarnos de que la canción realmente terminó
        if (audioPlayer.currentTime >= audioPlayer.duration) {
            playNextSong();
        }
    });

    // Event listener para errores de reproducción
    audioPlayer.addEventListener('error', (e) => {
        console.error('Error en la reproducción:', e);
        showAlert('Error al reproducir la canción', 'error');
        // Si hay un error, también pasamos a la siguiente
        playNextSong();
    });
    
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function togglePlay() {
        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    }

    function updateProgress() {
        const currentTime = audioPlayer.currentTime;
        const duration = audioPlayer.duration;
        
        // Update time displays
        currentTimeEl.textContent = formatTime(currentTime);
        
        // Update progress bar
        if (duration) {
            const progressPercent = (currentTime / duration) * 100;
            progressBar.style.width = `${progressPercent}%`;
            seekSlider.value = currentTime;
        }
    }

    function seekTo() {
        const time = parseFloat(seekSlider.value);
        audioPlayer.currentTime = time;
    }

    function updateVolume() {
        const volume = volumeSlider.value / 100;
        audioPlayer.volume = volume;
        
        // Update volume icon
        if (volume === 0) {
            volumeIcon.className = 'fas fa-volume-mute';
        } else if (volume < 0.5) {
            volumeIcon.className = 'fas fa-volume-down';
        } else {
            volumeIcon.className = 'fas fa-volume-up';
        }
    }

    function toggleMute() {
        if (audioPlayer.volume > 0) {
            audioPlayer.dataset.previousVolume = audioPlayer.volume;
            audioPlayer.volume = 0;
            volumeSlider.value = 0;
            volumeIcon.className = 'fas fa-volume-mute';
        } else {
            const previousVolume = parseFloat(audioPlayer.dataset.previousVolume) || 1;
            audioPlayer.volume = previousVolume;
            volumeSlider.value = previousVolume * 100;
            volumeIcon.className = previousVolume < 0.5 ? 'fas fa-volume-down' : 'fas fa-volume-up';
        }
    }

    function playPrevSong() {
        if (audioPlayer.currentTime > 3) {
            // Si han pasado más de 3 segundos, volver al inicio de la canción actual
            audioPlayer.currentTime = 0;
            return;
        }

        if (!currentPlaylist || currentPlaylist.length === 0) {
            console.log('Lista de reproducción vacía');
            return;
        }

        // Encontrar el índice de la canción actual
        const currentIndex = currentPlaylist.findIndex(song => song.id === currentSongId);
        
        // Calcular el índice anterior
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : currentPlaylist.length - 1;
        
        const prevSong = currentPlaylist[prevIndex];
        
        // Detener la reproducción actual antes de comenzar la anterior
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
          // Reproducir la canción anterior
        playSong(prevSong.id, prevSong.name, prevSong.coverUrl, prevSong.artist);
    }
    
    // Theme-aware styles for player elements
function updatePlayerTheme() {
    const isDarkMode = document.body.classList.contains('dark-mode');
    const player = document.querySelector('.player');
    if (player) {
        player.classList.toggle('dark', isDarkMode);
    }
}

// Monitor for theme changes
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
            updatePlayerTheme();
        }
    });
});

observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
});

// Update theme on initial load
document.addEventListener('DOMContentLoaded', () => {
    updatePlayerTheme();
});
});
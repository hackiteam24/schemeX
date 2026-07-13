/* ==================== */
/* Voice Assistant JavaScript */
/* Uses the shared SpeechService / LANGUAGE_MAP / NAV_COMMANDS from main.js */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const voiceBtn = document.getElementById('voiceAssistant');
    
    if (!voiceBtn) return;
    
    if (!window.SpeechService || !SpeechService.isRecordingSupported()) {
        voiceBtn.style.display = 'none';
        console.log('Speech Recognition/Recording not supported in this browser');
        return;
    }
    
    let isListening = false;
    let voiceWave = null;
    
    // Voice wave animation
    function createVoiceWave() {
        const wave = document.createElement('div');
        wave.className = 'voice-wave';
        wave.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            display: flex;
            gap: 4px;
            align-items: center;
            z-index: 9999;
        `;
        
        for (let i = 0; i < 5; i++) {
            const bar = document.createElement('div');
            bar.className = 'voice-wave-bar';
            wave.appendChild(bar);
        }
        
        return wave;
    }
    
    // Build the recognition instance via the shared service (mocked for compatibility)
    let recognition = SpeechService.isRecordingSupported() ? SpeechService : null;
    
    // Start listening
    async function startListening() {
        if (!recognition) return;
        
        try {
            await SpeechService.startRecording();
            isListening = true;
            voiceBtn.classList.add('listening');
            voiceBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
            
            // Create and show voice wave
            voiceWave = createVoiceWave();
            document.body.appendChild(voiceWave);
        } catch (error) {
            console.error('Speech recording error:', error);
            showToast('Could not access microphone.', 'error');
            stopListening();
        }
    }
    
    // Stop listening
    async function stopListening() {
        if (!isListening) return;
        isListening = false;
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        
        // Remove voice wave
        if (voiceWave) {
            voiceWave.remove();
            voiceWave = null;
        }
        
        showToast('Transcribing audio...', 'info');
        
        try {
            const audioBlob = await SpeechService.stopRecording();
            
            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.webm');
            formData.append('language', AppState.language);
            
            const response = await API.postForm('/api/chat/speech-to-text/', formData);
            
            if (response && response.transcript) {
                processVoiceCommand(response.transcript);
            } else {
                showToast('No speech detected or empty transcription.', 'warning');
            }
        } catch (error) {
            console.error('Error stopping recognition:', error);
            showToast('Failed to transcribe audio. Please try again.', 'error');
        }
    }
    
    // Process voice command
    async function processVoiceCommand(transcript) {
        showToast(`Heard: "${transcript}"`, 'info');
        
        const route = matchVoiceCommand(transcript);
        
        if (route) {
            window.location.href = route;
            return;
        }
        
        // No local nav match — send to backend for AI-driven handling
        try {
            const response = await API.post('/api/voice-command/', {
                command: transcript,
                language: AppState.language
            });
            
            if (response.action) {
                showToast(response.message, 'success');
                
                if (response.redirect) {
                    setTimeout(() => {
                        window.location.href = response.redirect;
                    }, 1500);
                }
            }
        } catch (error) {
            showToast('Could not process voice command. Please try again.', 'error');
        }
    }
    
    // Toggle voice assistant
    voiceBtn.addEventListener('click', () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    });
    
    // Keep recognition language synced with app language changes
    document.addEventListener('languagechange', () => {
        SpeechService.syncLang(recognition);
    });
    
    // Add voice button styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .voice-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary-green), var(--primary-light));
            color: var(--white);
            border: none;
            cursor: pointer;
            box-shadow: var(--shadow-xl);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            transition: all var(--transition-normal);
        }
        
        .voice-btn:hover {
            transform: scale(1.1);
            box-shadow: var(--shadow-2xl);
        }
        
        .voice-btn.listening {
            animation: pulse 1s ease-in-out infinite;
            background: linear-gradient(135deg, var(--saffron), var(--saffron-dark));
        }
        
        @media (max-width: 640px) {
            .voice-btn {
                bottom: 20px;
                right: 20px;
                width: 50px;
                height: 50px;
                font-size: 1.25rem;
            }
        }
    `;
    document.head.appendChild(style);
});

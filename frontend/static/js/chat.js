/* ==================== */
/* Chat Assistant JavaScript */
/* Uses the shared SpeechService from main.js for voice input */
/* ==================== */

document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const chatMessages = document.getElementById('chatMessages');
    const voiceIndicator = document.getElementById('voiceIndicator');
    
    let isListening = false;
    let currentChatId = null;
    
    // Build recognition instance via the shared service (mocked for compatibility)
    const recognition = window.SpeechService && SpeechService.isRecordingSupported() ? SpeechService : null;
    
    // Send message
    // Send message
    let isSending = false;

    window.sendMessage = async function() {
        if (isSending) return;

        const message = chatInput.value.trim();
        
        if (!message) return;

        isSending = true;
        sendBtn.disabled = true;
        chatInput.disabled = true;
        
        // Add user message
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send to API
            const response = await API.post('/api/chat/', {
                message: message,
                chat_id: currentChatId,
                language: AppState.language
            });
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add AI response
            addMessage(response.response, 'ai');
            
            // Update chat ID
            currentChatId = response.chat_id;
            
        } catch (error) {
            removeTypingIndicator();
            addMessage('I apologize, but I encountered an error. Please try again.', 'ai');
        } finally {
            isSending = false;
            sendBtn.disabled = false;
            chatInput.disabled = false;
            chatInput.focus();
        }
    };
    
    // Add message to chat
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message slide-up`;
        
        const avatarIcon = type === 'ai' ? 'fa-robot' : 'fa-user';
        
        const renderedContent = type === 'ai' && window.marked
            ? marked.parse(content)
            : `<p>${content}</p>`;

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                ${renderedContent}
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai-message typing-message';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-typing">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Toggle voice input
    window.toggleVoiceInput = function() {
        if (!recognition) {
            showToast('Voice input not supported in this browser', 'error');
            return;
        }
        
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    };
    
    // Start listening
    async function startListening() {
        try {
            await SpeechService.startRecording();
            isListening = true;
            voiceBtn.classList.add('listening');
            voiceIndicator.style.display = 'flex';
        } catch (error) {
            console.error('Error starting audio recording:', error);
            showToast('Could not access microphone.', 'error');
            stopListening();
        }
    }
    
    // Stop listening
    async function stopListening() {
        if (!isListening) return;
        isListening = false;
        voiceBtn.classList.remove('listening');
        voiceIndicator.style.display = 'none';

        showToast('Transcribing audio...', 'info');

        try {
            const audioBlob = await SpeechService.stopRecording();

            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.webm');
            formData.append('language', AppState.language);

            const response = await API.postForm('/api/chat/speech-to-text/', formData);

            if (response && response.transcript) {
                chatInput.value = response.transcript;
                sendMessage();
            } else {
                showToast('No speech detected or empty transcription.', 'warning');
            }
        } catch (error) {
            console.error('Transcription error:', error);
            showToast('Failed to transcribe audio. Please try again.', 'error');
        }
    }
    
    // Send message on Enter key
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Ask suggested question
    window.askSuggested = function(question) {
        chatInput.value = question;
        sendMessage();
    };
    
    // Start new chat
    window.startNewChat = function() {
        currentChatId = null;
        
        // Clear messages except welcome
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach(msg => {
            if (!msg.querySelector('.message-content ul')) {
                msg.remove();
            }
        });
        
        showToast('New chat started', 'success');
    };
    
    // Clear chat
    window.clearChat = function() {
        if (confirm('Are you sure you want to clear this chat?')) {
            startNewChat();
        }
    };
    
    // Toggle voice mode
    window.toggleVoice = function() {
        toggleVoiceInput();
    };
    
    // Load chat history
    async function loadChatHistory() {
        try {
            const response = await API.get('/api/chat/history/');
            
            if (response.chats && response.chats.length > 0) {
                const historyContainer = document.getElementById('chatHistory');
                
                // Clear existing history except first item
                const historyItems = historyContainer.querySelectorAll('.history-item');
                historyItems.forEach((item, index) => {
                    if (index > 0) item.remove();
                });
                
                // Add history items
                response.chats.forEach(chat => {
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    historyItem.innerHTML = `
                        <div class="history-icon">
                            <i class="fa-solid fa-message"></i>
                        </div>
                        <div class="history-content">
                            <h4>${chat.title}</h4>
                            <p>${chat.preview}</p>
                        </div>
                    `;
                    historyItem.addEventListener('click', () => loadChat(chat.id));
                    historyContainer.appendChild(historyItem);
                });
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }
    
    // Load specific chat
    async function loadChat(chatId) {
        try {
            const response = await API.get(`/api/chat/${chatId}/`);
            
            currentChatId = chatId;
            
            // Clear messages
            const messages = chatMessages.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
            
            // Add chat messages
            response.messages.forEach(msg => {
                addMessage(msg.content, msg.sender);
            });
            
            // Update active state
            const historyItems = document.querySelectorAll('.history-item');
            historyItems.forEach(item => item.classList.remove('active'));
            
        } catch (error) {
            console.error('Failed to load chat:', error);
            showToast('Failed to load chat', 'error');
        }
    }
    
    // Keep recognition language synced with app language changes
    document.addEventListener('languagechange', () => {
        SpeechService.syncLang(recognition);
    });
    
    // Initialize
    loadChatHistory();
    
    // Focus input on load
    chatInput.focus();
});

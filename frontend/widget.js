document.addEventListener('DOMContentLoaded', () => {
    const launcher = document.getElementById('chat-widget-launcher');
    const window = document.getElementById('chat-widget-window');
    const closeBtn = document.getElementById('chat-widget-close');
    const sendBtn = document.getElementById('chat-widget-send');
    const input = document.getElementById('chat-widget-input');
    const messagesContainer = document.getElementById('chat-widget-messages');
    const typingIndicator = document.querySelector('.typing');

    const API_URL = 'http://localhost:8000/api/chat';

    // Alternar visibilidade da janela
    launcher.addEventListener('click', () => {
        window.style.display = window.style.display === 'flex' ? 'none' : 'flex';
        if (window.style.display === 'flex') {
            input.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        window.style.display = 'none';
    });

    // Enviar mensagem
    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        // Adicionar mensagem do usuário na tela
        appendMessage(text, 'user');
        input.value = '';

        // Mostrar indicador de digitando
        typingIndicator.style.display = 'block';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        sendBtn.disabled = true;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) throw new Error('Erro na comunicação com o servidor');

            const data = await response.json();
            appendMessage(data.response, 'bot');
        } catch (error) {
            console.error(error);
            appendMessage('Desculpe, ocorreu um erro ao processar sua mensagem.', 'bot');
        } finally {
            typingIndicator.style.display = 'none';
            sendBtn.disabled = false;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    };

    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        msgDiv.textContent = text;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Mensagem de boas-vindas inicial
    setTimeout(() => {
        appendMessage('Olá! Sou o assistente da instituição. Como posso ajudar você hoje?', 'bot');
    }, 500);
});

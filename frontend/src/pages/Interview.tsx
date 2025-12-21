import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReactMediaRecorder } from 'react-media-recorder';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, ArrowLeft, Loader2, Volume2, Bot } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
}

export const Interview = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Скролл вниз при новом сообщении
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Функция обработки окончания записи
  const handleStop = async (_blobUrl: string, blob: Blob) => {
    if (!blob) return;
    
    setIsProcessing(true);
    
    const formData = new FormData();
    formData.append('file', blob, 'voice.wav'); 

    try {
      // Используем относительный путь для Nginx
      const response = await fetch('/api/interview/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Ошибка сети');

      const data = await response.json();

      setMessages(prev => [
        ...prev, 
        { role: 'user', text: data.user_text || "..." },
        { role: 'ai', text: data.ai_text }
      ]);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audio.play().catch(e => console.log("Auto-play blocked:", e));
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'ai', text: "Ошибка связи с сервером. Попробуй еще раз." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Хук записи звука
  const { status, startRecording, stopRecording } = useReactMediaRecorder({ 
    audio: true,
    onStop: handleStop
  });

  const isRecording = status === 'recording';

  // Логика переключения (Нажал -> Старт / Нажал -> Стоп)
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-bg text-text">
      {/* Шапка */}
      <div className="flex items-center p-4 border-b border-hint/10 bg-secondaryBg/50 backdrop-blur-md sticky top-0 z-10">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-hint hover:text-text">
          <ArrowLeft size={24} />
        </button>
        <div className="ml-2">
          <h1 className="font-bold text-lg">AI Interviewer</h1>
          <p className="text-xs text-hint">Нажми для записи</p>
        </div>
      </div>

      {/* Область чата */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-hint mt-10 opacity-60">
            <Bot size={48} className="mx-auto mb-4" />
            <p>Нажми на кнопку,<br/>чтобы начать говорить.</p>
            <p className="text-xs mt-2">(Повторное нажатие отправит сообщение)</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div 
              className={`
                max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed shadow-sm
                ${msg.role === 'user' 
                  ? 'bg-blue-500 text-white rounded-br-none' 
                  : 'bg-secondaryBg text-text rounded-bl-none'}
              `}
            >
              {msg.role === 'ai' && <Volume2 size={14} className="mb-1 opacity-50" />}
              {msg.text}
            </div>
          </div>
        ))}

        {/* Индикатор обработки */}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-secondaryBg p-3 rounded-2xl rounded-bl-none flex items-center space-x-2">
              <Loader2 size={16} className="animate-spin text-hint" />
              <span className="text-xs text-hint">Анализирую ответ...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Подвал с кнопкой */}
      <div className="p-6 pb-8 flex justify-center bg-gradient-to-t from-bg via-bg to-transparent">
        <button
          onClick={toggleRecording} // Теперь просто клик
          className="relative group outline-none select-none"
          disabled={isProcessing}
        >
          {/* Анимация пульсации */}
          <AnimatePresence>
            {isRecording && (
              <motion.div
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 1.6, opacity: 0 }}
                exit={{ scale: 1, opacity: 0 }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="absolute inset-0 bg-red-500 rounded-full"
              />
            )}
          </AnimatePresence>

          {/* Сама кнопка */}
          <div 
            className={`
              relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-xl transition-all duration-200
              ${isRecording ? 'bg-red-500 scale-110' : 'bg-button hover:bg-blue-600'}
              ${isProcessing ? 'opacity-50 cursor-not-allowed grayscale' : ''}
            `}
          >
            {/* Меняем иконку: Микрофон или Стоп (Квадрат) */}
            {isRecording ? (
                <Square size={28} className="text-white fill-current" />
            ) : (
                <Mic size={32} className="text-white" />
            )}
          </div>
        </button>
      </div>
    </div>
  );
};
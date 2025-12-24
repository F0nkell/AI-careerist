import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReactMediaRecorder } from 'react-media-recorder';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, ArrowLeft, Loader2, Volume2, Bot, Paperclip, Image as ImageIcon, X } from 'lucide-react';


interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  image?: string;
}

export const Interview = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Новые состояния для картинок
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Скролл вниз при новом сообщении или появлении превью
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing, imagePreview]);

  // Обработка выбора картинки через input
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  // Очистка выбранной картинки
  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Функция обработки окончания записи
  const handleStop = async (_blobUrl: string, blob: Blob) => {
    if (!blob) return;
    
    setIsProcessing(true);
    
    const formData = new FormData();
    formData.append('file', blob, 'voice.wav');
    
    // --- КАРТИНКА: Добавляем, если есть ---
    if (selectedImage) {
      formData.append('image', selectedImage);
    }

    // --- ПАМЯТЬ: Формируем историю ---
    const historyPayload = messages.slice(-10).map(msg => ({
      role: msg.role === 'ai' ? 'assistant' : 'user',
      content: msg.text
    }));
    formData.append('history', JSON.stringify(historyPayload));

    try {
      const response = await fetch('/api/interview/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Ошибка сети');

      const data = await response.json();

      // Добавляем сообщения в чат (включая картинку пользователя, если была)
      setMessages(prev => [
        ...prev, 
        { 
          role: 'user', 
          text: data.user_text || "...", 
          image: imagePreview || undefined // Сохраняем превью в истории
        },
        { role: 'ai', text: data.ai_text }
      ]);

      // Воспроизводим аудио
      if (data.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audio.play().catch(e => console.log("Auto-play blocked:", e));
      }

      // Сбрасываем картинку после успешной отправки
      clearImage();

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'ai', text: "Ошибка связи. Попробуй еще раз." }]);
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
          <p className="text-xs text-hint">Vision + Voice</p>
        </div>
      </div>

      {/* Область чата */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-hint mt-10 opacity-60">
            <Bot size={48} className="mx-auto mb-4" />
            <p>Нажми на кнопку,<br/>чтобы начать говорить.</p>
            <p className="text-xs mt-2">Можно прикрепить скриншот кода или задачи</p>
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
              {/* Отображение картинки в сообщении */}
              {msg.image && (
                <img 
                  src={msg.image} 
                  alt="User upload" 
                  className="mb-2 rounded-lg max-h-40 w-full object-cover border border-white/20"
                />
              )}
              
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
              <span className="text-xs text-hint">Смотрю и слушаю...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Превью картинки перед отправкой (Всплывает над футером) */}
      <AnimatePresence>
        {imagePreview && (
          <motion.div 
            initial={{ y: 50, opacity: 0 }} 
            animate={{ y: 0, opacity: 1 }} 
            exit={{ y: 50, opacity: 0 }} 
            className="px-6 pb-2"
          >
            <div className="relative inline-block">
              <img src={imagePreview} alt="Preview" className="h-20 rounded-xl border-2 border-blue-500 shadow-lg" />
              <button 
                onClick={clearImage} 
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow-md hover:bg-red-600"
              >
                <X size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Подвал с кнопками */}
      <div className="p-6 pb-8 flex justify-center items-center gap-6 bg-gradient-to-t from-bg via-bg to-transparent">
        
        {/* Кнопка скрепки (Слева) */}
        <button 
          onClick={() => fileInputRef.current?.click()}
          className="p-3 bg-secondaryBg rounded-full text-hint hover:text-blue-500 transition-colors shadow-sm active:scale-95"
          disabled={isProcessing || isRecording}
        >
          <Paperclip size={24} />
        </button>
        {/* Скрытый инпут для файла */}
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleImageSelect} 
          accept="image/*" 
          className="hidden" 
        />

        {/* Кнопка записи (Центр) */}
        <button
          onClick={toggleRecording}
          className="relative group outline-none select-none"
          disabled={isProcessing}
        >
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

          <div 
            className={`
              relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-xl transition-all duration-200
              ${isRecording ? 'bg-red-500 scale-110' : 'bg-button hover:bg-blue-600'}
              ${isProcessing ? 'opacity-50 cursor-not-allowed grayscale' : ''}
            `}
          >
            {isRecording ? (
                <Square size={28} className="text-white fill-current" />
            ) : (
                <Mic size={32} className="text-white" />
            )}
          </div>
        </button>
        
        {/* Пустышка справа для симметрии (чтобы кнопка записи была по центру) */}
        <div className="w-12 h-12" /> 
      </div>
    </div>
  );
};
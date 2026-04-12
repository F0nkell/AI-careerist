import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ArrowLeft, Sun, Moon } from 'lucide-react';

// Тип данных, которые возвращает наш Бэкенд
interface UploadResponse {
  filename: string;
  size_kb: number;
  message: string;
  ai_response?: string;
}

const Typewriter = ({ text, speed = 15 }: { text: string; speed?: number }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let index = 0;
    let currentText = '';
    const timer = setInterval(() => {
      if (index < text.length) {
        currentText += text.charAt(index);
        setDisplayedText(currentText);
        index++;
      } else {
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed]);

  return <div className="whitespace-pre-wrap text-sm leading-relaxed">{displayedText}</div>;
};

export const Resume = () => {
  const navigate = useNavigate();
  
  // Состояния интерфейса
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');
  
  const [isThemeDark, setIsThemeDark] = useState(false);

  useEffect(() => {
    // Пытаемся взять тему из Telegram с фоллбеком на светлую
    const tgTheme = (window as any).Telegram?.WebApp?.colorScheme;
    if (tgTheme === 'dark') {
      setIsThemeDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    setIsThemeDark(!isThemeDark);
    if (!isThemeDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Обработка выбора файла
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setErrorMsg('');
    }
  };

  // Отправка файла на сервер
  const handleUpload = async () => {
    if (!file) return;

    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/resume/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Ошибка загрузки');
      }

      const data: UploadResponse = await response.json();
      setResult(data);
      setStatus('success');
    } catch (e) {
      console.error(e);
      setStatus('error');
      setErrorMsg('Не удалось загрузить файл. Убедитесь, что сервер запущен.');
    }
  };

  return (
    <div className="min-h-screen bg-bg text-text p-4 flex flex-col font-sans">
      {/* Шапка */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-hint/15">
        <div className="flex items-center">
          <button 
            onClick={() => navigate(-1)} 
            className="p-2 -ml-2 text-hint hover:text-gold-500 transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <div className="ml-2">
            <h1 className="text-2xl font-black tracking-tight text-text">F0nKrit</h1>
            <p className="text-[10px] font-bold text-gold-500 uppercase tracking-widest mt-0.5">Resume Review</p>
          </div>
        </div>
        <button 
          onClick={toggleTheme} 
          className="p-2 rounded-full bg-secondaryBg text-text hover:text-gold-500 transition-all shadow-sm active:scale-95"
        >
          {isThemeDark ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center space-y-6">
        
        {/* Блок: Выбор файла */}
        {status !== 'success' && (
          <div className="w-full max-w-lg">
            <label 
              className={`
                flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-3xl cursor-pointer transition-all duration-300
                ${file ? 'border-gold-500 bg-gold-500/5 shadow-[0_0_20px_rgba(234,145,15,0.1)]' : 'border-hint/30 hover:border-gold-400 hover:bg-secondaryBg'}
              `}
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {file ? (
                  <>
                    <FileText size={48} className="text-gold-500 mb-3 drop-shadow-md" />
                    <p className="text-sm font-bold text-text truncate max-w-[200px]">{file.name}</p>
                    <p className="text-xs text-hint mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                  </>
                ) : (
                  <>
                    <Upload size={40} className="text-hint mb-3 transition-transform group-hover:-translate-y-1" />
                    <p className="text-sm text-hint font-medium">Нажми, чтобы выбрать PDF</p>
                  </>
                )}
              </div>
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
            </label>
          </div>
        )}

        {/* Блок: Ошибки */}
        {status === 'error' && (
          <div className="flex items-center space-x-2 text-red-500 bg-red-500/10 p-4 rounded-xl max-w-lg w-full">
            <AlertCircle size={20} />
            <span className="text-sm font-medium">{errorMsg}</span>
          </div>
        )}

        {/* Блок: Успех */}
        {status === 'success' && result && (
          <div className="w-full max-w-lg bg-secondaryBg p-6 sm:p-8 rounded-[2rem] text-center space-y-4 animate-in fade-in zoom-in duration-500 shadow-xl shadow-black/5">
            <div className="mx-auto w-16 h-16 bg-gradient-to-tr from-gold-600 to-gold-400 rounded-2xl rotate-3 flex items-center justify-center text-white shadow-xl shadow-gold-500/30 mb-6 transition-transform hover:rotate-6">
              <CheckCircle size={32} className="-rotate-3" />
            </div>
            <div>
              <h3 className="text-xl font-black text-text">Анализ завершен</h3>
            </div>
            
            {result.ai_response && (
              <div className="bg-bg text-left p-5 sm:p-6 rounded-2xl shadow-inner border border-black/5 dark:border-white/5 mt-4 relative">
                <div className="flex items-center mb-4 border-b border-hint/15 pb-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center text-gold-400 font-bold mr-3 shadow-md border border-gray-700">SR</div>
                  <div>
                    <p className="text-sm font-bold text-text">Senior Developer</p>
                    <p className="text-[10px] text-hint uppercase tracking-wider font-semibold">AI Feedback</p>
                  </div>
                </div>
                <div className="text-text font-medium text-[15px]">
                  <Typewriter text={result.ai_response} speed={10} />
                </div>
              </div>
            )}
            
            {!result.ai_response && (
              <div className="bg-bg p-4 rounded-xl text-sm text-left border border-hint/10">
                <p className="truncate">📄 <b className="font-semibold">Файл:</b> {result.filename}</p>
                <p>⚖️ <b className="font-semibold">Размер:</b> {result.size_kb} KB</p>
              </div>
            )}

            <button 
              onClick={() => { setStatus('idle'); setFile(null); }}
              className="w-full py-4 bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-2xl font-bold active:scale-95 transition-all mt-6 shadow-lg hover:shadow-xl dark:from-white dark:to-gray-200 dark:text-black"
            >
              Скормить другое резюме
            </button>
          </div>
        )}

        {/* Кнопка действия */}
        {status !== 'success' && (
          <button
            onClick={handleUpload}
            disabled={!file || status === 'uploading'}
            className={`
              w-full max-w-lg py-4 rounded-2xl font-bold text-lg transition-all duration-300
              flex items-center justify-center space-x-2
              ${!file || status === 'uploading' 
                ? 'bg-secondaryBg text-hint cursor-not-allowed border border-transparent' 
                : 'bg-gradient-to-r from-gold-500 to-gold-400 text-white shadow-[0_10px_30px_-10px_rgba(234,145,15,0.6)] hover:shadow-[0_15px_40px_-10px_rgba(234,145,15,0.8)] active:scale-95'}
            `}
          >
            {status === 'uploading' ? (
              <>
                <Loader2 size={24} className="animate-spin text-white" />
                <span className="text-white">Думаю...</span>
              </>
            ) : (
              <span>Разобрать резюме</span>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
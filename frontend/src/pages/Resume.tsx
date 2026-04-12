import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';

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

  return <div className="whitespace-pre-wrap text-left text-sm leading-relaxed">{displayedText}</div>;
};

export const Resume = () => {
  const navigate = useNavigate();
  
  // Состояния интерфейса
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');

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
      // Важно: стучимся на localhost, поэтому тестируй с ПК
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
    <div className="min-h-screen bg-bg text-text p-4 flex flex-col">
      {/* Шапка */}
      <div className="flex items-center mb-6">
        <button 
          onClick={() => navigate(-1)} 
          className="p-2 -ml-2 text-hint hover:text-text transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-xl font-bold ml-2">Resume Killer</h1>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center space-y-6">
        
        {/* Блок: Выбор файла (показываем, если еще не загрузили успешно) */}
        {status !== 'success' && (
          <div className="w-full max-w-sm">
            <label 
              className={`
                flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-2xl cursor-pointer transition-colors
                ${file ? 'border-blue-500 bg-blue-50/10' : 'border-hint/30 hover:border-blue-400 hover:bg-secondaryBg'}
              `}
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {file ? (
                  <>
                    <FileText size={48} className="text-blue-500 mb-3" />
                    <p className="text-sm font-medium text-text">{file.name}</p>
                    <p className="text-xs text-hint">{(file.size / 1024).toFixed(1)} KB</p>
                  </>
                ) : (
                  <>
                    <Upload size={40} className="text-hint mb-3" />
                    <p className="text-sm text-hint">Нажми, чтобы выбрать PDF</p>
                  </>
                )}
              </div>
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
            </label>
          </div>
        )}

        {/* Блок: Ошибки */}
        {status === 'error' && (
          <div className="flex items-center space-x-2 text-red-500 bg-red-100/10 p-3 rounded-lg">
            <AlertCircle size={20} />
            <span className="text-sm">{errorMsg}</span>
          </div>
        )}

        {/* Блок: Успех */}
        {status === 'success' && result && (
          <div className="w-full max-w-lg bg-secondaryBg p-6 rounded-2xl text-center space-y-4 animate-in fade-in zoom-in duration-300">
            <div className="mx-auto w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <CheckCircle size={32} />
            </div>
            <div>
              <h3 className="text-lg font-bold">Анализ завершен</h3>
            </div>
            
            {result.ai_response && (
              <div className="bg-bg p-4 rounded-xl border border-hint/10 shadow-inner mt-4 relative">
                <p className="text-xs text-hint mb-2 text-left font-mono border-b border-hint/10 pb-2">>_ Senior_Review.log</p>
                <div className="font-mono text-text">
                  <Typewriter text={result.ai_response} speed={10} />
                </div>
              </div>
            )}
            
            {!result.ai_response && (
              <div className="bg-bg p-3 rounded-lg text-sm text-left border border-hint/10">
                <p>📄 <b>Файл:</b> {result.filename}</p>
                <p>⚖️ <b>Размер:</b> {result.size_kb} KB</p>
              </div>
            )}

            <button 
              onClick={() => { setStatus('idle'); setFile(null); }}
              className="w-full py-3 bg-button text-buttonText rounded-xl font-semibold active:scale-95 transition-transform mt-4"
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
              w-full max-w-sm py-4 rounded-xl font-bold text-lg shadow-lg transition-all
              flex items-center justify-center space-x-2
              ${!file || status === 'uploading' 
                ? 'bg-secondaryBg text-hint cursor-not-allowed' 
                : 'bg-button text-buttonText active:scale-95 shadow-blue-500/20'}
            `}
          >
            {status === 'uploading' ? (
              <>
                <Loader2 size={24} className="animate-spin" />
                <span>Думаю...</span>
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
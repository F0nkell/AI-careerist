import WebApp from '@twa-dev/sdk';
import { useNavigate } from 'react-router-dom';
import { FileText, Mic } from 'lucide-react';

export const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 space-y-6 bg-bg text-text">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold">Career Killer AI 🚀</h1>
        <p className="text-hint">
          Привет! Выбери инструмент для прокачки.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 w-full max-w-xs">
        <button
          onClick={() => navigate('/resume')}
          className="flex items-center p-4 bg-secondaryBg rounded-xl space-x-4 active:scale-95 transition-transform"
        >
          <div className="bg-blue-500 p-2 rounded-lg text-white">
            <FileText size={24} />
          </div>
          <div className="text-left">
            <h3 className="font-semibold">Resume Killer</h3>
            <p className="text-xs text-hint">Улучши резюме с GPT-4</p>
          </div>
        </button>

        <button
          onClick={() => navigate('/interview')}
          className="flex items-center p-4 bg-secondaryBg rounded-xl space-x-4 active:scale-95 transition-transform"
        >
          <div className="bg-green-500 p-2 rounded-lg text-white">
            <Mic size={24} />
          </div>
          <div className="text-left">
            <h3 className="font-semibold">Mock Interview</h3>
            <p className="text-xs text-hint">Тренировка голосом</p>
          </div>
        </button>
      </div>
    </div>
  );
};
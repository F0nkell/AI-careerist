import WebApp from '@twa-dev/sdk';
import { useNavigate } from 'react-router-dom';
import { FileText, Mic } from 'lucide-react';

export const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 space-y-8 bg-bg text-text font-sans">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-black tracking-tighter">F0nKrit</h1>
        <p className="text-sm font-semibold text-gold-500 uppercase tracking-widest mt-1">
          Review & Prep
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 w-full max-w-xs">
        <button
          onClick={() => navigate('/resume')}
          className="flex items-center p-5 bg-secondaryBg rounded-2xl space-x-4 active:scale-95 transition-all hover:shadow-lg hover:shadow-gold-500/10 border border-transparent hover:border-gold-500/20"
        >
          <div className="bg-gradient-to-tr from-gold-600 to-gold-400 p-3 rounded-xl text-white shadow-md shadow-gold-500/30">
            <FileText size={24} />
          </div>
          <div className="text-left">
            <h3 className="font-bold text-lg">Resume Review</h3>
            <p className="text-xs text-hint mt-0.5">Улучши резюме с ИИ</p>
          </div>
        </button>

        <button
          onClick={() => navigate('/interview')}
          className="flex items-center p-5 bg-secondaryBg rounded-2xl space-x-4 active:scale-95 transition-all hover:shadow-lg hover:shadow-gold-500/10 border border-transparent hover:border-gold-500/20"
        >
          <div className="bg-gradient-to-tr from-gray-800 to-gray-900 dark:from-gray-200 dark:to-white p-3 rounded-xl text-gold-400 dark:text-gray-900 shadow-md">
            <Mic size={24} />
          </div>
          <div className="text-left">
            <h3 className="font-bold text-lg">Mock Interview</h3>
            <p className="text-xs text-hint mt-0.5">Тренировка голосом</p>
          </div>
        </button>
      </div>
    </div>
  );
};
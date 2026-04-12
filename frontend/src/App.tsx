import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';

import { Home } from './pages/Home';
import { Resume } from './pages/Resume';
import { Interview } from './pages/Interview';

function App() {
  useEffect(() => {
    try {
        WebApp.ready();
        WebApp.expand();
        // Принудительно устанавливаем первоначальную тему из Telegram
        const tgTheme = WebApp.colorScheme;
        if (tgTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
    } catch (e) {
        console.log("Not in Telegram environment");
        // Fallback for browser (check system preference)
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
          document.documentElement.classList.add('dark');
        }
    }
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/resume" element={<Resume />} />
        <Route path="/interview" element={<Interview />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
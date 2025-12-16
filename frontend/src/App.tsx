import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';

import { Home } from './pages/Home';
import { Resume } from './pages/Resume';
import { Interview } from './pages/Interview';

function App() {
  useEffect(() => {
    // Инициализация Telegram Web App
    // Оборачиваем в try/catch, чтобы не падало в обычном браузере
    try {
        WebApp.ready();
        WebApp.expand();
    } catch (e) {
        console.log("Not in Telegram environment");
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
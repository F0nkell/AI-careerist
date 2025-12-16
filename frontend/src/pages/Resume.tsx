import { useNavigate } from 'react-router-dom';

export const Resume = () => {
  const navigate = useNavigate();
  return (
    <div className="p-4 min-h-screen bg-bg text-text">
      <button onClick={() => navigate(-1)} className="text-link mb-4">← Назад</button>
      <h1 className="text-xl font-bold">Resume Parsing</h1>
      <p className="text-hint mt-2">Здесь будет загрузка PDF.</p>
    </div>
  );
};
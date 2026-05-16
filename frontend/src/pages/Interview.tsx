import { useState } from 'react';
import type { ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReactMediaRecorder } from 'react-media-recorder';
import {
  ArrowLeft,
  Bot,
  Briefcase,
  Code2,
  Loader2,
  Mic,
  RotateCcw,
  Square,
  UserRound,
} from 'lucide-react';

type SessionStatus = 'active' | 'completed';
type ConversationRole = 'interviewer' | 'candidate';

interface InterviewQuestion {
  id: number;
  profession: string;
  language: string | null;
  competency: string;
  level: string;
  difficulty: number;
  question_text: string;
  answer_time_limit_sec: number;
}

interface InterviewEvaluation {
  on_topic: boolean;
  coverage_percent: number;
  covered_points: string[];
  missing_points: string[];
  red_flags_seen: string[];
  should_redirect: boolean;
  redirect_message: string;
  should_follow_up: boolean;
  follow_up_question: string;
  final_feedback_to_user: string;
  score_reason: string;
  competency?: string;
}

interface AudioMetrics {
  duration_sec: number;
  silence_ratio: number;
  pause_count: number;
  longest_pause_sec: number;
  average_dbfs: number;
  is_too_quiet: boolean;
  approximate_words_per_minute: number;
  filler_words: number;
}

interface AnswerRecord {
  question_id: number;
  competency: string;
  level: string;
  difficulty: number;
  transcript: string;
  audio_metrics: AudioMetrics;
  evaluation: InterviewEvaluation;
  redirect_attempt: number;
}

interface InterviewSession {
  session_id: string;
  profession: string;
  language: string | null;
  selected_question_ids: number[];
  current_question_index: number;
  current_question: InterviewQuestion | null;
  redirect_attempts: number;
  answers: AnswerRecord[];
  evaluations: InterviewEvaluation[];
  status: SessionStatus;
}

interface FinalReport {
  estimated_level?: string;
  total_score?: number;
  per_topic_scores?: Record<string, number>;
  strengths?: string[];
  weak_topics?: string[];
  missing_topics?: string[];
  recommended_study_plan?: string[];
}

interface AnswerResponse {
  session: InterviewSession;
  transcript: string;
  audio_metrics: AudioMetrics;
  question_evaluation: InterviewEvaluation;
  interviewer_message: string;
  next_question: InterviewQuestion | null;
  completed_report: FinalReport | null;
  audio_base64?: string;
}

interface ConversationMessage {
  id: string;
  role: ConversationRole;
  text: string;
  meta?: string;
}

const API_BASE = '/api';

const nextMessageId = () => `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const questionMeta = (question: InterviewQuestion, index: number, total: number) =>
  `Вопрос ${index}/${total} - ${question.competency} - ${question.level} - difficulty ${question.difficulty}`;

const formatPercent = (value: number | undefined) => `${Math.round(value ?? 0)}%`;

export const Interview = () => {
  const navigate = useNavigate();
  const [profession, setProfession] = useState('backend');
  const [language, setLanguage] = useState('python');
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const startInterview = async () => {
    setIsStarting(true);
    setError('');
    setFinalReport(null);
    setMessages([]);

    try {
      const response = await fetch(`${API_BASE}/interview/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profession: profession.trim().toLowerCase(),
          language: language.trim().toLowerCase(),
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'Не удалось начать интервью');
      }

      const data = (await response.json()) as InterviewSession;
      setSession(data);

      if (data.current_question) {
        setMessages([
          {
            id: nextMessageId(),
            role: 'interviewer',
            text: data.current_question.question_text,
            meta: questionMeta(data.current_question, 1, data.selected_question_ids.length),
          },
        ]);
      }
    } catch (err) {
      setSession(null);
      setError(err instanceof Error ? err.message : 'Не удалось начать интервью');
    } finally {
      setIsStarting(false);
    }
  };

  const appendAnswerResult = (data: AnswerResponse) => {
    const nextMessages: ConversationMessage[] = [
      {
        id: nextMessageId(),
        role: 'candidate',
        text: data.transcript || '...',
        meta: 'Ответ кандидата',
      },
      {
        id: nextMessageId(),
        role: 'interviewer',
        text: data.interviewer_message || data.question_evaluation.final_feedback_to_user || 'Принял.',
        meta: data.question_evaluation.should_redirect ? 'Возвращаемся к вопросу' : 'Комментарий интервьюера',
      },
    ];

    if (data.next_question && !data.question_evaluation.should_redirect) {
      nextMessages.push({
        id: nextMessageId(),
        role: 'interviewer',
        text: data.next_question.question_text,
        meta: questionMeta(
          data.next_question,
          data.session.current_question_index + 1,
          data.session.selected_question_ids.length,
        ),
      });
    }

    if (data.completed_report) {
      nextMessages.push({
        id: nextMessageId(),
        role: 'interviewer',
        text: 'Собеседование завершено. Ниже собрал итоговую выжимку по уровню, сильным сторонам и темам, которые стоит подтянуть.',
        meta: 'Финал',
      });
    }

    setMessages((current) => [...current, ...nextMessages]);
  };

  const handleStop = async (_blobUrl: string, blob: Blob) => {
    if (!blob || !session || session.status !== 'active') return;

    setIsProcessing(true);
    setError('');

    const formData = new FormData();
    formData.append('session', JSON.stringify(session));
    formData.append('file', blob, 'answer.webm');

    try {
      const response = await fetch(`${API_BASE}/interview/session/answer`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'Не удалось обработать ответ');
      }

      const data = (await response.json()) as AnswerResponse;
      setSession(data.session);
      setFinalReport(data.completed_report);
      appendAnswerResult(data);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audio.play().catch(() => undefined);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обработать ответ');
    } finally {
      setIsProcessing(false);
    }
  };

  const { status, startRecording, stopRecording } = useReactMediaRecorder({
    audio: true,
    onStop: handleStop,
  });

  const isRecording = status === 'recording';
  const currentQuestion = session?.current_question;
  const totalQuestions = session?.selected_question_ids.length ?? 7;
  const currentQuestionNumber = session
    ? Math.min(session.current_question_index + 1, totalQuestions)
    : 1;
  const canRecord = Boolean(session && session.status === 'active' && !isProcessing && !isStarting);

  const toggleRecording = () => {
    if (!canRecord && !isRecording) return;
    if (isRecording) {
      stopRecording();
      return;
    }
    startRecording();
  };

  const handleProfessionChange = (event: ChangeEvent<HTMLInputElement>) => {
    setProfession(event.target.value);
  };

  const handleLanguageChange = (event: ChangeEvent<HTMLInputElement>) => {
    setLanguage(event.target.value);
  };

  return (
    <div className="min-h-screen bg-bg text-text">
      <header className="sticky top-0 z-10 border-b border-hint/10 bg-bg/90 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-lg p-2 text-hint transition-colors hover:bg-secondaryBg hover:text-text"
            aria-label="Назад"
          >
            <ArrowLeft size={22} />
          </button>
          <div>
            <h1 className="text-lg font-bold">AI Interviewer</h1>
            <p className="text-xs text-hint">Техническое собеседование голосом</p>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-5">
        {!session && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-5 shadow-sm">
            <div className="mb-5">
              <p className="text-sm uppercase text-hint">Настройка интервью</p>
              <h2 className="mt-2 text-2xl font-bold">Кого собеседуем?</h2>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block rounded-lg border border-hint/10 bg-bg p-3">
                <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-hint">
                  <Briefcase size={14} />
                  Должность
                </span>
                <input
                  value={profession}
                  onChange={handleProfessionChange}
                  className="w-full bg-transparent text-base font-semibold outline-none"
                  placeholder="backend"
                />
              </label>

              <label className="block rounded-lg border border-hint/10 bg-bg p-3">
                <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-hint">
                  <Code2 size={14} />
                  Стек
                </span>
                <input
                  value={language}
                  onChange={handleLanguageChange}
                  className="w-full bg-transparent text-base font-semibold outline-none"
                  placeholder="python"
                />
              </label>
            </div>

            <button
              type="button"
              onClick={startInterview}
              disabled={isStarting}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gold-500 px-4 py-3 font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isStarting ? <Loader2 size={18} className="animate-spin" /> : <Mic size={18} />}
              Начать интервью
            </button>
          </section>
        )}

        {session && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-gold-500">
                  Вопрос {currentQuestionNumber}/{totalQuestions}
                </p>
                <p className="mt-1 text-xs uppercase text-hint">
                  {session.profession} - {session.language || 'any stack'}
                </p>
              </div>
              {session.redirect_attempts > 0 && session.status === 'active' && (
                <span className="rounded-lg border border-gold-500/30 px-3 py-1 text-xs font-semibold text-gold-500">
                  возврат {session.redirect_attempts}/2
                </span>
              )}
            </div>

            <div className="space-y-3">
              {messages.map((message) => (
                <DialogMessage key={message.id} message={message} />
              ))}

              {isProcessing && (
                <div className="flex items-center gap-2 rounded-lg border border-hint/10 bg-bg p-3 text-sm text-hint">
                  <Loader2 size={16} className="animate-spin" />
                  Интервьюер слушает и анализирует ответ
                </div>
              )}
            </div>

            {session.status === 'active' && currentQuestion && (
              <div className="mt-5 flex items-center justify-center">
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={isProcessing || isStarting || (!canRecord && !isRecording)}
                  className={`flex h-20 w-20 items-center justify-center rounded-full shadow-xl transition-all disabled:cursor-not-allowed disabled:opacity-50 ${
                    isRecording
                      ? 'bg-red-500 text-white shadow-red-500/30'
                      : 'bg-gold-500 text-white shadow-gold-500/30'
                  }`}
                  aria-label={isRecording ? 'Остановить запись' : 'Начать запись'}
                >
                  {isRecording ? <Square size={28} className="fill-current" /> : <Mic size={30} />}
                </button>
              </div>
            )}
          </section>
        )}

        {error && (
          <section className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </section>
        )}

        {session?.status === 'completed' && finalReport && (
          <section className="rounded-lg border border-gold-500/30 bg-secondaryBg p-4">
            <h2 className="text-lg font-bold">Итог собеседования</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Уровень" value={finalReport.estimated_level || 'n/a'} />
              <Metric label="Итог" value={formatPercent(finalReport.total_score)} />
            </div>

            {finalReport.per_topic_scores && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-semibold uppercase text-hint">Темы</p>
                <div className="space-y-2">
                  {Object.entries(finalReport.per_topic_scores).map(([topic, score]) => (
                    <div key={topic} className="flex items-center justify-between text-sm">
                      <span>{topic}</span>
                      <span className="font-semibold text-gold-500">{formatPercent(score)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <ReportList title="Сильные стороны" items={finalReport.strengths} />
            <ReportList title="Проблемные темы" items={finalReport.weak_topics} />
            <ReportList title="Что практиковать" items={finalReport.recommended_study_plan} />

            <button
              type="button"
              onClick={startInterview}
              disabled={isStarting}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-hint/20 px-4 py-3 font-semibold transition-colors hover:bg-bg disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isStarting ? <Loader2 size={18} className="animate-spin" /> : <RotateCcw size={18} />}
              Новая сессия
            </button>
          </section>
        )}
      </main>
    </div>
  );
};

const DialogMessage = ({ message }: { message: ConversationMessage }) => {
  const isCandidate = message.role === 'candidate';

  return (
    <div className={`flex gap-3 ${isCandidate ? 'justify-end' : 'justify-start'}`}>
      {!isCandidate && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gold-500 text-white">
          <Bot size={17} />
        </div>
      )}
      <div
        className={`max-w-[86%] rounded-lg border p-3 text-sm leading-relaxed ${
          isCandidate
            ? 'border-gold-500/30 bg-gold-500 text-white'
            : 'border-hint/10 bg-bg text-text'
        }`}
      >
        {message.meta && (
          <p className={`mb-1 text-xs font-semibold uppercase ${isCandidate ? 'text-white/70' : 'text-hint'}`}>
            {message.meta}
          </p>
        )}
        <p className="whitespace-pre-wrap">{message.text}</p>
      </div>
      {isCandidate && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bg text-hint">
          <UserRound size={17} />
        </div>
      )}
    </div>
  );
};

const Metric = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg border border-hint/10 bg-bg p-3">
    <p className="text-xs text-hint">{label}</p>
    <p className="mt-1 font-semibold">{value}</p>
  </div>
);

const ReportList = ({ title, items }: { title: string; items?: string[] }) => {
  if (!items || items.length === 0) return null;

  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold uppercase text-hint">{title}</p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-hint">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
};

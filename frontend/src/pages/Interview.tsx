import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReactMediaRecorder } from 'react-media-recorder';
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Loader2,
  Mic,
  RotateCcw,
  Square,
  XCircle,
} from 'lucide-react';

type SessionStatus = 'active' | 'completed';

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

const API_BASE = '/api';

const formatPercent = (value: number) => `${Math.round(value)}%`;

export const Interview = () => {
  const navigate = useNavigate();
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [latestTranscript, setLatestTranscript] = useState('');
  const [latestEvaluation, setLatestEvaluation] = useState<InterviewEvaluation | null>(null);
  const [latestMetrics, setLatestMetrics] = useState<AudioMetrics | null>(null);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const startInterview = async () => {
    setIsStarting(true);
    setError('');
    setLatestTranscript('');
    setLatestEvaluation(null);
    setLatestMetrics(null);
    setFinalReport(null);

    try {
      const response = await fetch(`${API_BASE}/interview/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profession: 'backend', language: 'python' }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'Не удалось начать интервью');
      }

      const data = (await response.json()) as InterviewSession;
      setSession(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось начать интервью');
    } finally {
      setIsStarting(false);
    }
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
      setLatestTranscript(data.transcript);
      setLatestEvaluation(data.question_evaluation);
      setLatestMetrics(data.audio_metrics);
      setFinalReport(data.completed_report);

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
            <h1 className="text-lg font-bold">Backend Python Interview</h1>
            <p className="text-xs text-hint">Structured trainer</p>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-5">
        {!session && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-5 shadow-sm">
            <div className="mb-5">
              <p className="text-sm uppercase text-hint">Backend Developer</p>
              <h2 className="mt-2 text-2xl font-bold">Python interview</h2>
            </div>
            <button
              type="button"
              onClick={startInterview}
              disabled={isStarting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gold-500 px-4 py-3 font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isStarting ? <Loader2 size={18} className="animate-spin" /> : <Mic size={18} />}
              Start interview
            </button>
          </section>
        )}

        {session && currentQuestion && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-gold-500">
                  Question {currentQuestionNumber}/{totalQuestions}
                </p>
                <p className="mt-1 text-xs uppercase text-hint">
                  {currentQuestion.competency} · {currentQuestion.level} · difficulty {currentQuestion.difficulty}
                </p>
              </div>
              {session.redirect_attempts > 0 && (
                <span className="rounded-lg border border-gold-500/30 px-3 py-1 text-xs font-semibold text-gold-500">
                  redirect {session.redirect_attempts}/2
                </span>
              )}
            </div>

            <p className="text-lg font-semibold leading-relaxed">{currentQuestion.question_text}</p>

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
                aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              >
                {isRecording ? <Square size={28} className="fill-current" /> : <Mic size={30} />}
              </button>
            </div>

            {isProcessing && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-hint">
                <Loader2 size={16} className="animate-spin" />
                Processing answer
              </div>
            )}
          </section>
        )}

        {error && (
          <section className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </section>
        )}

        {latestTranscript && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-4">
            <h2 className="mb-2 text-sm font-semibold text-hint">Transcript</h2>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{latestTranscript}</p>
          </section>
        )}

        {latestEvaluation && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {latestEvaluation.should_redirect ? (
                  <RotateCcw size={18} className="text-gold-500" />
                ) : latestEvaluation.on_topic ? (
                  <CheckCircle2 size={18} className="text-emerald-500" />
                ) : (
                  <XCircle size={18} className="text-red-400" />
                )}
                <h2 className="text-sm font-semibold">Evaluation</h2>
              </div>
              <span className="text-sm font-bold text-gold-500">
                {formatPercent(latestEvaluation.coverage_percent)}
              </span>
            </div>

            <p className="text-sm leading-relaxed">{latestEvaluation.final_feedback_to_user}</p>

            {latestEvaluation.missing_points.length > 0 && (
              <div className="mt-3">
                <p className="mb-2 text-xs font-semibold uppercase text-hint">Missing points</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-hint">
                  {latestEvaluation.missing_points.slice(0, 4).map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {latestEvaluation.should_redirect && (
              <div className="mt-3 rounded-lg border border-gold-500/30 p-3 text-sm text-gold-500">
                Same question remains active
              </div>
            )}
          </section>
        )}

        {latestMetrics && (
          <section className="rounded-lg border border-hint/10 bg-secondaryBg p-4">
            <div className="mb-3 flex items-center gap-2">
              <BarChart3 size={18} className="text-hint" />
              <h2 className="text-sm font-semibold">Audio metrics</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <Metric label="Duration" value={`${latestMetrics.duration_sec}s`} />
              <Metric label="Pauses" value={String(latestMetrics.pause_count)} />
              <Metric label="WPM" value={String(Math.round(latestMetrics.approximate_words_per_minute))} />
              <Metric label="Fillers" value={String(latestMetrics.filler_words)} />
            </div>
          </section>
        )}

        {session?.status === 'completed' && finalReport && (
          <section className="rounded-lg border border-gold-500/30 bg-secondaryBg p-4">
            <h2 className="text-lg font-bold">Final report</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Level" value={finalReport.estimated_level || 'n/a'} />
              <Metric label="Score" value={`${Math.round(finalReport.total_score ?? 0)}%`} />
            </div>

            {finalReport.per_topic_scores && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-semibold uppercase text-hint">Per-topic scores</p>
                <div className="space-y-2">
                  {Object.entries(finalReport.per_topic_scores).map(([topic, score]) => (
                    <div key={topic} className="flex items-center justify-between text-sm">
                      <span>{topic}</span>
                      <span className="font-semibold text-gold-500">{Math.round(score)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <ReportList title="Strengths" items={finalReport.strengths} />
            <ReportList title="Weak topics" items={finalReport.weak_topics} />
            <ReportList title="Study plan" items={finalReport.recommended_study_plan} />

            <button
              type="button"
              onClick={startInterview}
              disabled={isStarting}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-hint/20 px-4 py-3 font-semibold transition-colors hover:bg-bg disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isStarting ? <Loader2 size={18} className="animate-spin" /> : <RotateCcw size={18} />}
              Start again
            </button>
          </section>
        )}
      </main>
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

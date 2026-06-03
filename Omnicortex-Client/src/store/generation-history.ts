import type {
  ImageHistoryItem,
  ResumeHistoryItem,
  ResumeResponse,
} from '@/types';

type ResumePageState = {
  input: string;
  result: ResumeResponse | null;
  history: ResumeHistoryItem[];
};

type ImagePageState = {
  prompt: string;
  mode: string;
  steps: number;
  imageUrl: string;
  history: ImageHistoryItem[];
};

const RESUME_PAGE_STATE_KEY = 'omnicortex-ai-resume-page';
const IMAGE_PAGE_STATE_KEY = 'omnicortex-ai-image-page';
const MAX_HISTORY_ITEMS = 8;
const LEGACY_SEEDED_RESUME_INPUT = `Aditya Sharma
Senior Software Engineer

Experience
- Led platform engineering for AI document pipelines.
- Built TypeScript frontends and Python APIs for production SaaS.

Skills
- React, TypeScript, Tailwind CSS, Python, FastAPI, Docker`;

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const raw = window.localStorage.getItem(key);

  if (!raw) {
    return fallback;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    window.localStorage.removeItem(key);
    return fallback;
  }
}

function writeStorage<T>(key: string, value: T) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

function removeStorage(key: string) {
  window.localStorage.removeItem(key);
}

function hasResumeStateContent(state: ResumePageState, defaultInput: string) {
  const normalizedInput = state.input.trim();
  const defaultNormalizedInput = defaultInput.trim();
  const legacyNormalizedInput = LEGACY_SEEDED_RESUME_INPUT.trim();

  const hasCustomInput = Boolean(
    normalizedInput &&
      normalizedInput !== defaultNormalizedInput &&
      normalizedInput !== legacyNormalizedInput,
  );

  return hasCustomInput || Boolean(state.result?.pdf_url) || state.history.length > 0;
}

export function getResumePageState(defaultInput: string): ResumePageState {
  const fallbackState = {
    input: defaultInput,
    result: null,
    history: [],
  };

  const state = readStorage<ResumePageState>(RESUME_PAGE_STATE_KEY, fallbackState);

  if (!hasResumeStateContent(state, defaultInput)) {
    removeStorage(RESUME_PAGE_STATE_KEY);
    return fallbackState;
  }

  return {
    ...state,
    history: state.history.slice(0, MAX_HISTORY_ITEMS),
  };
}

export function setResumePageState(state: ResumePageState) {
  const nextHistory = state.history.slice(0, MAX_HISTORY_ITEMS);
  const hasInput = Boolean(state.input.trim());
  const hasResult = Boolean(state.result?.pdf_url);

  if (!hasInput && !hasResult && nextHistory.length === 0) {
    removeStorage(RESUME_PAGE_STATE_KEY);
    return;
  }

  writeStorage(RESUME_PAGE_STATE_KEY, {
    ...state,
    history: nextHistory,
  });
}

export function appendResumeHistoryItem(
  history: ResumeHistoryItem[],
  item: ResumeHistoryItem,
) {
  return [item, ...history.filter((entry) => entry.pdfUrl !== item.pdfUrl)].slice(
    0,
    MAX_HISTORY_ITEMS,
  );
}

export function getImagePageState(defaultPrompt: string, defaultMode: string, defaultSteps: number): ImagePageState {
  return readStorage<ImagePageState>(IMAGE_PAGE_STATE_KEY, {
    prompt: defaultPrompt,
    mode: defaultMode,
    steps: defaultSteps,
    imageUrl: '',
    history: [],
  });
}

export function setImagePageState(state: ImagePageState) {
  const nextHistory = state.history.slice(0, MAX_HISTORY_ITEMS);
  const hasPrompt = Boolean(state.prompt.trim());
  const hasImage = Boolean(state.imageUrl);

  if (!hasPrompt && !hasImage && nextHistory.length === 0) {
    removeStorage(IMAGE_PAGE_STATE_KEY);
    return;
  }

  writeStorage(IMAGE_PAGE_STATE_KEY, {
    ...state,
    history: nextHistory,
  });
}

export function appendImageHistoryItem(
  history: ImageHistoryItem[],
  item: ImageHistoryItem,
) {
  return [item, ...history.filter((entry) => entry.imageUrl !== item.imageUrl)].slice(
    0,
    MAX_HISTORY_ITEMS,
  );
}

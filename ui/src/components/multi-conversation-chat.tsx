"use client";

import { FormEvent, ReactNode, useEffect, useState, useSyncExternalStore } from "react";
import {
  CopilotChat,
  Thread,
  useAgent,
  useRenderTool,
  useThreads,
} from "@copilotkit/react-core/v2";
import {
  getClerkAccessToken,
  subscribeToClerkAccessToken,
} from "@/lib/clerk-token-store";
import { OPEN_RESUME_PARSE_MODAL_EVENT } from "@/lib/ui-events";
import styles from "./multi-conversation-chat.module.css";

const THREAD_PAGE_SIZE = 25;
const MAX_VISIBLE_STATE_ITEMS = 5;

interface ProjectStateItem {
  id?: number;
  name?: string;
  projectName?: string;
  techStack?: string[];
  urls?: string[];
  description?: string;
  tags?: string[];
  createdAt?: string;
  updatedAt?: string;
}

interface ExperienceStateItem {
  id?: number;
  companyName?: string;
  startDate?: string;
  endDate?: string | null;
  pursuing?: boolean;
  position?: string;
  description?: string;
  location?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface AchievementStateItem {
  id?: number;
  name?: string;
  link?: string;
  organisation?: string;
  date?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface EducationStateItem {
  id?: number;
  degreeName?: string;
  degreename?: string;
  location?: string;
  startYear?: string;
  startyear?: string;
  endYear?: string | null;
  endyear?: string | null;
  pursuing?: boolean;
  cgpaOrPercentage?: string;
  "cgpa/percentage"?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface ProfileStateItem {
  name?: string;
  role?: string;
  contact?: string;
  location?: string;
  linkedinUrl?: string;
  linkedinurl?: string;
  additionalUrls?: string[];
  additionalurls?: string[];
}

interface ResumeState {
  projects?: ProjectStateItem[];
  experiences?: ExperienceStateItem[];
  achievements?: AchievementStateItem[];
  educations?: EducationStateItem[];
  summary?: string;
  skills?: string[];
  profile?: ProfileStateItem;
}

interface ParsedResumeDraft {
  projects: ProjectStateItem[];
  experiences: ExperienceStateItem[];
  achievements: AchievementStateItem[];
  educations: EducationStateItem[];
}

interface ProjectFormState {
  name: string;
  description: string;
  techStack: string;
}

interface ExperienceFormState {
  companyName: string;
  position: string;
  description: string;
  startDate: string;
  endDate: string;
  location: string;
}

interface AchievementFormState {
  name: string;
  organisation: string;
  date: string;
  link: string;
}

interface EducationFormState {
  degreeName: string;
  location: string;
  startYear: string;
  endYear: string;
  cgpaOrPercentage: string;
}

interface ProfileFormState {
  name: string;
  role: string;
  contact: string;
  location: string;
  linkedinUrl: string;
  additionalUrls: string;
}

function formatThreadTime(thread: Thread): string {
  const iso = thread.lastRunAt ?? thread.updatedAt;
  const date = new Date(iso);

  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

interface MultiConversationChatProps {
  agentId: string;
  hasPublicKey: boolean;
}

export function MultiConversationChat({
  agentId,
  hasPublicKey,
}: MultiConversationChatProps) {
  if (!hasPublicKey) {
    return <SingleSessionChat agentId={agentId} />;
  }

  return <MultiSessionChat agentId={agentId} />;
}

function SingleSessionChat({ agentId }: { agentId: string }) {
  return (
    <main className={styles.singleSession}>
      <ToolCallRenderers agentId={agentId} />
      <div className={styles.chatBody}>
        <div className={styles.chatWorkspace}>
          <ResumeStatePanel agentId={agentId} />
          <div className={styles.chatPane}>
            <CopilotChat
              agentId={agentId}
              chatView={styles.chatView}
              labels={{
                chatInputPlaceholder: "Ask your agent anything...",
              }}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

function MultiSessionChat({ agentId }: { agentId: string }) {
  const [activeThreadId, setActiveThreadId] = useState<string | undefined>();
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editingThreadName, setEditingThreadName] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    threads,
    isLoading,
    error,
    hasMoreThreads,
    isFetchingMoreThreads,
    fetchMoreThreads,
    renameThread,
    archiveThread,
  } = useThreads({
    agentId,
    limit: THREAD_PAGE_SIZE,
  });

  const startNewConversation = () => {
    setActiveThreadId(undefined);
    setEditingThreadId(null);
    setEditingThreadName("");
    setActionError(null);
  };

  const startRename = (thread: Thread) => {
    setEditingThreadId(thread.id);
    setEditingThreadName(thread.name ?? "");
    setActionError(null);
  };

  const cancelRename = () => {
    setEditingThreadId(null);
    setEditingThreadName("");
    setActionError(null);
  };

  const submitRename = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!editingThreadId) {
      return;
    }

    const trimmedName = editingThreadName.trim();
    if (!trimmedName) {
      setActionError("Thread name cannot be empty.");
      return;
    }

    try {
      await renameThread(editingThreadId, trimmedName);
      setEditingThreadId(null);
      setEditingThreadName("");
      setActionError(null);
    } catch (renameError) {
      const message =
        renameError instanceof Error ? renameError.message : "Rename failed.";
      setActionError(message);
    }
  };

  const handleArchive = async (threadId: string) => {
    try {
      await archiveThread(threadId);
      if (threadId === activeThreadId) {
        setActiveThreadId(undefined);
      }
      setActionError(null);
    } catch (archiveError) {
      const message =
        archiveError instanceof Error ? archiveError.message : "Archive failed.";
      setActionError(message);
    }
  };

  return (
    <div className={styles.layout}>
      <ToolCallRenderers agentId={agentId} />
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div>
            <h1 className={styles.sidebarTitle}>Conversations</h1>
            <p className={styles.sidebarSubtitle}>Agent: {agentId}</p>
          </div>
          <button
            type="button"
            className={styles.newThreadButton}
            onClick={startNewConversation}
          >
            New
          </button>
        </div>

        {error && (
          <p className={styles.error}>
            Could not load threads: {error.message}
          </p>
        )}

        {actionError && <p className={styles.error}>{actionError}</p>}

        {isLoading ? (
          <p className={styles.emptyState}>Loading conversations...</p>
        ) : threads.length === 0 ? (
          <p className={styles.emptyState}>No conversations yet.</p>
        ) : (
          <ul className={styles.threadList}>
            {threads.map((thread) => {
              const isActive = thread.id === activeThreadId;
              const isEditing = thread.id === editingThreadId;

              return (
                <li
                  key={thread.id}
                  className={`${styles.threadItem} ${isActive ? styles.threadItemActive : ""}`}
                >
                  {isEditing ? (
                    <form
                      className={styles.renameForm}
                      onSubmit={(event) => void submitRename(event)}
                    >
                      <input
                        className={styles.renameInput}
                        value={editingThreadName}
                        onChange={(event) =>
                          setEditingThreadName(event.target.value)
                        }
                        autoFocus
                      />
                      <div className={styles.renameActions}>
                        <button type="submit" className={styles.actionButton}>
                          Save
                        </button>
                        <button
                          type="button"
                          className={styles.actionButton}
                          onClick={cancelRename}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <button
                        type="button"
                        className={styles.threadSelect}
                        onClick={() => setActiveThreadId(thread.id)}
                      >
                        <span className={styles.threadName}>
                          {thread.name ?? "New conversation"}
                        </span>
                        <span className={styles.threadTime}>
                          {formatThreadTime(thread)}
                        </span>
                      </button>
                      <div className={styles.threadActions}>
                        <button
                          type="button"
                          className={styles.actionButton}
                          onClick={() => startRename(thread)}
                        >
                          Rename
                        </button>
                        <button
                          type="button"
                          className={`${styles.actionButton} ${styles.archiveButton}`}
                          onClick={() => void handleArchive(thread.id)}
                        >
                          Archive
                        </button>
                      </div>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        {hasMoreThreads && (
          <button
            type="button"
            className={styles.loadMoreButton}
            onClick={() => fetchMoreThreads()}
            disabled={isFetchingMoreThreads}
          >
            {isFetchingMoreThreads ? "Loading..." : "Load older conversations"}
          </button>
        )}
      </aside>

      <main className={styles.chatPanel}>
        <div className={styles.chatBody}>
          <div className={styles.chatWorkspace}>
            <ResumeStatePanel agentId={agentId} />
            <div className={styles.chatPane}>
              <CopilotChat
                agentId={agentId}
                threadId={activeThreadId}
                chatView={styles.chatView}
                labels={{
                  chatInputPlaceholder: "Ask your agent anything...",
                }}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function normalizeArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function normalizeProfile(value: unknown): Required<ProfileStateItem> {
  const payload = asRecord(value);
  return {
    name: asString(payload.name) ?? "",
    role: asString(payload.role) ?? "",
    contact: asString(payload.contact) ?? "",
    location: asString(payload.location) ?? "",
    linkedinUrl: asString(payload.linkedinUrl) ?? asString(payload.linkedinurl) ?? "",
    linkedinurl: asString(payload.linkedinurl) ?? "",
    additionalUrls: normalizeArray<string>(payload.additionalUrls ?? payload.additionalurls),
    additionalurls: normalizeArray<string>(payload.additionalurls),
  };
}

function emptyParsedResumeDraft(): ParsedResumeDraft {
  return {
    projects: [],
    experiences: [],
    achievements: [],
    educations: [],
  };
}

async function parseBackendError(response: Response): Promise<string> {
  const fallback = `Request failed with status ${response.status}.`;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return fallback;
  }
  try {
    const payload = (await response.json()) as Record<string, unknown>;
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (typeof payload.error === "string") {
      return payload.error;
    }
    return fallback;
  } catch {
    return fallback;
  }
}

function normalizeParsedResume(value: unknown): ParsedResumeDraft {
  const payload = asRecord(value);
  return {
    projects: normalizeArray<Record<string, unknown>>(payload.projects).map((item) => ({
      name: asString(item.name) ?? asString(item.projectName) ?? "",
      projectName: asString(item.projectName) ?? asString(item.name) ?? "",
      description: asString(item.description) ?? "",
      techStack: normalizeArray<string>(item.techStack).map((entry) => asString(entry) ?? "").filter(Boolean),
    })),
    experiences: normalizeArray<Record<string, unknown>>(payload.experiences).map((item) => ({
      companyName: asString(item.companyName) ?? "",
      position: asString(item.position) ?? "",
      description: asString(item.description) ?? "",
      startDate: asString(item.startDate) ?? "",
      endDate: asString(item.endDate) ?? null,
      pursuing: Boolean(item.pursuing),
      location: asString(item.location) ?? "",
    })),
    achievements: normalizeArray<Record<string, unknown>>(payload.achievements).map((item) => ({
      name: asString(item.name) ?? "",
      organisation: asString(item.organisation) ?? "",
      date: asString(item.date) ?? "",
      link: asString(item.link) ?? "",
    })),
    educations: normalizeArray<Record<string, unknown>>(payload.educations).map((item) => ({
      degreeName: asString(item.degreeName) ?? asString(item.degreename) ?? "",
      location: asString(item.location) ?? "",
      startYear: asString(item.startYear) ?? asString(item.startyear) ?? "",
      endYear: asString(item.endYear) ?? asString(item.endyear) ?? null,
      pursuing: Boolean(item.pursuing),
      cgpaOrPercentage:
        asString(item.cgpaOrPercentage) ?? asString(item["cgpa/percentage"]) ?? "",
    })),
  };
}

function collectMissingParsedDraftFields(draft: ParsedResumeDraft): string[] {
  const issues: string[] = [];

  draft.projects.forEach((item, index) => {
    const missing: string[] = [];
    if (!(item.projectName ?? item.name ?? "").trim()) {
      missing.push("projectName");
    }
    if (!(item.description ?? "").trim()) {
      missing.push("description");
    }
    if (missing.length > 0) {
      issues.push(`projects[${index + 1}]: ${missing.join(", ")}`);
    }
  });

  draft.experiences.forEach((item, index) => {
    const missing: string[] = [];
    const pursuing = Boolean(item.pursuing);
    if (!(item.companyName ?? "").trim()) {
      missing.push("companyName");
    }
    if (!(item.position ?? "").trim()) {
      missing.push("position");
    }
    if (!(item.description ?? "").trim()) {
      missing.push("description");
    }
    if (!(item.startDate ?? "").trim()) {
      missing.push("startDate");
    }
    if (!pursuing && !(item.endDate ?? "").trim()) {
      missing.push("endDate (or set pursuing=true)");
    }
    if (!(item.location ?? "").trim()) {
      missing.push("location");
    }
    if (missing.length > 0) {
      issues.push(`experiences[${index + 1}]: ${missing.join(", ")}`);
    }
  });

  draft.achievements.forEach((item, index) => {
    const missing: string[] = [];
    if (!(item.name ?? "").trim()) {
      missing.push("name");
    }
    if (!(item.organisation ?? "").trim()) {
      missing.push("organisation");
    }
    if (!(item.date ?? "").trim()) {
      missing.push("date");
    }
    if (!(item.link ?? "").trim()) {
      missing.push("link");
    }
    if (missing.length > 0) {
      issues.push(`achievements[${index + 1}]: ${missing.join(", ")}`);
    }
  });

  draft.educations.forEach((item, index) => {
    const missing: string[] = [];
    const pursuing = Boolean(item.pursuing);
    if (!(item.degreeName ?? item.degreename ?? "").trim()) {
      missing.push("degreeName");
    }
    if (!(item.location ?? "").trim()) {
      missing.push("location");
    }
    if (!(item.startYear ?? item.startyear ?? "").trim()) {
      missing.push("startYear");
    }
    if (!pursuing && !(item.endYear ?? item.endyear ?? "").trim()) {
      missing.push("endYear (or set pursuing=true)");
    }
    if (!(item.cgpaOrPercentage ?? item["cgpa/percentage"] ?? "").trim()) {
      missing.push("cgpaOrPercentage");
    }
    if (missing.length > 0) {
      issues.push(`educations[${index + 1}]: ${missing.join(", ")}`);
    }
  });

  return issues;
}

function ResumeStatePanel({ agentId }: { agentId: string }) {
  const { agent } = useAgent({ agentId });
  const accessToken = useSyncExternalStore(
    subscribeToClerkAccessToken,
    getClerkAccessToken,
    () => null,
  );
  const state = (agent.state ?? {}) as ResumeState;
  const projects = normalizeArray<ProjectStateItem>(state.projects);
  const experiences = normalizeArray<ExperienceStateItem>(state.experiences);
  const achievements = normalizeArray<AchievementStateItem>(state.achievements);
  const educations = normalizeArray<EducationStateItem>(state.educations);
  const summary = asString(state.summary) ?? "";
  const skills = normalizeArray<string>(state.skills);
  const profile = normalizeProfile(state.profile);
  const hasProfileData = Boolean(
    profile.name ||
      profile.role ||
      profile.contact ||
      profile.location ||
      profile.linkedinUrl ||
      profile.additionalUrls.length,
  );
  const hasAnyState =
    projects.length > 0 ||
    experiences.length > 0 ||
    achievements.length > 0 ||
    educations.length > 0 ||
    Boolean(summary) ||
    skills.length > 0 ||
    hasProfileData;
  const [editingProjectIndex, setEditingProjectIndex] = useState<number | null>(null);
  const [editingExperienceIndex, setEditingExperienceIndex] = useState<number | null>(null);
  const [editingAchievementIndex, setEditingAchievementIndex] = useState<number | null>(null);
  const [editingEducationIndex, setEditingEducationIndex] = useState<number | null>(null);
  const [projectForm, setProjectForm] = useState<ProjectFormState>({
    name: "",
    description: "",
    techStack: "",
  });
  const [experienceForm, setExperienceForm] = useState<ExperienceFormState>({
    companyName: "",
    position: "",
    description: "",
    startDate: "",
    endDate: "",
    location: "",
  });
  const [achievementForm, setAchievementForm] = useState<AchievementFormState>({
    name: "",
    organisation: "",
    date: "",
    link: "",
  });
  const [educationForm, setEducationForm] = useState<EducationFormState>({
    degreeName: "",
    location: "",
    startYear: "",
    endYear: "",
    cgpaOrPercentage: "",
  });
  const [isEditingSummary, setIsEditingSummary] = useState(false);
  const [summaryDraft, setSummaryDraft] = useState<string>("");
  const [isEditingSkills, setIsEditingSkills] = useState(false);
  const [skillsDraft, setSkillsDraft] = useState<string>("");
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState<ProfileFormState>({
    name: "",
    role: "",
    contact: "",
    location: "",
    linkedinUrl: "",
    additionalUrls: "",
  });
  const [isParseModalOpen, setIsParseModalOpen] = useState(false);
  const [isParsingResume, setIsParsingResume] = useState(false);
  const [isSavingParsedToSystem, setIsSavingParsedToSystem] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [parseSuccess, setParseSuccess] = useState<string | null>(null);
  const [selectedResumeFile, setSelectedResumeFile] = useState<File | null>(null);
  const [parsedResumeDraft, setParsedResumeDraft] = useState<ParsedResumeDraft>(
    emptyParsedResumeDraft(),
  );

  const applyStatePatch = (patch: Partial<ResumeState>) => {
    agent.setState({
      ...((agent.state ?? {}) as Record<string, unknown>),
      ...patch,
    });
  };

  useEffect(() => {
    const handler = () => {
      setIsParseModalOpen(true);
      setParseError(null);
      setParseSuccess(null);
      setSelectedResumeFile(null);
      setParsedResumeDraft(emptyParsedResumeDraft());
    };
    window.addEventListener(OPEN_RESUME_PARSE_MODAL_EVENT, handler);
    return () => {
      window.removeEventListener(OPEN_RESUME_PARSE_MODAL_EVENT, handler);
    };
  }, []);

  const closeParseModal = () => {
    if (isParsingResume) {
      return;
    }
    setIsParseModalOpen(false);
    setParseError(null);
    setParseSuccess(null);
    setSelectedResumeFile(null);
    setParsedResumeDraft(emptyParsedResumeDraft());
  };

  const parseUploadedResume = async () => {
    if (!accessToken) {
      setParseError("Sign in again to parse resumes.");
      return;
    }
    if (!selectedResumeFile) {
      setParseError("Select a PDF or DOCX file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedResumeFile);
    setIsParsingResume(true);
    setParseError(null);
    setParseSuccess(null);
    try {
      const response = await fetch("/api/backend/resumes/parse", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await parseBackendError(response));
      }
      const payload = (await response.json()) as unknown;
      setParsedResumeDraft(normalizeParsedResume(payload));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to parse uploaded resume.";
      setParseError(message);
    } finally {
      setIsParsingResume(false);
    }
  };

  const applyParsedResumeToState = () => {
    applyStatePatch({
      projects: parsedResumeDraft.projects,
      experiences: parsedResumeDraft.experiences,
      achievements: parsedResumeDraft.achievements,
      educations: parsedResumeDraft.educations,
    });
    closeParseModal();
  };

  const addParsedResumeToSystem = async () => {
    if (!accessToken) {
      setParseError("Sign in again to save parsed data.");
      return;
    }
    const validationIssues = collectMissingParsedDraftFields(parsedResumeDraft);
    if (validationIssues.length > 0) {
      setParseSuccess(null);
      setParseError(
        `Please add missing fields before saving: ${validationIssues.join("; ")}`,
      );
      return;
    }
    setIsSavingParsedToSystem(true);
    setParseError(null);
    setParseSuccess(null);
    try {
      const response = await fetch("/api/backend/resumes/parse/save", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(parsedResumeDraft),
      });
      if (!response.ok) {
        throw new Error(await parseBackendError(response));
      }
      const result = (await response.json()) as Record<string, unknown>;
      const saved = asRecord(result.saved);
      setParseSuccess(
        `Saved to system: ${saved.projects ?? 0} projects, ${saved.experiences ?? 0} experiences, ${saved.achievements ?? 0} achievements, ${saved.educations ?? 0} educations.`,
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to save parsed data to system.";
      setParseError(message);
    } finally {
      setIsSavingParsedToSystem(false);
    }
  };

  const resetProjectForm = () => {
    setEditingProjectIndex(null);
    setProjectForm({ name: "", description: "", techStack: "" });
  };

  const resetExperienceForm = () => {
    setEditingExperienceIndex(null);
    setExperienceForm({
      companyName: "",
      position: "",
      description: "",
      startDate: "",
      endDate: "",
      location: "",
    });
  };

  const resetAchievementForm = () => {
    setEditingAchievementIndex(null);
    setAchievementForm({ name: "", organisation: "", date: "", link: "" });
  };

  const resetEducationForm = () => {
    setEditingEducationIndex(null);
    setEducationForm({
      degreeName: "",
      location: "",
      startYear: "",
      endYear: "",
      cgpaOrPercentage: "",
    });
  };

  const submitProjectForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = projectForm.name.trim();
    const description = projectForm.description.trim();
    if (!name || !description) {
      return;
    }
    const item: ProjectStateItem = {
      name,
      description,
      techStack: splitCsv(projectForm.techStack),
    };
    const updatedProjects = [...projects];
    if (editingProjectIndex === null) {
      updatedProjects.push(item);
    } else {
      updatedProjects[editingProjectIndex] = item;
    }
    applyStatePatch({ projects: updatedProjects });
    resetProjectForm();
  };

  const submitExperienceForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const companyName = experienceForm.companyName.trim();
    const position = experienceForm.position.trim();
    const description = experienceForm.description.trim();
    const startDate = experienceForm.startDate.trim();
    const location = experienceForm.location.trim();
    const endDate = experienceForm.endDate.trim();
    if (!companyName || !position || !description || !startDate || !location) {
      return;
    }
    const item: ExperienceStateItem = {
      companyName,
      position,
      description,
      startDate,
      endDate: endDate || null,
      location,
    };
    const updatedExperiences = [...experiences];
    if (editingExperienceIndex === null) {
      updatedExperiences.push(item);
    } else {
      updatedExperiences[editingExperienceIndex] = item;
    }
    applyStatePatch({ experiences: updatedExperiences });
    resetExperienceForm();
  };

  const submitAchievementForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = achievementForm.name.trim();
    const organisation = achievementForm.organisation.trim();
    const date = achievementForm.date.trim();
    const link = achievementForm.link.trim();
    if (!name || !organisation || !date || !link) {
      return;
    }
    const item: AchievementStateItem = {
      name,
      organisation,
      date,
      link,
    };
    const updatedAchievements = [...achievements];
    if (editingAchievementIndex === null) {
      updatedAchievements.push(item);
    } else {
      updatedAchievements[editingAchievementIndex] = item;
    }
    applyStatePatch({ achievements: updatedAchievements });
    resetAchievementForm();
  };

  const submitEducationForm = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const degreeName = educationForm.degreeName.trim();
    const location = educationForm.location.trim();
    const startYear = educationForm.startYear.trim();
    const endYear = educationForm.endYear.trim();
    const cgpaOrPercentage = educationForm.cgpaOrPercentage.trim();
    if (!degreeName || !location || !startYear || !cgpaOrPercentage) {
      return;
    }
    const item: EducationStateItem = {
      degreeName,
      location,
      startYear,
      endYear: endYear || null,
      cgpaOrPercentage,
    };
    const updatedEducations = [...educations];
    if (editingEducationIndex === null) {
      updatedEducations.push(item);
    } else {
      updatedEducations[editingEducationIndex] = item;
    }
    applyStatePatch({ educations: updatedEducations });
    resetEducationForm();
  };

  const startSummaryEdit = () => {
    setIsEditingSummary(true);
    setSummaryDraft(summary);
  };

  const cancelSummaryEdit = () => {
    setIsEditingSummary(false);
    setSummaryDraft("");
  };

  const saveSummary = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextSummary = summaryDraft.trim();
    if (!nextSummary) {
      return;
    }
    applyStatePatch({ summary: nextSummary });
    cancelSummaryEdit();
  };

  const startSkillsEdit = () => {
    setIsEditingSkills(true);
    setSkillsDraft(skills.join(", "));
  };

  const cancelSkillsEdit = () => {
    setIsEditingSkills(false);
    setSkillsDraft("");
  };

  const saveSkills = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextSkills = splitCsv(skillsDraft);
    if (nextSkills.length === 0) {
      return;
    }
    applyStatePatch({ skills: nextSkills });
    cancelSkillsEdit();
  };

  const startProfileEdit = () => {
    setIsEditingProfile(true);
    setProfileForm({
      name: profile.name,
      role: profile.role,
      contact: profile.contact,
      location: profile.location,
      linkedinUrl: profile.linkedinUrl,
      additionalUrls: profile.additionalUrls.join(", "),
    });
  };

  const cancelProfileEdit = () => {
    setIsEditingProfile(false);
    setProfileForm({
      name: "",
      role: "",
      contact: "",
      location: "",
      linkedinUrl: "",
      additionalUrls: "",
    });
  };

  const saveProfile = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextProfile = {
      name: profileForm.name.trim(),
      role: profileForm.role.trim(),
      contact: profileForm.contact.trim(),
      location: profileForm.location.trim(),
      linkedinUrl: profileForm.linkedinUrl.trim(),
      additionalUrls: splitCsv(profileForm.additionalUrls),
    };
    if (
      !nextProfile.name ||
      !nextProfile.role ||
      !nextProfile.contact ||
      !nextProfile.location ||
      !nextProfile.linkedinUrl
    ) {
      return;
    }
    applyStatePatch({ profile: nextProfile });
    cancelProfileEdit();
  };

  return (
    <aside className={styles.resumeStatePanel}>
      <div className={styles.resumeStateHeader}>
        <h3>Shared Resume State</h3>
        <div className={styles.resumeStateHeaderActions}>
          {!hasAnyState && <span className={styles.stateHint}>No snapshot loaded yet.</span>}
        </div>
      </div>

      <div className={styles.stateGrid}>
        <StateSection
          title="Summary"
          count={1}
          emptyLabel="No summary"
          items={[summary]}
          renderItem={(item) =>
            isEditingSummary ? (
              <form className={styles.inlineForm} onSubmit={saveSummary}>
                <label className={styles.inlineLabel}>
                  Summary
                  <textarea
                    className={styles.inlineTextarea}
                    value={summaryDraft}
                    onChange={(event) => setSummaryDraft(event.target.value)}
                  />
                </label>
                <div className={styles.inlineActions}>
                  <button type="submit" className={styles.inlineActionPrimary}>
                    Save Summary
                  </button>
                  <button
                    type="button"
                    className={styles.inlineActionSecondary}
                    onClick={cancelSummaryEdit}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <p className={styles.payloadLine}>
                  <span className={styles.payloadValue}>{item || "Not provided"}</span>
                </p>
                <div className={styles.payloadActions}>
                  <button
                    type="button"
                    className={styles.payloadActionButton}
                    onClick={startSummaryEdit}
                  >
                    {item ? "Edit" : "Set"}
                  </button>
                  <button
                    type="button"
                    className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                    onClick={() => applyStatePatch({ summary: "" })}
                    disabled={!item}
                  >
                    Clear
                  </button>
                </div>
              </>
            )
          }
        />
        <StateSection
          title="Profile"
          count={1}
          emptyLabel="No profile"
          items={[profile]}
          renderItem={(item) =>
            isEditingProfile ? (
              <form className={styles.inlineForm} onSubmit={saveProfile}>
                <label className={styles.inlineLabel}>
                  Name
                  <input
                    className={styles.inlineInput}
                    value={profileForm.name}
                    onChange={(event) =>
                      setProfileForm((current) => ({ ...current, name: event.target.value }))
                    }
                  />
                </label>
                <label className={styles.inlineLabel}>
                  Role
                  <input
                    className={styles.inlineInput}
                    value={profileForm.role}
                    onChange={(event) =>
                      setProfileForm((current) => ({ ...current, role: event.target.value }))
                    }
                  />
                </label>
                <label className={styles.inlineLabel}>
                  Contact
                  <input
                    className={styles.inlineInput}
                    value={profileForm.contact}
                    onChange={(event) =>
                      setProfileForm((current) => ({ ...current, contact: event.target.value }))
                    }
                  />
                </label>
                <label className={styles.inlineLabel}>
                  Location
                  <input
                    className={styles.inlineInput}
                    value={profileForm.location}
                    onChange={(event) =>
                      setProfileForm((current) => ({ ...current, location: event.target.value }))
                    }
                  />
                </label>
                <label className={styles.inlineLabel}>
                  LinkedIn URL
                  <input
                    className={styles.inlineInput}
                    value={profileForm.linkedinUrl}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        linkedinUrl: event.target.value,
                      }))
                    }
                  />
                </label>
                <label className={styles.inlineLabel}>
                  Additional URLs (comma separated)
                  <input
                    className={styles.inlineInput}
                    value={profileForm.additionalUrls}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        additionalUrls: event.target.value,
                      }))
                    }
                  />
                </label>
                <div className={styles.inlineActions}>
                  <button type="submit" className={styles.inlineActionPrimary}>
                    Save Profile
                  </button>
                  <button
                    type="button"
                    className={styles.inlineActionSecondary}
                    onClick={cancelProfileEdit}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <PayloadField label="Name" value={item.name} />
                <PayloadField label="Role" value={item.role} />
                <PayloadField label="Contact" value={item.contact} />
                <PayloadField label="Location" value={item.location} />
                <PayloadField label="LinkedIn" value={item.linkedinUrl || item.linkedinurl} />
                <PayloadTagList
                  label="Additional URLs"
                  values={normalizeArray<string>(item.additionalUrls ?? item.additionalurls)}
                  emptyLabel="No additional URLs provided"
                />
                <div className={styles.payloadActions}>
                  <button
                    type="button"
                    className={styles.payloadActionButton}
                    onClick={startProfileEdit}
                  >
                    {hasProfileData ? "Edit" : "Set"}
                  </button>
                  <button
                    type="button"
                    className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                    onClick={() =>
                      applyStatePatch({
                        profile: {
                          name: "",
                          role: "",
                          contact: "",
                          location: "",
                          linkedinUrl: "",
                          additionalUrls: [],
                        },
                      })
                    }
                    disabled={!hasProfileData}
                  >
                    Clear
                  </button>
                </div>
              </>
            )
          }
        />
        <StateSection
          title="Skills"
          count={skills.length}
          emptyLabel="No skills"
          items={[skills]}
          renderItem={(item) =>
            isEditingSkills ? (
              <form className={styles.inlineForm} onSubmit={saveSkills}>
                <label className={styles.inlineLabel}>
                  Skills (comma separated)
                  <input
                    className={styles.inlineInput}
                    value={skillsDraft}
                    onChange={(event) => setSkillsDraft(event.target.value)}
                  />
                </label>
                <div className={styles.inlineActions}>
                  <button type="submit" className={styles.inlineActionPrimary}>
                    Save Skills
                  </button>
                  <button
                    type="button"
                    className={styles.inlineActionSecondary}
                    onClick={cancelSkillsEdit}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <PayloadTagList
                  label="Skills"
                  values={item}
                  emptyLabel="No skills provided"
                />
                <div className={styles.payloadActions}>
                  <button
                    type="button"
                    className={styles.payloadActionButton}
                    onClick={startSkillsEdit}
                  >
                    {item.length > 0 ? "Edit" : "Set"}
                  </button>
                  <button
                    type="button"
                    className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                    onClick={() => applyStatePatch({ skills: [] })}
                    disabled={item.length === 0}
                  >
                    Clear
                  </button>
                </div>
              </>
            )
          }
        />
        <StateSection
          title="Projects"
          count={projects.length}
          emptyLabel="No projects"
          items={projects}
          renderItem={(item, index) => (
            <>
              <p className={styles.payloadTitle}>
                {item.name ?? item.projectName ?? "Untitled project"}
              </p>
              <PayloadField label="Description" value={item.description} />
              <PayloadTagList
                label="Tech Stack"
                values={normalizeArray<string>(item.techStack)}
                emptyLabel="No technologies provided"
              />
              <div className={styles.payloadActions}>
                <button
                  type="button"
                  className={styles.payloadActionButton}
                  onClick={() => {
                    setEditingProjectIndex(index);
                    setProjectForm({
                      name: item.name ?? item.projectName ?? "",
                      description: item.description ?? "",
                      techStack: normalizeArray<string>(item.techStack).join(", "),
                    });
                  }}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                  onClick={() =>
                    applyStatePatch({
                      projects: projects.filter((_, projectIndex) => projectIndex !== index),
                    })
                  }
                >
                  Delete
                </button>
              </div>
            </>
          )}
          footer={
            <form className={styles.inlineForm} onSubmit={submitProjectForm}>
              <label className={styles.inlineLabel}>
                Project Name
                <input
                  className={styles.inlineInput}
                  value={projectForm.name}
                  onChange={(event) =>
                    setProjectForm((current) => ({ ...current, name: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Description
                <textarea
                  className={styles.inlineTextarea}
                  value={projectForm.description}
                  onChange={(event) =>
                    setProjectForm((current) => ({ ...current, description: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Tech Stack (comma separated)
                <input
                  className={styles.inlineInput}
                  value={projectForm.techStack}
                  onChange={(event) =>
                    setProjectForm((current) => ({ ...current, techStack: event.target.value }))
                  }
                />
              </label>
              <div className={styles.inlineActions}>
                <button type="submit" className={styles.inlineActionPrimary}>
                  {editingProjectIndex === null ? "Add Project" : "Update Project"}
                </button>
                <button
                  type="button"
                  className={styles.inlineActionSecondary}
                  onClick={resetProjectForm}
                >
                  Clear
                </button>
              </div>
            </form>
          }
        />
        <StateSection
          title="Experiences"
          count={experiences.length}
          emptyLabel="No experiences"
          items={experiences}
          renderItem={(item, index) => (
            <>
              <p className={styles.payloadTitle}>
                {item.position ?? "Role not provided"}
              </p>
              <PayloadField label="Company" value={item.companyName} />
              <PayloadField
                label="Dates"
                value={
                  item.startDate
                    ? `${item.startDate} - ${item.endDate ?? "Present"}`
                    : undefined
                }
              />
              <PayloadField label="Location" value={item.location} />
              <PayloadField label="Description" value={item.description} />
              <div className={styles.payloadActions}>
                <button
                  type="button"
                  className={styles.payloadActionButton}
                  onClick={() => {
                    setEditingExperienceIndex(index);
                    setExperienceForm({
                      companyName: item.companyName ?? "",
                      position: item.position ?? "",
                      description: item.description ?? "",
                      startDate: item.startDate ?? "",
                      endDate: item.endDate ?? "",
                      location: item.location ?? "",
                    });
                  }}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                  onClick={() =>
                    applyStatePatch({
                      experiences: experiences.filter(
                        (_, experienceIndex) => experienceIndex !== index,
                      ),
                    })
                  }
                >
                  Delete
                </button>
              </div>
            </>
          )}
          footer={
            <form className={styles.inlineForm} onSubmit={submitExperienceForm}>
              <label className={styles.inlineLabel}>
                Company
                <input
                  className={styles.inlineInput}
                  value={experienceForm.companyName}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      companyName: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Position
                <input
                  className={styles.inlineInput}
                  value={experienceForm.position}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      position: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Description
                <textarea
                  className={styles.inlineTextarea}
                  value={experienceForm.description}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      description: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Start Date
                <input
                  className={styles.inlineInput}
                  value={experienceForm.startDate}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      startDate: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                End Date (optional)
                <input
                  className={styles.inlineInput}
                  value={experienceForm.endDate}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      endDate: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Location
                <input
                  className={styles.inlineInput}
                  value={experienceForm.location}
                  onChange={(event) =>
                    setExperienceForm((current) => ({
                      ...current,
                      location: event.target.value,
                    }))
                  }
                />
              </label>
              <div className={styles.inlineActions}>
                <button type="submit" className={styles.inlineActionPrimary}>
                  {editingExperienceIndex === null ? "Add Experience" : "Update Experience"}
                </button>
                <button
                  type="button"
                  className={styles.inlineActionSecondary}
                  onClick={resetExperienceForm}
                >
                  Clear
                </button>
              </div>
            </form>
          }
        />
        <StateSection
          title="Achievements"
          count={achievements.length}
          emptyLabel="No achievements"
          items={achievements}
          renderItem={(item, index) => (
            <>
              <p className={styles.payloadTitle}>{item.name ?? "Untitled achievement"}</p>
              <PayloadField label="Organisation" value={item.organisation} />
              <PayloadField label="Date" value={item.date} />
              <PayloadField label="Link" value={item.link} />
              <div className={styles.payloadActions}>
                <button
                  type="button"
                  className={styles.payloadActionButton}
                  onClick={() => {
                    setEditingAchievementIndex(index);
                    setAchievementForm({
                      name: item.name ?? "",
                      organisation: item.organisation ?? "",
                      date: item.date ?? "",
                      link: item.link ?? "",
                    });
                  }}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                  onClick={() =>
                    applyStatePatch({
                      achievements: achievements.filter(
                        (_, achievementIndex) => achievementIndex !== index,
                      ),
                    })
                  }
                >
                  Delete
                </button>
              </div>
            </>
          )}
          footer={
            <form className={styles.inlineForm} onSubmit={submitAchievementForm}>
              <label className={styles.inlineLabel}>
                Name
                <input
                  className={styles.inlineInput}
                  value={achievementForm.name}
                  onChange={(event) =>
                    setAchievementForm((current) => ({ ...current, name: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Organisation
                <input
                  className={styles.inlineInput}
                  value={achievementForm.organisation}
                  onChange={(event) =>
                    setAchievementForm((current) => ({
                      ...current,
                      organisation: event.target.value,
                    }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Date
                <input
                  className={styles.inlineInput}
                  value={achievementForm.date}
                  onChange={(event) =>
                    setAchievementForm((current) => ({ ...current, date: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Link
                <input
                  className={styles.inlineInput}
                  value={achievementForm.link}
                  onChange={(event) =>
                    setAchievementForm((current) => ({ ...current, link: event.target.value }))
                  }
                />
              </label>
              <div className={styles.inlineActions}>
                <button type="submit" className={styles.inlineActionPrimary}>
                  {editingAchievementIndex === null ? "Add Achievement" : "Update Achievement"}
                </button>
                <button
                  type="button"
                  className={styles.inlineActionSecondary}
                  onClick={resetAchievementForm}
                >
                  Clear
                </button>
              </div>
            </form>
          }
        />
        <StateSection
          title="Educations"
          count={educations.length}
          emptyLabel="No educations"
          items={educations}
          renderItem={(item, index) => (
            <>
              <p className={styles.payloadTitle}>{item.degreeName ?? item.degreename ?? "Untitled degree"}</p>
              <PayloadField label="Location" value={item.location} />
              <PayloadField
                label="Years"
                value={
                  item.startYear || item.startyear
                    ? `${item.startYear ?? item.startyear} - ${item.endYear ?? item.endyear ?? "Present"}`
                    : undefined
                }
              />
              <PayloadField
                label="CGPA/Percentage"
                value={item.cgpaOrPercentage ?? item["cgpa/percentage"]}
              />
              <div className={styles.payloadActions}>
                <button
                  type="button"
                  className={styles.payloadActionButton}
                  onClick={() => {
                    setEditingEducationIndex(index);
                    setEducationForm({
                      degreeName: item.degreeName ?? item.degreename ?? "",
                      location: item.location ?? "",
                      startYear: item.startYear ?? item.startyear ?? "",
                      endYear: item.endYear ?? item.endyear ?? "",
                      cgpaOrPercentage: item.cgpaOrPercentage ?? item["cgpa/percentage"] ?? "",
                    });
                  }}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className={`${styles.payloadActionButton} ${styles.deleteActionButton}`}
                  onClick={() =>
                    applyStatePatch({
                      educations: educations.filter((_, educationIndex) => educationIndex !== index),
                    })
                  }
                >
                  Delete
                </button>
              </div>
            </>
          )}
          footer={
            <form className={styles.inlineForm} onSubmit={submitEducationForm}>
              <label className={styles.inlineLabel}>
                Degree Name
                <input
                  className={styles.inlineInput}
                  value={educationForm.degreeName}
                  onChange={(event) =>
                    setEducationForm((current) => ({ ...current, degreeName: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Location
                <input
                  className={styles.inlineInput}
                  value={educationForm.location}
                  onChange={(event) =>
                    setEducationForm((current) => ({ ...current, location: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                Start Year
                <input
                  className={styles.inlineInput}
                  value={educationForm.startYear}
                  onChange={(event) =>
                    setEducationForm((current) => ({ ...current, startYear: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                End Year (optional)
                <input
                  className={styles.inlineInput}
                  value={educationForm.endYear}
                  onChange={(event) =>
                    setEducationForm((current) => ({ ...current, endYear: event.target.value }))
                  }
                />
              </label>
              <label className={styles.inlineLabel}>
                CGPA/Percentage
                <input
                  className={styles.inlineInput}
                  value={educationForm.cgpaOrPercentage}
                  onChange={(event) =>
                    setEducationForm((current) => ({
                      ...current,
                      cgpaOrPercentage: event.target.value,
                    }))
                  }
                />
              </label>
              <div className={styles.inlineActions}>
                <button type="submit" className={styles.inlineActionPrimary}>
                  {editingEducationIndex === null ? "Add Education" : "Update Education"}
                </button>
                <button
                  type="button"
                  className={styles.inlineActionSecondary}
                  onClick={resetEducationForm}
                >
                  Clear
                </button>
              </div>
            </form>
          }
        />
      </div>
      {isParseModalOpen && (
        <div className={styles.parseModalBackdrop} role="dialog" aria-modal="true">
          <div className={styles.parseModal}>
            <div className={styles.parseModalHeader}>
              <h4 className={styles.parseModalTitle}>Parse Resume</h4>
              <button
                type="button"
                className={styles.parseModalClose}
                onClick={closeParseModal}
                disabled={isParsingResume}
              >
                Close
              </button>
            </div>
            <p className={styles.parseModalHint}>
              Upload a PDF or DOCX file to extract structured projects, experiences, achievements,
              and educations.
            </p>
            <label className={styles.inlineLabel}>
              Resume File
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                className={styles.inlineInput}
                onChange={(event) => setSelectedResumeFile(event.target.files?.[0] ?? null)}
                disabled={isParsingResume}
              />
            </label>
            <div className={styles.inlineActions}>
              <button
                type="button"
                className={styles.inlineActionPrimary}
                onClick={() => void parseUploadedResume()}
                disabled={isParsingResume}
              >
                {isParsingResume ? "Parsing..." : "Upload and Parse"}
              </button>
            </div>
            <div className={styles.parseDraftSections}>
              <section className={styles.parseDraftSection}>
                <h5>Projects ({parsedResumeDraft.projects.length})</h5>
                {parsedResumeDraft.projects.length === 0 ? (
                  <p className={styles.stateEmpty}>No parsed projects.</p>
                ) : (
                  <ul className={styles.payloadList}>
                    {parsedResumeDraft.projects.map((item, index) => (
                      <li key={`parsed-project-${index}`} className={styles.payloadItem}>
                        <button
                          type="button"
                          className={styles.parseBoxDeleteButton}
                          aria-label="Delete project box"
                          onClick={() =>
                            setParsedResumeDraft((current) => ({
                              ...current,
                              projects: current.projects.filter((_, itemIndex) => itemIndex !== index),
                            }))
                          }
                        >
                          x
                        </button>
                        <label className={styles.inlineLabel}>
                          Project Name
                          <input
                            className={styles.inlineInput}
                            value={item.name ?? item.projectName ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.projects];
                                next[index] = {
                                  ...next[index],
                                  name: event.target.value,
                                  projectName: event.target.value,
                                };
                                return { ...current, projects: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Description
                          <textarea
                            className={styles.inlineTextarea}
                            value={item.description ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.projects];
                                next[index] = { ...next[index], description: event.target.value };
                                return { ...current, projects: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Tech Stack (comma separated)
                          <input
                            className={styles.inlineInput}
                            value={normalizeArray<string>(item.techStack).join(", ")}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.projects];
                                next[index] = {
                                  ...next[index],
                                  techStack: splitCsv(event.target.value),
                                };
                                return { ...current, projects: next };
                              })
                            }
                          />
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className={styles.parseDraftSection}>
                <h5>Experiences ({parsedResumeDraft.experiences.length})</h5>
                {parsedResumeDraft.experiences.length === 0 ? (
                  <p className={styles.stateEmpty}>No parsed experiences.</p>
                ) : (
                  <ul className={styles.payloadList}>
                    {parsedResumeDraft.experiences.map((item, index) => (
                      <li key={`parsed-exp-${index}`} className={styles.payloadItem}>
                        <button
                          type="button"
                          className={styles.parseBoxDeleteButton}
                          aria-label="Delete experience box"
                          onClick={() =>
                            setParsedResumeDraft((current) => ({
                              ...current,
                              experiences: current.experiences.filter(
                                (_, itemIndex) => itemIndex !== index,
                              ),
                            }))
                          }
                        >
                          x
                        </button>
                        <label className={styles.inlineLabel}>
                          Company
                          <input
                            className={styles.inlineInput}
                            value={item.companyName ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], companyName: event.target.value };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Position
                          <input
                            className={styles.inlineInput}
                            value={item.position ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], position: event.target.value };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Description
                          <textarea
                            className={styles.inlineTextarea}
                            value={item.description ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], description: event.target.value };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Start Date
                          <input
                            className={styles.inlineInput}
                            value={item.startDate ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], startDate: event.target.value };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          End Date
                          <input
                            className={styles.inlineInput}
                            value={item.endDate ?? ""}
                            disabled={Boolean(item.pursuing)}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], endDate: event.target.value || null };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.checkboxLabel}>
                          <input
                            type="checkbox"
                            checked={Boolean(item.pursuing)}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = {
                                  ...next[index],
                                  pursuing: event.target.checked,
                                  endDate: event.target.checked ? null : next[index].endDate ?? "",
                                };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                          Currently working here (`pursuing`)
                        </label>
                        <label className={styles.inlineLabel}>
                          Location
                          <input
                            className={styles.inlineInput}
                            value={item.location ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.experiences];
                                next[index] = { ...next[index], location: event.target.value };
                                return { ...current, experiences: next };
                              })
                            }
                          />
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className={styles.parseDraftSection}>
                <h5>Achievements ({parsedResumeDraft.achievements.length})</h5>
                {parsedResumeDraft.achievements.length === 0 ? (
                  <p className={styles.stateEmpty}>No parsed achievements.</p>
                ) : (
                  <ul className={styles.payloadList}>
                    {parsedResumeDraft.achievements.map((item, index) => (
                      <li key={`parsed-ach-${index}`} className={styles.payloadItem}>
                        <button
                          type="button"
                          className={styles.parseBoxDeleteButton}
                          aria-label="Delete achievement box"
                          onClick={() =>
                            setParsedResumeDraft((current) => ({
                              ...current,
                              achievements: current.achievements.filter(
                                (_, itemIndex) => itemIndex !== index,
                              ),
                            }))
                          }
                        >
                          x
                        </button>
                        <label className={styles.inlineLabel}>
                          Name
                          <input
                            className={styles.inlineInput}
                            value={item.name ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.achievements];
                                next[index] = { ...next[index], name: event.target.value };
                                return { ...current, achievements: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Organisation
                          <input
                            className={styles.inlineInput}
                            value={item.organisation ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.achievements];
                                next[index] = { ...next[index], organisation: event.target.value };
                                return { ...current, achievements: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Date
                          <input
                            className={styles.inlineInput}
                            value={item.date ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.achievements];
                                next[index] = { ...next[index], date: event.target.value };
                                return { ...current, achievements: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Link
                          <input
                            className={styles.inlineInput}
                            value={item.link ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.achievements];
                                next[index] = { ...next[index], link: event.target.value };
                                return { ...current, achievements: next };
                              })
                            }
                          />
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className={styles.parseDraftSection}>
                <h5>Educations ({parsedResumeDraft.educations.length})</h5>
                {parsedResumeDraft.educations.length === 0 ? (
                  <p className={styles.stateEmpty}>No parsed educations.</p>
                ) : (
                  <ul className={styles.payloadList}>
                    {parsedResumeDraft.educations.map((item, index) => (
                      <li key={`parsed-edu-${index}`} className={styles.payloadItem}>
                        <button
                          type="button"
                          className={styles.parseBoxDeleteButton}
                          aria-label="Delete education box"
                          onClick={() =>
                            setParsedResumeDraft((current) => ({
                              ...current,
                              educations: current.educations.filter(
                                (_, itemIndex) => itemIndex !== index,
                              ),
                            }))
                          }
                        >
                          x
                        </button>
                        <label className={styles.inlineLabel}>
                          Degree Name
                          <input
                            className={styles.inlineInput}
                            value={item.degreeName ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = { ...next[index], degreeName: event.target.value };
                                return { ...current, educations: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Location
                          <input
                            className={styles.inlineInput}
                            value={item.location ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = { ...next[index], location: event.target.value };
                                return { ...current, educations: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          Start Year
                          <input
                            className={styles.inlineInput}
                            value={item.startYear ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = { ...next[index], startYear: event.target.value };
                                return { ...current, educations: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.inlineLabel}>
                          End Year
                          <input
                            className={styles.inlineInput}
                            value={item.endYear ?? ""}
                            disabled={Boolean(item.pursuing)}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = { ...next[index], endYear: event.target.value || null };
                                return { ...current, educations: next };
                              })
                            }
                          />
                        </label>
                        <label className={styles.checkboxLabel}>
                          <input
                            type="checkbox"
                            checked={Boolean(item.pursuing)}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = {
                                  ...next[index],
                                  pursuing: event.target.checked,
                                  endYear: event.target.checked ? null : next[index].endYear ?? "",
                                };
                                return { ...current, educations: next };
                              })
                            }
                          />
                          Currently pursuing this education
                        </label>
                        <label className={styles.inlineLabel}>
                          CGPA/Percentage
                          <input
                            className={styles.inlineInput}
                            value={item.cgpaOrPercentage ?? ""}
                            onChange={(event) =>
                              setParsedResumeDraft((current) => {
                                const next = [...current.educations];
                                next[index] = {
                                  ...next[index],
                                  cgpaOrPercentage: event.target.value,
                                };
                                return { ...current, educations: next };
                              })
                            }
                          />
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
            <div className={styles.parseModalFooter}>
              <div className={styles.parseFeedback}>
                {parseError && <p className={styles.parseError}>{parseError}</p>}
                {parseSuccess && <p className={styles.parseSuccess}>{parseSuccess}</p>}
              </div>
              <div className={styles.parseModalActions}>
                <button
                  type="button"
                  className={styles.inlineActionPrimary}
                  onClick={() => void addParsedResumeToSystem()}
                  disabled={isParsingResume || isSavingParsedToSystem}
                >
                  {isSavingParsedToSystem ? "Saving..." : "Add to System"}
                </button>
                <button
                  type="button"
                  className={styles.inlineActionPrimary}
                  onClick={applyParsedResumeToState}
                  disabled={isParsingResume || isSavingParsedToSystem}
                >
                  Apply to Shared State
                </button>
                <button
                  type="button"
                  className={styles.inlineActionSecondary}
                  onClick={closeParseModal}
                  disabled={isParsingResume || isSavingParsedToSystem}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

interface StateSectionProps<TItem> {
  title: string;
  count: number;
  items: TItem[];
  emptyLabel: string;
  renderItem: (item: TItem, index: number) => JSX.Element;
  footer?: ReactNode;
}

function StateSection<TItem>({
  title,
  count,
  items,
  emptyLabel,
  renderItem,
  footer,
}: StateSectionProps<TItem>) {
  const visibleItems = items.slice(0, MAX_VISIBLE_STATE_ITEMS);
  const hiddenCount = Math.max(0, count - visibleItems.length);

  return (
    <article className={styles.stateCard}>
      <header className={styles.stateCardHeader}>
        <span className={styles.stateCardTitle}>{title}</span>
        <span className={styles.stateCardCount}>{count}</span>
      </header>
      {visibleItems.length === 0 ? (
        <p className={styles.stateEmpty}>{emptyLabel}</p>
      ) : (
        <>
          <ul className={styles.payloadList}>
            {visibleItems.map((item, index) => (
              <li key={`${title}-${index}`} className={styles.payloadItem}>
                {renderItem(item, index)}
              </li>
            ))}
          </ul>
          {hiddenCount > 0 && (
            <p className={styles.stateMore}>
              +{hiddenCount} more
            </p>
          )}
        </>
      )}
      {footer}
    </article>
  );
}

function PayloadField({ label, value }: { label: string; value: string | undefined | null }) {
  const normalizedValue = value?.trim();
  return (
    <p className={styles.payloadLine}>
      <span className={styles.payloadLabel}>{label}:</span>{" "}
      <span className={styles.payloadValue}>{normalizedValue || "Not provided"}</span>
    </p>
  );
}

function PayloadTagList({
  label,
  values,
  emptyLabel,
}: {
  label: string;
  values: string[];
  emptyLabel: string;
}) {
  if (values.length === 0) {
    return <PayloadField label={label} value={emptyLabel} />;
  }

  return (
    <div className={styles.payloadTagsWrap}>
      <span className={styles.payloadLabel}>{label}:</span>
      <div className={styles.payloadTags}>
        {values.map((value, index) => (
          <span key={`${label}-${value}-${index}`} className={styles.payloadTag}>
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function ToolCallRenderers({ agentId }: { agentId: string }) {
  useRenderTool(
    {
      name: "*",
      agentId,
      render: ({ name, status, parameters, result, toolCallId }) => {
        const summary = summarizeToolCall(name, status, parameters, result);
        return (
          <ToolRenderDisclosure
            toolCallId={toolCallId}
            title={summary.title}
            body={summary.body}
          />
        );
      },
    },
    [agentId],
  );

  return null;
}

function summarizeToolCall(
  name: string,
  status: "inProgress" | "executing" | "complete",
  parameters: unknown,
  result: string | undefined,
): { title: string; body: string } {
  const statusPrefix =
    status === "complete"
      ? "Completed"
      : status === "executing"
        ? "Running"
        : "Preparing";

  if (name === "add_project_to_resume") {
    const payload = asRecord(parameters);
    const projects = normalizeArray<Record<string, unknown>>(payload.projects);
    const project = projects.length > 0 ? asRecord(projects[0]) : asRecord(payload.project);
    const projectName = asString(project.projectName) ?? "project";
    return {
      title: `${statusPrefix}: add_project_to_resume`,
      body:
        status === "complete"
          ? `Updated shared resume projects (${projects.length || 1}).`
          : `Updating shared state for project "${projectName}".`,
    };
  }

  if (name === "add_experience_to_resume") {
    const payload = asRecord(parameters);
    const experiences = normalizeArray<Record<string, unknown>>(payload.experiences);
    const experience = experiences.length > 0 ? asRecord(experiences[0]) : asRecord(payload.experience);
    const companyName = asString(experience.companyName) ?? "company";
    const position = asString(experience.position) ?? "role";
    return {
      title: `${statusPrefix}: add_experience_to_resume`,
      body:
        status === "complete"
          ? `Updated shared resume experiences (${experiences.length || 1}).`
          : `Updating shared state for experience "${position} @ ${companyName}".`,
    };
  }

  if (name === "add_achievement_to_resume") {
    const payload = asRecord(parameters);
    const achievements = normalizeArray<Record<string, unknown>>(payload.achievements);
    const achievement =
      achievements.length > 0 ? asRecord(achievements[0]) : asRecord(payload.achievement);
    const achievementName = asString(achievement.name) ?? "achievement";
    return {
      title: `${statusPrefix}: add_achievement_to_resume`,
      body:
        status === "complete"
          ? `Updated shared resume achievements (${achievements.length || 1}).`
          : `Updating shared state for achievement "${achievementName}".`,
    };
  }

  if (name === "add_education_to_resume") {
    const payload = asRecord(parameters);
    const educations = normalizeArray<Record<string, unknown>>(payload.educations);
    const education = educations.length > 0 ? asRecord(educations[0]) : asRecord(payload.education);
    const degreeName = asString(education.degreeName) ?? "education";
    return {
      title: `${statusPrefix}: add_education_to_resume`,
      body:
        status === "complete"
          ? `Updated shared resume educations (${educations.length || 1}).`
          : `Updating shared state for education "${degreeName}".`,
    };
  }

  if (name === "add_summary") {
    const payload = asRecord(parameters);
    const summary = asString(payload.summary) ?? "summary";
    return {
      title: `${statusPrefix}: add_summary`,
      body:
        status === "complete"
          ? `Updated shared resume summary to "${summary}".`
          : `Updating shared resume summary.`,
    };
  }

  if (name === "add_profile") {
    const payload = asRecord(parameters);
    const profile = asRecord(payload.profile);
    const profileName = asString(profile.name) ?? "profile";
    const profileRole = asString(profile.role);
    return {
      title: `${statusPrefix}: add_profile`,
      body:
        status === "complete"
          ? `Updated shared resume profile for "${profileName}${profileRole ? ` (${profileRole})` : ""}".`
          : `Updating shared resume profile for "${profileName}".`,
    };
  }

  if (name === "add_skills") {
    const payload = asRecord(parameters);
    const skills = normalizeArray<string>(payload.skills);
    return {
      title: `${statusPrefix}: add_skills`,
      body:
        status === "complete"
          ? `Updated shared resume skills (${skills.length}).`
          : "Updating shared resume skills.",
    };
  }

  if (status === "complete") {
    const normalizedResult = result?.trim();
    return {
      title: `${statusPrefix}: ${name}`,
      body: normalizedResult || "Tool call completed.",
    };
  }

  return {
    title: `${statusPrefix}: ${name}`,
    body: `Executing ${name} with ${summarizeParameters(parameters)}.`,
  };
}

function summarizeParameters(parameters: unknown): string {
  if (!parameters || typeof parameters !== "object") {
    return "no parameters";
  }
  const entries = Object.entries(parameters as Record<string, unknown>);
  if (entries.length === 0) {
    return "no parameters";
  }
  const keys = entries.map(([key]) => key);
  return `${keys.slice(0, 3).join(", ")}${keys.length > 3 ? "..." : ""}`;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed || undefined;
}

function ToolRenderDisclosure({
  toolCallId,
  title,
  body,
}: {
  toolCallId: string;
  title: string;
  body: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={styles.toolCallRenderCard} key={toolCallId}>
      <button
        type="button"
        className={styles.toolCallRenderToggle}
        onClick={() => setIsExpanded((value) => !value)}
        aria-expanded={isExpanded}
      >
        <span className={styles.toolCallRenderTitle}>{title}</span>
        <span className={styles.toolCallRenderChevron}>{isExpanded ? "▲" : "▼"}</span>
      </button>
      {isExpanded && <p className={styles.toolCallRenderBody}>{body}</p>}
    </div>
  );
}

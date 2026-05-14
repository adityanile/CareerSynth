"use client";

import { FormEvent, ReactNode, useState } from "react";
import { CopilotChat, Thread, useAgent, useThreads } from "@copilotkit/react-core/v2";
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

interface ResumeState {
  projects?: ProjectStateItem[];
  experiences?: ExperienceStateItem[];
  achievements?: AchievementStateItem[];
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

function ResumeStatePanel({ agentId }: { agentId: string }) {
  const { agent } = useAgent({ agentId });
  const state = (agent.state ?? {}) as ResumeState;
  const projects = normalizeArray<ProjectStateItem>(state.projects);
  const experiences = normalizeArray<ExperienceStateItem>(state.experiences);
  const achievements = normalizeArray<AchievementStateItem>(state.achievements);
  const hasAnyState = projects.length > 0 || experiences.length > 0 || achievements.length > 0;
  const [editingProjectIndex, setEditingProjectIndex] = useState<number | null>(null);
  const [editingExperienceIndex, setEditingExperienceIndex] = useState<number | null>(null);
  const [editingAchievementIndex, setEditingAchievementIndex] = useState<number | null>(null);
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

  const applyStatePatch = (patch: Partial<ResumeState>) => {
    agent.setState({
      ...((agent.state ?? {}) as Record<string, unknown>),
      ...patch,
    });
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

  return (
    <aside className={styles.resumeStatePanel}>
      <div className={styles.resumeStateHeader}>
        <h3>Shared Resume State</h3>
        {!hasAnyState && <span className={styles.stateHint}>No snapshot loaded yet.</span>}
      </div>

      <div className={styles.stateGrid}>
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
      </div>
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

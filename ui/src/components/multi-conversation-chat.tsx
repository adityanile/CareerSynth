"use client";

import { FormEvent, useMemo, useState } from "react";
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
      <header className={styles.chatHeader}>
        <h2>Conversation</h2>
        <p className={styles.headerNotice}>
          Add a Copilot public key to enable multi-conversation history.
        </p>
      </header>
      <div className={styles.chatBody}>
        <div className={styles.chatWorkspace}>
          <ResumeStatePanel agentId={agentId} />
          <CopilotChat
            agentId={agentId}
            chatView={styles.chatView}
            labels={{
              chatInputPlaceholder: "Ask your agent anything...",
            }}
          />
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

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId),
    [activeThreadId, threads],
  );

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
        <header className={styles.chatHeader}>
          <h2>{activeThread?.name ?? "New conversation"}</h2>
        </header>
        <div className={styles.chatBody}>
          <div className={styles.chatWorkspace}>
            <ResumeStatePanel agentId={agentId} />
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
          renderItem={(item) => (
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
            </>
          )}
        />
        <StateSection
          title="Experiences"
          count={experiences.length}
          emptyLabel="No experiences"
          items={experiences}
          renderItem={(item) => (
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
            </>
          )}
        />
        <StateSection
          title="Achievements"
          count={achievements.length}
          emptyLabel="No achievements"
          items={achievements}
          renderItem={(item) => (
            <>
              <p className={styles.payloadTitle}>{item.name ?? "Untitled achievement"}</p>
              <PayloadField label="Organisation" value={item.organisation} />
              <PayloadField label="Date" value={item.date} />
              <PayloadField label="Link" value={item.link} />
            </>
          )}
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
}

function StateSection<TItem>({
  title,
  count,
  items,
  emptyLabel,
  renderItem,
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

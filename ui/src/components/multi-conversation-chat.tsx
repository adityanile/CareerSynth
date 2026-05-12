"use client";

import { FormEvent, useMemo, useState } from "react";
import { CopilotChat, Thread, useThreads } from "@copilotkit/react-core/v2";
import styles from "./multi-conversation-chat.module.css";

const THREAD_PAGE_SIZE = 25;

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
        <CopilotChat
          agentId={agentId}
          chatView={styles.chatView}
          labels={{
            chatInputPlaceholder: "Ask your agent anything...",
          }}
        />
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
          <CopilotChat
            agentId={agentId}
            threadId={activeThreadId}
            chatView={styles.chatView}
            labels={{
              chatInputPlaceholder: "Ask your agent anything...",
            }}
          />
        </div>
      </main>
    </div>
  );
}

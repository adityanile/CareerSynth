"use client";

import { FormEvent, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  getEntraAccessToken,
  subscribeToEntraAccessToken,
} from "@/lib/entra-token-store";
import styles from "./profile-resource-manager.module.css";

type ResourceTab = "projects" | "experiences" | "achievements";

interface ProjectItem {
  id: number;
  name: string;
  techStack: string[];
  urls: string[];
  description: string;
  tags: string[];
}

interface ExperienceItem {
  id: number;
  companyName: string;
  startDate: string;
  endDate: string | null;
  position: string;
  description: string;
  location: string;
}

interface AchievementItem {
  id: number;
  name: string;
  link: string;
  organisation: string;
  date: string;
}

interface ItemsResponse<TItem> {
  items: TItem[];
}

interface ProjectForm {
  name: string;
  description: string;
  techStack: string;
  urls: string;
  tags: string;
}

interface ExperienceForm {
  companyName: string;
  startDate: string;
  endDate: string;
  position: string;
  description: string;
  location: string;
}

interface AchievementForm {
  name: string;
  link: string;
  organisation: string;
  date: string;
}

const emptyProjectForm: ProjectForm = {
  name: "",
  description: "",
  techStack: "",
  urls: "",
  tags: "",
};

const emptyExperienceForm: ExperienceForm = {
  companyName: "",
  startDate: "",
  endDate: "",
  position: "",
  description: "",
  location: "",
};

const emptyAchievementForm: AchievementForm = {
  name: "",
  link: "",
  organisation: "",
  date: "",
};

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

async function parseError(response: Response): Promise<string> {
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

async function request<TResponse>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<TResponse> {
  const response = await fetch(`/api/backend/${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }
  return (await response.json()) as TResponse;
}

export function ProfileResourceManager() {
  const accessToken = useSyncExternalStore(
    subscribeToEntraAccessToken,
    getEntraAccessToken,
    () => null,
  );
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<ResourceTab>("projects");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [experiences, setExperiences] = useState<ExperienceItem[]>([]);
  const [achievements, setAchievements] = useState<AchievementItem[]>([]);

  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);
  const [editingExperienceId, setEditingExperienceId] = useState<number | null>(null);
  const [editingAchievementId, setEditingAchievementId] = useState<number | null>(null);

  const [projectForm, setProjectForm] = useState<ProjectForm>(emptyProjectForm);
  const [experienceForm, setExperienceForm] = useState<ExperienceForm>(emptyExperienceForm);
  const [achievementForm, setAchievementForm] = useState<AchievementForm>(emptyAchievementForm);

  const totalItems = projects.length + experiences.length + achievements.length;

  const loadAllResources = async (token: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [projectsResponse, experiencesResponse, achievementsResponse] =
        await Promise.all([
          request<ItemsResponse<ProjectItem>>("projects", token, { method: "GET" }),
          request<ItemsResponse<ExperienceItem>>("experiences", token, { method: "GET" }),
          request<ItemsResponse<AchievementItem>>("achievements", token, { method: "GET" }),
        ]);
      setProjects(projectsResponse.items ?? []);
      setExperiences(experiencesResponse.items ?? []);
      setAchievements(achievementsResponse.items ?? []);
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Failed to load resources.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    const timerId = window.setTimeout(() => {
      void loadAllResources(accessToken);
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [accessToken]);

  const tabs = useMemo(
    () => [
      { key: "projects", label: `Projects (${projects.length})` },
      { key: "experiences", label: `Experiences (${experiences.length})` },
      { key: "achievements", label: `Achievements (${achievements.length})` },
    ] as const,
    [projects.length, experiences.length, achievements.length],
  );

  const resetProjectForm = () => {
    setEditingProjectId(null);
    setProjectForm(emptyProjectForm);
  };

  const resetExperienceForm = () => {
    setEditingExperienceId(null);
    setExperienceForm(emptyExperienceForm);
  };

  const resetAchievementForm = () => {
    setEditingAchievementId(null);
    setAchievementForm(emptyAchievementForm);
  };

  const submitProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const payload = {
      name: projectForm.name.trim(),
      description: projectForm.description.trim(),
      techStack: splitCsv(projectForm.techStack),
      urls: splitCsv(projectForm.urls),
      tags: splitCsv(projectForm.tags),
    };
    if (!payload.name || !payload.description) {
      setError("Project name and description are required.");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      if (editingProjectId === null) {
        const created = await request<ProjectItem>("projects", accessToken, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setProjects((current) => [created, ...current]);
      } else {
        const updated = await request<ProjectItem>(`projects/${editingProjectId}`, accessToken, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        setProjects((current) =>
          current.map((item) => (item.id === editingProjectId ? updated : item)),
        );
      }
      resetProjectForm();
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Failed to save project.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const submitExperience = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const payload = {
      companyName: experienceForm.companyName.trim(),
      startDate: experienceForm.startDate.trim(),
      endDate: experienceForm.endDate.trim() || null,
      position: experienceForm.position.trim(),
      description: experienceForm.description.trim(),
      location: experienceForm.location.trim(),
    };
    if (!payload.companyName || !payload.startDate || !payload.position || !payload.description || !payload.location) {
      setError("Experience company, start date, position, description and location are required.");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      if (editingExperienceId === null) {
        const created = await request<ExperienceItem>("experiences", accessToken, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setExperiences((current) => [created, ...current]);
      } else {
        const updated = await request<ExperienceItem>(
          `experiences/${editingExperienceId}`,
          accessToken,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        );
        setExperiences((current) =>
          current.map((item) => (item.id === editingExperienceId ? updated : item)),
        );
      }
      resetExperienceForm();
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Failed to save experience.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const submitAchievement = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const payload = {
      name: achievementForm.name.trim(),
      link: achievementForm.link.trim(),
      organisation: achievementForm.organisation.trim(),
      date: achievementForm.date.trim(),
    };
    if (!payload.name || !payload.link || !payload.organisation || !payload.date) {
      setError("Achievement name, link, organisation and date are required.");
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      if (editingAchievementId === null) {
        const created = await request<AchievementItem>("achievements", accessToken, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setAchievements((current) => [created, ...current]);
      } else {
        const updated = await request<AchievementItem>(
          `achievements/${editingAchievementId}`,
          accessToken,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        );
        setAchievements((current) =>
          current.map((item) => (item.id === editingAchievementId ? updated : item)),
        );
      }
      resetAchievementForm();
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Failed to save achievement.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const deleteResource = async (tab: ResourceTab, id: number) => {
    if (!accessToken) {
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      await request<void>(`${tab}/${id}`, accessToken, { method: "DELETE" });
      if (tab === "projects") {
        setProjects((current) => current.filter((item) => item.id !== id));
      } else if (tab === "experiences") {
        setExperiences((current) => current.filter((item) => item.id !== id));
      } else {
        setAchievements((current) => current.filter((item) => item.id !== id));
      }
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "Failed to delete item.";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!accessToken) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        className={styles.launcher}
        onClick={() => setIsOpen(true)}
      >
        CareerSynth Database State
        <span className={styles.badge}>{totalItems}</span>
      </button>

      {isOpen && (
        <>
          <div
            className={styles.overlay}
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <section className={styles.modal}>
            <header className={styles.header}>
              <div>
                <h2 className={styles.title}>CareerSynth Database State</h2>
                <p className={styles.subtitle}>
                  Backend CRUD for projects, experiences, and achievements.
                </p>
              </div>
              <button
                type="button"
                className={styles.closeButton}
                onClick={() => setIsOpen(false)}
              >
                Close
              </button>
            </header>

            {error && <p className={styles.error}>{error}</p>}

            <div className={styles.tabs}>
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  className={`${styles.tabButton} ${activeTab === tab.key ? styles.tabButtonActive : ""}`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => void loadAllResources(accessToken)}
                disabled={isLoading || isSaving}
              >
                {isLoading ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            <div className={styles.content}>
              {activeTab === "projects" && (
                <>
                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>Projects</h3>
                    {projects.length === 0 ? (
                      <p className={styles.empty}>No projects found.</p>
                    ) : (
                      <ul className={styles.list}>
                        {projects.map((item) => (
                          <li key={item.id} className={styles.item}>
                            <p className={styles.itemTitle}>{item.name}</p>
                            <p className={styles.itemLine}>{item.description}</p>
                            <p className={styles.itemLine}>Tech: {item.techStack.join(", ") || "N/A"}</p>
                            <div className={styles.actions}>
                              <button
                                type="button"
                                className={styles.button}
                                onClick={() => {
                                  setEditingProjectId(item.id);
                                  setProjectForm({
                                    name: item.name,
                                    description: item.description,
                                    techStack: item.techStack.join(", "),
                                    urls: item.urls.join(", "),
                                    tags: item.tags.join(", "),
                                  });
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className={`${styles.button} ${styles.deleteButton}`}
                                onClick={() => void deleteResource("projects", item.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>

                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>
                      {editingProjectId === null ? "Add Project" : "Edit Project"}
                    </h3>
                    <form className={styles.form} onSubmit={(event) => void submitProject(event)}>
                      <label className={styles.label}>
                        Name
                        <input
                          className={styles.input}
                          value={projectForm.name}
                          onChange={(event) =>
                            setProjectForm((current) => ({ ...current, name: event.target.value }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Description
                        <textarea
                          className={styles.textarea}
                          value={projectForm.description}
                          onChange={(event) =>
                            setProjectForm((current) => ({
                              ...current,
                              description: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Tech Stack (comma separated)
                        <input
                          className={styles.input}
                          value={projectForm.techStack}
                          onChange={(event) =>
                            setProjectForm((current) => ({
                              ...current,
                              techStack: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        URLs (comma separated)
                        <input
                          className={styles.input}
                          value={projectForm.urls}
                          onChange={(event) =>
                            setProjectForm((current) => ({ ...current, urls: event.target.value }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Tags (comma separated)
                        <input
                          className={styles.input}
                          value={projectForm.tags}
                          onChange={(event) =>
                            setProjectForm((current) => ({ ...current, tags: event.target.value }))
                          }
                        />
                      </label>
                      <div className={styles.formActions}>
                        <button type="submit" className={styles.primaryButton} disabled={isSaving}>
                          {isSaving ? "Saving..." : editingProjectId === null ? "Add" : "Update"}
                        </button>
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          onClick={resetProjectForm}
                          disabled={isSaving}
                        >
                          Clear
                        </button>
                      </div>
                    </form>
                  </article>
                </>
              )}

              {activeTab === "experiences" && (
                <>
                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>Experiences</h3>
                    {experiences.length === 0 ? (
                      <p className={styles.empty}>No experiences found.</p>
                    ) : (
                      <ul className={styles.list}>
                        {experiences.map((item) => (
                          <li key={item.id} className={styles.item}>
                            <p className={styles.itemTitle}>
                              {item.position} @ {item.companyName}
                            </p>
                            <p className={styles.itemLine}>
                              {item.startDate} - {item.endDate ?? "Present"} | {item.location}
                            </p>
                            <p className={styles.itemLine}>{item.description}</p>
                            <div className={styles.actions}>
                              <button
                                type="button"
                                className={styles.button}
                                onClick={() => {
                                  setEditingExperienceId(item.id);
                                  setExperienceForm({
                                    companyName: item.companyName,
                                    startDate: item.startDate,
                                    endDate: item.endDate ?? "",
                                    position: item.position,
                                    description: item.description,
                                    location: item.location,
                                  });
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className={`${styles.button} ${styles.deleteButton}`}
                                onClick={() => void deleteResource("experiences", item.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>

                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>
                      {editingExperienceId === null ? "Add Experience" : "Edit Experience"}
                    </h3>
                    <form className={styles.form} onSubmit={(event) => void submitExperience(event)}>
                      <label className={styles.label}>
                        Company
                        <input
                          className={styles.input}
                          value={experienceForm.companyName}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              companyName: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Position
                        <input
                          className={styles.input}
                          value={experienceForm.position}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              position: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Description
                        <textarea
                          className={styles.textarea}
                          value={experienceForm.description}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              description: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Start Date
                        <input
                          className={styles.input}
                          value={experienceForm.startDate}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              startDate: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        End Date (optional)
                        <input
                          className={styles.input}
                          value={experienceForm.endDate}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              endDate: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Location
                        <input
                          className={styles.input}
                          value={experienceForm.location}
                          onChange={(event) =>
                            setExperienceForm((current) => ({
                              ...current,
                              location: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <div className={styles.formActions}>
                        <button type="submit" className={styles.primaryButton} disabled={isSaving}>
                          {isSaving ? "Saving..." : editingExperienceId === null ? "Add" : "Update"}
                        </button>
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          onClick={resetExperienceForm}
                          disabled={isSaving}
                        >
                          Clear
                        </button>
                      </div>
                    </form>
                  </article>
                </>
              )}

              {activeTab === "achievements" && (
                <>
                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>Achievements</h3>
                    {achievements.length === 0 ? (
                      <p className={styles.empty}>No achievements found.</p>
                    ) : (
                      <ul className={styles.list}>
                        {achievements.map((item) => (
                          <li key={item.id} className={styles.item}>
                            <p className={styles.itemTitle}>{item.name}</p>
                            <p className={styles.itemLine}>{item.organisation}</p>
                            <p className={styles.itemLine}>{item.date}</p>
                            <p className={styles.itemLine}>{item.link}</p>
                            <div className={styles.actions}>
                              <button
                                type="button"
                                className={styles.button}
                                onClick={() => {
                                  setEditingAchievementId(item.id);
                                  setAchievementForm({
                                    name: item.name,
                                    link: item.link,
                                    organisation: item.organisation,
                                    date: item.date,
                                  });
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className={`${styles.button} ${styles.deleteButton}`}
                                onClick={() => void deleteResource("achievements", item.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>

                  <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>
                      {editingAchievementId === null ? "Add Achievement" : "Edit Achievement"}
                    </h3>
                    <form className={styles.form} onSubmit={(event) => void submitAchievement(event)}>
                      <label className={styles.label}>
                        Name
                        <input
                          className={styles.input}
                          value={achievementForm.name}
                          onChange={(event) =>
                            setAchievementForm((current) => ({ ...current, name: event.target.value }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Link
                        <input
                          className={styles.input}
                          value={achievementForm.link}
                          onChange={(event) =>
                            setAchievementForm((current) => ({ ...current, link: event.target.value }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Organisation
                        <input
                          className={styles.input}
                          value={achievementForm.organisation}
                          onChange={(event) =>
                            setAchievementForm((current) => ({
                              ...current,
                              organisation: event.target.value,
                            }))
                          }
                        />
                      </label>
                      <label className={styles.label}>
                        Date
                        <input
                          className={styles.input}
                          value={achievementForm.date}
                          onChange={(event) =>
                            setAchievementForm((current) => ({ ...current, date: event.target.value }))
                          }
                        />
                      </label>
                      <div className={styles.formActions}>
                        <button type="submit" className={styles.primaryButton} disabled={isSaving}>
                          {isSaving ? "Saving..." : editingAchievementId === null ? "Add" : "Update"}
                        </button>
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          onClick={resetAchievementForm}
                          disabled={isSaving}
                        >
                          Clear
                        </button>
                      </div>
                    </form>
                  </article>
                </>
              )}
            </div>
          </section>
        </>
      )}
    </>
  );
}

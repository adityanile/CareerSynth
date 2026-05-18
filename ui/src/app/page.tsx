import Link from "next/link";
import styles from "./page.module.css";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function Home() {
  const { userId } = await auth();
  const isSignedIn = Boolean(userId);

  if (isSignedIn) {
    redirect("/workspace");
  }

  return (
    <main className={styles.page}>
      <div className={styles.backgroundGlow} aria-hidden="true" />
      <header className={styles.navbar}>
        <div className={styles.brand}>CareerSynth</div>
        <div className={styles.navActions}>
          {isSignedIn ? (
            <Link className={styles.secondaryButton} href="/workspace">
              Open Workspace
            </Link>
          ) : (
            <Link className={styles.secondaryButton} href="/sign-in">
              Sign In
            </Link>
          )}
        </div>
      </header>

      <section className={styles.hero}>
        <p className={styles.kicker}>AI Career Intelligence</p>
        <h1 className={styles.title}>
          The career operating system that remembers your entire professional journey.
        </h1>
        <p className={styles.subtitle}>
          CareerSynth is more than a resume builder. It continuously learns from every interaction,
          maintains a structured memory of your projects, achievements, skills, and experience, and
          delivers personalized career assistance on demand.
        </p>
        <div className={styles.heroActions}>
          {isSignedIn ? (
            <Link className={styles.primaryButton} href="/workspace">
              Continue to Workspace
            </Link>
          ) : (
            <Link className={styles.primaryButton} href="/sign-in">
              Start Building
            </Link>
          )}
          <a className={styles.ghostButton} href="#how-it-works">
            See How It Works
          </a>
        </div>
      </section>

      <section className={styles.metrics}>
        <article className={styles.metricCard}>
          <p className={styles.metricValue}>1</p>
          <p className={styles.metricLabel}>
            Unified career memory across projects, achievements, skills, experience, and education
          </p>
        </article>
        <article className={styles.metricCard}>
          <p className={styles.metricValue}>2</p>
          <p className={styles.metricLabel}>
            AI extraction from existing resumes into editable, structured, production-ready data
          </p>
        </article>
        <article className={styles.metricCard}>
          <p className={styles.metricValue}>3</p>
          <p className={styles.metricLabel}>
            End-to-end execution through conversation: profile optimization, resume assets, and guidance
          </p>
        </article>
      </section>

      <section id="how-it-works" className={styles.section}>
        <h2 className={styles.sectionTitle}>How CareerSynth Works</h2>
        <div className={styles.steps}>
          <article className={styles.stepCard}>
            <span className={styles.stepIndex}>01</span>
            <h3>Ingest</h3>
            <p>Upload your current resume once. The system identifies and structures your complete career information automatically.</p>
          </article>
          <article className={styles.stepCard}>
            <span className={styles.stepIndex}>02</span>
            <h3>Refine</h3>
            <p>Use interactive live-edit panels to control exactly what goes into your resume and professional profile.</p>
          </article>
          <article className={styles.stepCard}>
            <span className={styles.stepIndex}>03</span>
            <h3>Persist</h3>
            <p>Save curated data to your long-term system memory so every future output becomes more personalized and accurate.</p>
          </article>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>What You Control</h2>
        <div className={styles.featureGrid}>
          <article className={styles.featureCard}>
            <h3>Persistent Professional Memory</h3>
            <p>We retain your evolving career context, so you never restart from zero in each session.</p>
          </article>
          <article className={styles.featureCard}>
            <h3>Conversation-Driven Control</h3>
            <p>The chat interface can operate the complete system. Ask naturally, and the workflow executes end-to-end.</p>
          </article>
          <article className={styles.featureCard}>
            <h3>Individualized Career Consultation</h3>
            <p>Get person-specific guidance on role fit, profile strength, and strategic next steps.</p>
          </article>
          <article className={styles.featureCard}>
            <h3>LinkedIn and Profile Optimization</h3>
            <p>Improve your public professional presence using context-aware recommendations based on your own background.</p>
          </article>
          <article className={styles.featureCard}>
            <h3>Resume + Cover Letter Generation</h3>
            <p>Create tailored assets quickly, including why you are a strong fit for specific opportunities.</p>
          </article>
          <article className={styles.featureCard}>
            <h3>ATS Validation Across Sources</h3>
            <p>Generate and validate resumes from multiple data sources in one workflow, with ATS-oriented checks.</p>
          </article>
        </div>
      </section>

      <footer className={styles.footer}>
        <p>
          CareerSynth · Created by Aditya Nile ·{" "}
          <a
            href="https://github.com/adityanile/"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </p>
        {isSignedIn && <Link href="/workspace">Go to Workspace</Link>}
      </footer>
    </main>
  );
}

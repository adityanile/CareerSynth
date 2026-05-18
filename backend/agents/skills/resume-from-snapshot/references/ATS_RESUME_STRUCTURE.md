%===========================================================
% ATS-FRIENDLY RESUME TEMPLATE
% Inspired by ResumeSkills by Paramchoudhary
% Clean, single-column, keyword-optimized LaTeX Resume
%===========================================================

\documentclass[letterpaper,11pt]{article}

% ---- PACKAGES ----
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{multicol}
\usepackage{fontenc}
\usepackage[T1]{fontenc}
\input{glyphtounicode}

% ---- PAGE SETUP ----
\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins for ATS readability
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% ---- SECTION FORMATTING ----
% ATS-friendly: bold, uppercase section titles with a rule
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure PDF is machine-readable (critical for ATS)
\pdfgentounicode=1

% ---- CUSTOM COMMANDS ----

% Resume header item
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

% Job/Project heading: Role | Company | Location | Date
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

% Project / Education sub-item (no italic subtitle)
\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

% Project entry
\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}


%===========================================================
%                    RESUME STARTS HERE
%===========================================================
\begin{document}

%------------------------------------------------------------
%  HEADER — Name, Contact, Links
%------------------------------------------------------------
\begin{center}
    {\Huge \scshape \textbf{Your Full Name}} \\ \vspace{4pt}
    \small
    +91-XXXXX-XXXXX $|$
    \href{mailto:your.email@gmail.com}{\underline{your.email@gmail.com}} $|$
    \href{https://linkedin.com/in/yourprofile}{\underline{linkedin.com/in/yourprofile}} $|$
    \href{https://github.com/yourusername}{\underline{github.com/yourusername}} $|$
    Pune, Maharashtra, India
\end{center}

%------------------------------------------------------------
%  PROFESSIONAL SUMMARY  (optional but ATS-friendly)
%------------------------------------------------------------
\section{Professional Summary}
  \small{
    Results-driven Software Engineer with 3+ years of experience building scalable web applications using React, Node.js, and AWS. Proven track record of improving system performance by 40\% and delivering projects on time. Seeking to leverage expertise in full-stack development and cloud infrastructure to drive impactful solutions at a forward-thinking organization.
  }
  \vspace{2pt}

%------------------------------------------------------------
%  SKILLS — keyword-dense for ATS parsing
%------------------------------------------------------------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: Python, JavaScript, TypeScript, Java, SQL, Bash} \\
     \textbf{Frameworks \& Libraries}{: React.js, Node.js, Express.js, Django, Spring Boot, FastAPI} \\
     \textbf{Databases}{: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch} \\
     \textbf{Cloud \& DevOps}{: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes, GitHub Actions, CI/CD} \\
     \textbf{Tools}{: Git, JIRA, Postman, Figma, VS Code, IntelliJ IDEA} \\
     \textbf{Concepts}{: REST APIs, Microservices, Agile/Scrum, System Design, Data Structures \& Algorithms}
    }}
 \end{itemize}

%------------------------------------------------------------
%  WORK EXPERIENCE — STAR-method bullets with metrics
%------------------------------------------------------------
\section{Work Experience}
  \resumeSubHeadingListStart

    % ---- Job 1 ----
    \resumeSubheading
      {Senior Software Engineer}{Jan 2023 -- Present}
      {Tech Company Name}{Pune, Maharashtra, India}
      \resumeItemListStart
        \resumeItem{Led development of a microservices-based order management system serving \textbf{500K+ daily active users}, reducing latency by \textbf{35\%} through Redis caching and query optimization.}
        \resumeItem{Architected and deployed a real-time notification service using AWS SNS/SQS, processing \textbf{2M+ events/day} with 99.9\% uptime SLA.}
        \resumeItem{Mentored a team of 4 junior engineers through code reviews, pair programming, and weekly knowledge sessions, improving team velocity by \textbf{25\%}.}
        \resumeItem{Collaborated with product and design teams to deliver \textbf{12 major features} on schedule, contributing to a \textbf{20\% increase} in user retention.}
        \resumeItem{Reduced cloud infrastructure costs by \textbf{\$40K/year} by right-sizing EC2 instances and implementing auto-scaling policies.}
      \resumeItemListEnd

    % ---- Job 2 ----
    \resumeSubheading
      {Software Engineer}{Jul 2021 -- Dec 2022}
      {Previous Company Name}{Bangalore, Karnataka, India}
      \resumeItemListStart
        \resumeItem{Built RESTful APIs in Node.js/Express serving \textbf{300+ enterprise clients}, achieving sub-100ms response times at P95.}
        \resumeItem{Migrated legacy monolith to React.js SPA, improving page load speed by \textbf{60\%} and increasing user engagement by \textbf{18\%}.}
        \resumeItem{Implemented automated CI/CD pipelines with GitHub Actions, cutting deployment time from \textbf{2 hours to 15 minutes}.}
        \resumeItem{Wrote comprehensive unit and integration tests (Jest, Mocha) achieving \textbf{85\%+ code coverage} across all services.}
      \resumeItemListEnd

    % ---- Job 3 (Internship) ----
    \resumeSubheading
      {Software Development Intern}{Jan 2021 -- Jun 2021}
      {Internship Company Name}{Remote}
      \resumeItemListStart
        \resumeItem{Developed and shipped \textbf{3 full-stack features} using Django + React, used by \textbf{10,000+ students} on the e-learning platform.}
        \resumeItem{Optimized database queries in PostgreSQL, reducing average query execution time by \textbf{45\%}.}
      \resumeItemListEnd

  \resumeSubHeadingListEnd

%------------------------------------------------------------
%  EDUCATION
%------------------------------------------------------------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Bachelor of Engineering in Computer Science}{Jul 2017 -- May 2021}
      {University / College Name}{Pune, Maharashtra, India}
      \resumeItemListStart
        \resumeItem{CGPA: 8.5 / 10.0}
        \resumeItem{Relevant Coursework: Data Structures \& Algorithms, Operating Systems, Database Management Systems, Computer Networks, Software Engineering}
      \resumeItemListEnd
  \resumeSubHeadingListEnd

%------------------------------------------------------------
%  PROJECTS — with tech stack and measurable impact
%------------------------------------------------------------
\section{Projects}
    \resumeSubHeadingListStart

      \resumeProjectHeading
        {\textbf{E-Commerce Platform} $|$ \emph{React, Node.js, MongoDB, Stripe, AWS S3}}{Mar 2023 -- May 2023}
        \resumeItemListStart
          \resumeItem{Built a full-stack e-commerce application with product catalog, cart management, Stripe payment integration, and order tracking for \textbf{1,000+ test users}.}
          \resumeItem{Implemented JWT-based authentication, role-based access control, and OAuth 2.0 social login.}
          \resumeItem{Deployed on AWS with auto-scaling; handles \textbf{500 concurrent users} with average response time under \textbf{200ms}.}
        \resumeItemListEnd

      \resumeProjectHeading
        {\textbf{Real-Time Chat Application} $|$ \emph{React, Socket.io, Node.js, Redis, PostgreSQL}}{Nov 2022 -- Jan 2023}
        \resumeItemListStart
          \resumeItem{Engineered a WebSocket-based chat app supporting \textbf{1,000+ concurrent connections} with message persistence and read receipts.}
          \resumeItem{Used Redis Pub/Sub for horizontal scaling across multiple server instances; reduced message delivery latency to under \textbf{50ms}.}
        \resumeItemListEnd

      \resumeProjectHeading
        {\textbf{ML-Powered Resume Screener} $|$ \emph{Python, FastAPI, scikit-learn, Docker, React}}{Aug 2022 -- Oct 2022}
        \resumeItemListStart
          \resumeItem{Built an NLP-based resume screening tool achieving \textbf{87\% accuracy} in classifying candidates against job descriptions.}
          \resumeItem{Containerized with Docker and deployed CI/CD pipeline reducing release cycles to \textbf{daily deployments}.}
        \resumeItemListEnd

    \resumeSubHeadingListEnd

%------------------------------------------------------------
%  CERTIFICATIONS  (ATS picks these up as keywords)
%------------------------------------------------------------
\section{Certifications}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
      \textbf{AWS Certified Solutions Architect -- Associate} (Amazon Web Services, 2023) \\
      \textbf{Google Professional Data Engineer} (Google Cloud, 2022) \\
      \textbf{Meta Front-End Developer Certificate} (Coursera, 2022)
    }}
 \end{itemize}

%------------------------------------------------------------
%  ACHIEVEMENTS & AWARDS  (optional section)
%------------------------------------------------------------
\section{Achievements}
  \resumeSubHeadingListStart
    \resumeSubItem{Winner, \textbf{HackIndia 2022} national hackathon (Top 5 out of 800+ teams) -- built a fintech micro-lending solution.}
    \resumeSubItem{Ranked in top \textbf{5\%} on LeetCode with 400+ problems solved (DSA); handle: \href{https://leetcode.com/yourusername}{\underline{yourusername}}.}
    \resumeSubItem{Published technical article on \textit{Scaling Node.js Microservices} with \textbf{8,000+ views} on Medium.}
  \resumeSubHeadingListEnd

%------------------------------------------------------------
%  LANGUAGES  (especially useful for India-based roles)
%------------------------------------------------------------
\section{Languages}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
      \textbf{English}{: Professional Proficiency} \hspace{1em}
      \textbf{Hindi}{: Native} \hspace{1em}
      \textbf{Marathi}{: Native}
    }}
 \end{itemize}

%===========================================================
\end{document}
